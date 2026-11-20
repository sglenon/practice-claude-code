"""Report watcher for Exercise 10.

There is a FileChanged hook inside a session, but no watcher that starts
a headless run by itself. This script is our own polling watcher; it
supplies that trigger by polling a file every few seconds.

Standard library only. Works on Windows, macOS, Linux.

Usage:
    python3 course/s3/agent/agent_check.py --once
    python3 course/s3/agent/agent_check.py --watch

What it does:
    1. Reads agent/brief.md and agent/settings.txt. Both must exist.
    2. Reads the tool list and owner from agent/settings.txt. Stops with a
       clear message if the tools include Bash, Edit or Write, or if the
       owner line is empty.
    3. Computes report_total and source_total in code (course/s3/agent/
       reconcile.py). The agent never computes these numbers.
    4. On PASS: prints the result and writes results/latest.json. It does
       not call Claude at all.
    5. On FAIL: sends the brief plus the computed numbers on stdin to a
       headless Claude run that may only read files (--allowedTools from
       settings.txt, --permission-mode dontAsk). The agent reports CAUSE,
       EVIDENCE and NEXT STEP. It does not fix the data or the report.
    6. Counts files changed by the agent by hashing every tracked and
       untracked file before and after the run. This is the proof that a
       read-only run changed nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reconcile  # noqa: E402  (local import, path set above)

BRIEF_PATH = ROOT / "agent" / "brief.md"
SETTINGS_PATH = ROOT / "agent" / "settings.txt"
REPORT_PATH = ROOT / "reports" / "revenue_report.txt"
RESULTS_PATH = ROOT / "results" / "latest.json"

# Limits for the headless Claude run. Measured dry run (3 runs, read-only
# brief, opus default model): 10.5-15.2 seconds, $0.13-$0.15 per run. Budget
# set to about 3x the measured cost. Raise MAX_TURNS if your brief needs more
# reasoning steps; a too-low budget can stop the run before it gives a
# result (see course/s3/README.md).
MAX_TURNS = 8
MAX_BUDGET_USD = 0.45
TIMEOUT_SECONDS = 120
POLL_SECONDS = 2

READ_ONLY_TOOLS = {"Read", "Grep", "Glob"}
DENIED_TOOLS = "Bash,Edit,Write,NotebookEdit"


class GuardError(Exception):
    """Raised when a safety check fails. The caller must stop, not continue."""


def read_settings(path: Path = SETTINGS_PATH) -> dict:
    """Read key = value lines from agent/settings.txt."""
    if not path.exists():
        raise GuardError(f"missing settings file: {path}")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


BRIEF_LABELS = ("Goal:", "Limits:", "Files:", "Done when:", "Check:")


def check_brief_labels(path: Path = BRIEF_PATH) -> None:
    """Strip <!-- --> comment lines. Stop if a label has no real text under it."""
    lines = [
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("<!--")
    ]
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped not in BRIEF_LABELS:
            continue
        body = ""
        for next_line in lines[index + 1:]:
            if next_line.strip() in BRIEF_LABELS:
                break
            if next_line.strip():
                body = next_line.strip()
                break
        if not body:
            raise GuardError(
                f"brief.md label '{stripped}' has no text. "
                "Remove the <!-- --> hint and write a real line."
            )


def check_guards(settings: dict) -> tuple[str, str]:
    """Validate settings and brief. Return (tools, owner). Raise GuardError on failure."""
    if not BRIEF_PATH.exists():
        raise GuardError(f"missing brief file: {BRIEF_PATH}")
    check_brief_labels()
    tools = settings.get("tools", "")
    owner = settings.get("owner", "")
    if not tools:
        raise GuardError("settings.txt has no tools line")
    tool_names = {t.strip() for t in tools.split(",") if t.strip()}
    blocked = tool_names - READ_ONLY_TOOLS
    if blocked:
        raise GuardError(
            "settings.txt tools include a write tool: "
            + ", ".join(sorted(blocked))
            + ". This agent may only read."
        )
    if not owner.strip():
        raise GuardError("settings.txt owner is empty. Set owner to a real person.")
    return tools, owner


def claude_path() -> str:
    """Find the claude CLI on PATH. Works for claude and claude.cmd on Windows."""
    found = shutil.which("claude") or shutil.which("claude.cmd")
    if not found:
        raise GuardError("claude was not found on PATH")
    return found


def claude_auth_ok() -> bool:
    """Run `claude auth status`. Return True on exit 0 (logged in)."""
    exe = claude_path()
    try:
        completed = subprocess.run(
            [exe, "auth", "status"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR  could not run claude auth status: {exc}")
        return False
    return completed.returncode == 0


def git_changed_files() -> dict[str, str]:
    """Return {path: content hash} for every file git tracks or could track.

    Ignored files (agent/, reports/, results/, node_modules/) are left out.
    A file that was already modified before the run is still caught, because
    the content hash changes.
    """
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=30, check=False,
            encoding="utf-8",
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    snapshot: dict[str, str] = {}
    for name in completed.stdout.split("\0"):
        if not name:
            continue
        path = ROOT / name
        try:
            snapshot[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            snapshot[name] = "missing"
    return snapshot


def count_changed(before: dict[str, str], after: dict[str, str]) -> int:
    """Count files that were added, removed or changed between two snapshots."""
    names = set(before) | set(after)
    return sum(1 for name in names if before.get(name) != after.get(name))


def parse_agent_result(result_text: str) -> dict:
    """Pull CAUSE, EVIDENCE and NEXT STEP lines out of the agent's text result."""
    cause = evidence = next_step = ""
    for line in result_text.splitlines():
        stripped = line.strip().lstrip("*#-> ").replace("**", "")
        if stripped.upper().startswith("CAUSE:"):
            cause = stripped.split(":", 1)[1].strip()
        elif stripped.upper().startswith("EVIDENCE:"):
            evidence = stripped.split(":", 1)[1].strip()
        elif stripped.upper().startswith("NEXT STEP:"):
            next_step = stripped.split(":", 1)[1].strip()
    if not (cause and evidence and next_step):
        return {"status": "REVIEW", "cause": cause, "evidence": evidence, "next_step": next_step}
    return {"status": "FAIL", "cause": cause, "evidence": evidence, "next_step": next_step}


def run_agent(tools: str, numbers: dict) -> dict:
    """Send the brief and the numbers to a read-only headless Claude run."""
    exe = claude_path()
    brief_text = BRIEF_PATH.read_text(encoding="utf-8")
    stdin_text = (
        brief_text
        + "\n\n---\nComputed numbers (from code, not from you):\n"
        + f"report_total = {numbers['report_total']}\n"
        + f"source_total = {numbers['source_total']}\n"
        + f"difference = {numbers['difference']}\n"
    )
    before = git_changed_files()
    cmd = [
        exe,
        "-p",
        "Follow the brief on stdin.",
        "--allowedTools",
        tools,
        "--disallowedTools",
        DENIED_TOOLS,
        "--permission-mode",
        "dontAsk",
        "--max-turns",
        str(MAX_TURNS),
        "--max-budget-usd",
        str(MAX_BUDGET_USD),
        "--output-format",
        "json",
    ]
    try:
        completed = subprocess.run(
            cmd,
            input=stdin_text,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired:
        after = git_changed_files()
        return {
            "status": "ERROR",
            "cause": f"claude did not finish within {TIMEOUT_SECONDS} seconds",
            "evidence": "",
            "next_step": "",
            "files_changed": count_changed(before, after),
            "cost_usd": 0.0,
        }
    after = git_changed_files()
    files_changed = count_changed(before, after)

    # Even on a non-zero exit (for example budget_exhausted), claude can
    # still print a JSON object with a cost. Try to read it before giving up.
    payload = None
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = None

    if completed.returncode != 0 and payload is None:
        return {
            "status": "ERROR",
            "cause": f"claude exited with code {completed.returncode}",
            "evidence": completed.stderr.strip()[:200],
            "next_step": "",
            "files_changed": files_changed,
            "cost_usd": 0.0,
        }
    if payload is None:
        return {
            "status": "ERROR",
            "cause": "claude did not return valid JSON",
            "evidence": completed.stdout.strip()[:200],
            "next_step": "",
            "files_changed": files_changed,
            "cost_usd": 0.0,
        }
    if completed.returncode != 0:
        errors = payload.get("errors") or [payload.get("subtype", "unknown error")]
        return {
            "status": "ERROR",
            "cause": "; ".join(str(e) for e in errors),
            "cause_source": "payload",
            "evidence": "",
            "next_step": "Raise MAX_BUDGET_USD or MAX_TURNS, or shorten the brief.",
            "files_changed": files_changed,
            "cost_usd": payload.get("total_cost_usd", 0.0),
        }
    result_text = payload.get("result", "")
    cost_usd = payload.get("total_cost_usd", 0.0)
    parsed = parse_agent_result(result_text)
    parsed["files_changed"] = files_changed
    parsed["cost_usd"] = cost_usd
    return parsed


def write_results(data: dict) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def one_pass() -> dict:
    """Run reconcile once, call the agent only on FAIL, print and save the result."""
    settings = read_settings()
    tools, owner = check_guards(settings)
    numbers = reconcile.reconcile()

    record = {
        "status": numbers["status"],
        "report_total": numbers["report_total"],
        "source_total": numbers["source_total"],
        "difference": numbers["difference"],
        "cause": "",
        "evidence": "",
        "next_step": "",
        "files_changed": 0,
        "cost_usd": 0.0,
        "owner": owner,
    }

    if numbers["status"] == "PASS":
        print(
            "PASS  report {report_total}  source {source_total}".format(**numbers)
        )
        write_results(record)
        return record

    if not claude_auth_ok():
        record["status"] = "ERROR"
        record["cause"] = "claude auth status failed. Log in before running this script."
        print(f"ERROR  {record['cause']}")
        write_results(record)
        return record

    agent_result = run_agent(tools, numbers)
    record["status"] = agent_result["status"]
    record["cause"] = agent_result.get("cause", "")
    record["evidence"] = agent_result.get("evidence", "")
    record["next_step"] = agent_result.get("next_step", "")
    record["files_changed"] = agent_result.get("files_changed", 0)
    record["cost_usd"] = agent_result.get("cost_usd", 0.0)

    print(
        "FAIL  report {report_total}  source {source_total}  "
        "difference {difference}".format(**numbers)
    )
    if record["status"] == "ERROR":
        print(f"ERROR  the agent stopped before it gave an answer: {record['cause']}")
        if agent_result.get("cause_source") == "payload":
            print("       The limits stopped the run. This is safety rule 2.")
        else:
            print("       Check that the folder is trusted and that claude auth status passes.")
    elif record["status"] == "REVIEW":
        print("REVIEW  the agent answered without the three labels. A person must read results/latest.json.")
    else:
        print(f"CAUSE: {record['cause']}")
        print(f"EVIDENCE: {record['evidence']}")
        print(f"NEXT STEP: {record['next_step']}")
    print(f"files changed by the agent: {record['files_changed']}")

    write_results(record)
    return record


def report_hash() -> str:
    """Hash the report file's bytes. Empty string if the file is missing."""
    if not REPORT_PATH.exists():
        return ""
    return hashlib.sha256(REPORT_PATH.read_bytes()).hexdigest()


def watch() -> None:
    """Poll the report file every POLL_SECONDS. Run one pass per change."""
    print(f"watching {REPORT_PATH} every {POLL_SECONDS} seconds. Press Ctrl+C to stop.")
    last_hash = report_hash()
    try:
        while True:
            time.sleep(POLL_SECONDS)
            current_hash = report_hash()
            if current_hash and current_hash != last_hash:
                last_hash = current_hash
                try:
                    one_pass()
                except GuardError as exc:
                    print(f"STOPPED  {exc}")
                except reconcile.ReconcileError as exc:
                    print(f"ERROR  {exc}")
    except KeyboardInterrupt:
        print("stopped.")


def main() -> int:
    # Flush every print immediately. Needed so --watch output shows up right
    # away when stdout is redirected to a file or a log, not just a terminal.
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description="Check the revenue report against the source data.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", action="store_true", help="run one check and exit")
    group.add_argument("--watch", action="store_true", help="poll the report and run on every change")
    args = parser.parse_args()

    try:
        if args.once:
            record = one_pass()
            return 0 if record["status"] == "PASS" else 1
        watch()
        return 0
    except GuardError as exc:
        print(f"STOPPED  {exc}")
        return 2
    except reconcile.ReconcileError as exc:
        print(f"ERROR  {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
