"""Revenue by region for Q3 2026. Loads data/*.csv into SQLite in memory."""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def _val(v):
    return int(v) if v.isdigit() else v

def load(conn, table, path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    conn.execute(f"CREATE TABLE {table} ({', '.join(cols)})")
    conn.executemany(
        f"INSERT INTO {table} VALUES ({', '.join('?' for _ in cols)})",
        [tuple(_val(r[c]) for c in cols) for r in rows],
    )

def revenue_by_region():
    conn = sqlite3.connect(":memory:")
    load(conn, "orders", ROOT / "data" / "orders.csv")
    load(conn, "customers", ROOT / "data" / "customers.csv")
    sql = (ROOT / "analysis" / "revenue_by_region.sql").read_text()
    return conn.execute(sql).fetchall()

if __name__ == "__main__":
    rows = revenue_by_region()
    for region, revenue in rows:
        print(f"{region}\t{revenue}")
    print(f"Total\t{sum(r for _, r in rows)}")
