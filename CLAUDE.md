# CLAUDE.md — Team Practice Repo

## About this project

This is a small practice repository for the Claude Code enablement series.
It is non-production. It is for training exercises.

## Build and test

```bash
npm install
npm run build
npm test
npm run lint
python3 -m unittest discover -s pyreport -v
```

## Conventions

1. Never edit files under `generated/`.
2. Use feature branches. Branch name format: `feat/<ticket-id>-short-description`.
3. Write a one-line summary at the top of every pull request.
4. Do not paste customer names, ID numbers, or policy numbers into prompts.
5. Keep functions short. One function does one thing.

## Restricted paths

Do not read or edit these paths without an explicit instruction from the team lead:

- `.env` and `.env.*`
- `secrets/`
- Any path that contains `/prod/`

These restrictions are also enforced by the permission rules in `.claude/settings.json`.

## Build/test commands that Claude must use

| Task | Command |
|------|---------|
| Build | `npm run build` |
| All tests | `npm test` |
| Lint | `npm run lint` |
| Single test file | `npm test -- --testPathPattern=<filename>` |
| Python tests | `python3 -m unittest discover -s pyreport -v` |

## Notes for Claude

- If a command fails, report the full error. Do not silently retry.
- If you are unsure about a file path or rule, ask before editing.
- After any code change, run `npm test` and report the result.
- For files in `server/`, run `python3 server/test_ops_db.py`, not `npm test`.
