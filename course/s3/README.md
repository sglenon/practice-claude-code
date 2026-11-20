# Session 3 reference files

Files used by Exercises 8, 9 and 10. There is a FileChanged hook inside a
session, but no watcher that starts a headless run by itself. The watcher
in Exercise 10 is our own polling script.

## Exercise 8 — fix the bug, fix the data

1. `git switch exercise/s3-ex8`
2. `npm install`
3. `node -e "console.log(require('./src/auth.js').login('ghost'))"`
4. `python3 analysis/revenue_by_region.py`
5. Write the brief. Use the five labels: Goal, Limits, Files, Done when, Check.
6. Run `npm test` after the dev fix. Run `python3 analysis/revenue_by_region.py` after the data fix.

PowerShell step 3 (same command, one line):
```powershell
node -e "console.log(require('./src/auth.js').login('ghost'))"
```

## Exercise 9 — hook and subagent

1. Make `.claude/agents`, then copy `course/s3/security-reviewer.md` to
   `.claude/agents/security-reviewer.md`, before you start Claude. A running session does
   not pick up a new subagent file.
   - Bash: `mkdir -p .claude/agents` then `cp course/s3/security-reviewer.md .claude/agents/security-reviewer.md`
   - PowerShell: `New-Item -ItemType Directory -Force .claude/agents` then `Copy-Item course/s3/security-reviewer.md .claude/agents/security-reviewer.md`
2. Merge the settings file into `.claude/settings.json`. One copy, not a hand edit.
   - Bash: `cp course/s3/settings.with-hook.json .claude/settings.json`
   - PowerShell: `Copy-Item course/s3/settings.with-hook.windows.json .claude/settings.json`
3. Check the file is valid JSON: `python3 -m json.tool .claude/settings.json` (PowerShell: `python -m json.tool .claude/settings.json`)
4. Start Claude. Open `/hooks` in Claude Code. Confirm the Bash PreToolUse hook is listed.
5. Run `echo app-prod` and show the output. Only the hook pattern matches this text.
6. Done when: Claude shows the line `Blocked: command matches protected pattern`.

## Exercise 10 — build a report watcher

See the step table in the lab page. Files used:

- `course/s3/agent/reconcile.py` — computes report_total and source_total in code.
- `course/s3/agent/agent_check.py` — the watcher. Run with `--once` or `--watch`.
- `course/s3/agent/brief.template.md`, `brief.reference.md` — copy one into `agent/brief.md`.
- `course/s3/agent/settings.template.txt` — copy into `agent/settings.txt`. Set `tools` and `owner`.
- `course/s3/sample-reports/*.txt` — copy one into `reports/revenue_report.txt`.

One-line commands:

```bash
mkdir agent
cp course/s3/agent/brief.template.md agent/brief.md
cp course/s3/agent/settings.template.txt agent/settings.txt
mkdir -p reports
cp course/s3/sample-reports/report-wrong.txt reports/revenue_report.txt
python3 course/s3/agent/agent_check.py --once
```

```powershell
New-Item -ItemType Directory -Force agent
Copy-Item course/s3/agent/brief.template.md agent/brief.md
Copy-Item course/s3/agent/settings.template.txt agent/settings.txt
New-Item -ItemType Directory -Force reports
Copy-Item course/s3/sample-reports/report-wrong.txt reports/revenue_report.txt
python course/s3/agent/agent_check.py --once
```

Safety rules:
1. The agent reads. The script writes.
2. The agent has limits: tools, turns, budget, timeout.
3. The agent reports to a named person. A person approves each change.
