#!/usr/bin/env python3
"""Test the ops-db MCP server as a real child process. Standard library only.

Run:
    python3 server/test_ops_db.py
    python3 server/test_ops_db.py path/to/ops_db_server.py   (optional: test a
                                                                different server file)

Also reads the environment variable OPS_DB_SERVER for the server path, if no
argument is given. The argument, if given, wins over the environment variable.

Prints exactly these three lines (PASS or FAIL):
    PASS tools list
    PASS open tickets = 5
    PASS DELETE refused

Exit code 0 only if all three pass.

Windows: if `python3` is not found, use `python` instead.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SERVER = HERE / "ops_db_server.py"


def server_path() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    env_path = os.environ.get("OPS_DB_SERVER")
    if env_path:
        return Path(env_path).resolve()
    return DEFAULT_SERVER


def send(proc: subprocess.Popen, message: dict) -> None:
    proc.stdin.write(json.dumps(message) + "\n")
    proc.stdin.flush()


def read_reply(proc: subprocess.Popen) -> dict:
    line = proc.stdout.readline()
    if not line:
        raise RuntimeError("Server closed its output (no reply).")
    return json.loads(line)


def call_tool(proc: subprocess.Popen, request_id: int, name: str, arguments: dict) -> dict:
    send(
        proc,
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
    )
    return read_reply(proc)


def main() -> int:
    target = server_path()
    results = []  # list of (label, passed, reason)

    proc = subprocess.Popen(
        [sys.executable, str(target)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    try:
        send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "test_ops_db", "version": "0.1.0"},
                },
            },
        )
        read_reply(proc)
        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 1. tools/list
        send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        list_reply = read_reply(proc)
        tool_names = {t.get("name") for t in list_reply.get("result", {}).get("tools", [])}
        if {"list_tables", "run_select"}.issubset(tool_names):
            results.append(("tools list", True, ""))
        else:
            results.append(("tools list", False, f"tools seen: {sorted(tool_names)}"))

        # 2. open tickets = 5
        reply = call_tool(
            proc,
            3,
            "run_select",
            {"sql": "SELECT COUNT(*) FROM tickets WHERE closed_at IS NULL"},
        )
        result = reply.get("result", {})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        if result.get("isError"):
            results.append(("open tickets = 5", False, f"server returned an error: {text!r}"))
        elif "5" in text.splitlines()[-1] if text.splitlines() else False:
            results.append(("open tickets = 5", True, ""))
        else:
            results.append(("open tickets = 5", False, f"got: {text!r}"))

        # 3. DELETE refused
        reply = call_tool(
            proc,
            4,
            "run_select",
            {"sql": "DELETE FROM tickets WHERE id = 'T14'"},
        )
        result = reply.get("result", {})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        if result.get("isError") and "Only SELECT is allowed" in text:
            results.append(("DELETE refused", True, ""))
        else:
            results.append(("DELETE refused", False, f"got: {text!r}, isError={result.get('isError')}"))

        # Confirm the table still has 14 rows after the DELETE attempt.
        reply = call_tool(proc, 5, "run_select", {"sql": "SELECT COUNT(*) FROM tickets"})
        result = reply.get("result", {})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        last_line = text.splitlines()[-1] if text.splitlines() else ""
        if result.get("isError") or "14" not in last_line:
            # Keep this as part of the DELETE-refused check, since it proves
            # the DELETE really did nothing.
            for i, (label, passed, reason) in enumerate(results):
                if label == "DELETE refused":
                    results[i] = (label, False, f"row count check failed: {text!r}")
    finally:
        try:
            proc.stdin.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            proc.wait(timeout=5)
        except Exception:  # noqa: BLE001
            proc.kill()

    all_passed = True
    for label, passed, reason in results:
        status = "PASS" if passed else "FAIL"
        if passed:
            print(f"{status} {label}")
        else:
            print(f"{status} {label} ({reason})")
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
