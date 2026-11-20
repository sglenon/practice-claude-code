#!/usr/bin/env python3
"""Instructor check for Session 2. Python 3 standard library only.

Run from the repo root:
    python3 course/s2/check_s2.py

Windows: if `python3` is not found, use `python` instead.

Checks:
1. ops/ops.db gives the five expected numbers.
2. server/test_ops_db.py run against the reference server (course/s2/ops_db_server.py)
   prints 3 PASS.

Prints one PASS or FAIL line per check. Exit code 0 only if all pass.
"""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / "ops" / "ops.db"
REFERENCE_SERVER = REPO_ROOT / "course" / "s2" / "ops_db_server.py"
TEST_SCRIPT = REPO_ROOT / "server" / "test_ops_db.py"

EXPECTED = {
    "open tickets": 5,
    "closed in range, BETWEEN (planted fault)": 7,
    "closed in range, correct": 8,
    "open high-priority tickets": 2,
}
EXPECTED_PER_TEAM = {"Web": 3, "Data": 3, "Ops": 2}


def check(label: str, got, expected) -> bool:
    passed = got == expected
    status = "PASS" if passed else "FAIL"
    print(f"{status} {label}: got {got!r}, expected {expected!r}")
    return passed


def main() -> int:
    if not DB_PATH.exists():
        print(f"FAIL database missing: {DB_PATH}")
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    try:
        open_tickets = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE closed_at IS NULL"
        ).fetchone()[0]
        closed_between = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE closed_at BETWEEN '2026-10-01' AND '2026-10-14'"
        ).fetchone()[0]
        closed_correct = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE closed_at IS NOT NULL "
            "AND closed_at < '2026-10-15 00:00:00'"
        ).fetchone()[0]
        open_high = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE closed_at IS NULL AND priority = 'high'"
        ).fetchone()[0]
        per_team_rows = conn.execute(
            "SELECT team, COUNT(*) FROM tickets WHERE closed_at IS NOT NULL "
            "AND closed_at < '2026-10-15 00:00:00' GROUP BY team"
        ).fetchall()
        per_team = dict(per_team_rows)
    finally:
        conn.close()

    all_ok = True
    all_ok &= check("open tickets", open_tickets, EXPECTED["open tickets"])
    all_ok &= check(
        "closed in range, BETWEEN (planted fault)",
        closed_between,
        EXPECTED["closed in range, BETWEEN (planted fault)"],
    )
    all_ok &= check("closed in range, correct", closed_correct, EXPECTED["closed in range, correct"])
    all_ok &= check("open high-priority tickets", open_high, EXPECTED["open high-priority tickets"])
    for team, expected_count in EXPECTED_PER_TEAM.items():
        all_ok &= check(f"team {team} closed in range", per_team.get(team, 0), expected_count)
    all_ok &= check("team Sec has no row", "Sec" not in per_team, True)

    env = dict(os.environ)
    result = subprocess.run(
        [sys.executable, str(TEST_SCRIPT), str(REFERENCE_SERVER)],
        capture_output=True,
        text=True,
        env=env,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    server_ok = result.returncode == 0
    print("PASS reference server test" if server_ok else "FAIL reference server test")
    all_ok &= server_ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
