# practice-claude-code

Small non-production practice repository for the Claude Code enablement course.
Node.js and Python example app used in Session 1, 2 and 3 exercises.

Do not use for production work. `.env` and `secrets/` hold dummy values only,
committed on purpose so attendees can practice permission deny rules and hooks.

## Setup

```bash
npm install
```

## Build and test

```bash
npm run build
npm test
npm run lint
python3 -m unittest discover -s pyreport -v
```

## Layout

- `src/` — calculator, auth and formatter modules (Node.js / Jest)
- `pyreport/` — sensor reading report (Python)
- `ops/` — ticket data and database for the Session 2 ops report (`ops.db`, `tickets.csv`, `make_db.py`)
- `reports/` — the Session 2 ops report and its queries
- `server/` — MCP server skeleton the attendee completes (Session 2)
- `course/s2/` — reference MCP server, reference skills and the instructor check (fallback)
- `course/s3/` — reference hook and subagent files (Session 3)
- `.claude/` — Claude Code configuration and skills

## Session 2: check the ops report

1. `ops/ops.db` is ready. Run `python3 ops/make_db.py` only to build it again.
2. Open `reports/ops_weekly.md`. Read the three numbers.
3. Write a skill that checks each number against `ops/ops.db`. See
   `course/s2/reconcile/SKILL.md` for the finished version.
4. Complete `server/ops_db_server.py`, then test it: run
   `python3 server/test_ops_db.py`.
5. Connect the server: run
   `claude mcp add --transport stdio ops-db -- python3 "$PWD/server/ops_db_server.py"`.
6. Instructor check: run `python3 course/s2/check_s2.py`.
