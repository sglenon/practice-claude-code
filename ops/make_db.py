#!/usr/bin/env python3
"""Build ops/ops.db from ops/tickets.csv. Python 3 standard library only.

Run from any folder:
    python3 ops/make_db.py

Windows: type `python` instead of `python3` if `python3` is not found.

This script is deterministic. Run it twice. The database file is the same
both times.
"""
import csv
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "tickets.csv"
DB_PATH = HERE / "ops.db"


def build(csv_path: Path = CSV_PATH, db_path: Path = DB_PATH) -> None:
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "CREATE TABLE tickets ("
            "id TEXT PRIMARY KEY, "
            "team TEXT NOT NULL, "
            "priority TEXT NOT NULL, "
            "opened_at TEXT NOT NULL, "
            "closed_at TEXT"
            ")"
        )
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        for row in rows:
            closed = row["closed_at"].strip() or None
            conn.execute(
                "INSERT INTO tickets (id, team, priority, opened_at, closed_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (row["id"], row["team"], row["priority"], row["opened_at"], closed),
            )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    build()
    print(f"Built {DB_PATH}")
