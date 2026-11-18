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
python3 -m unittest discover -s board -v
```

## Layout

- `src/` — calculator, auth and formatter modules (Node.js / Jest)
- `pyreport/` — sensor reading report (Python)
- `board/` — ticket board app (Python); `python3 board/make_board.py` to build,
  `python3 -m unittest discover -s board -v` to test
- `course/s1/` — coffee board fallback (Session 1)
- `server/` — MCP server status fixture (Session 2)
- `course/s2/` — reference MCP server (fallback)
- `course/s3/` — reference hook and subagent files (Session 3)
- `.claude/` — Claude Code configuration and skills
