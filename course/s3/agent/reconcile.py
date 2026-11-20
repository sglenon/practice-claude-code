"""Reconcile the shipped report against the raw order data.

Standard library only. Works on Windows, macOS, Linux.

report_total  = the "Total" line in reports/revenue_report.txt
source_total  = the sum of the amount column in data/orders.csv

Run directly to print both numbers and the difference:
    python3 course/s3/agent/reconcile.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
REPORT_PATH = ROOT / "reports" / "revenue_report.txt"
ORDERS_PATH = ROOT / "data" / "orders.csv"


class ReconcileError(Exception):
    """Raised when a required input file is missing or unreadable."""


def report_total(path: Path = REPORT_PATH) -> int:
    """Read the Total line out of the revenue report text file."""
    if not path.exists():
        raise ReconcileError(f"missing report file: {path}")
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        parts = line.strip().split("\t")
        if len(parts) == 2 and parts[0].strip().lower() == "total":
            try:
                return int(parts[1].strip())
            except ValueError as exc:
                raise ReconcileError(f"bad total value in {path}: {parts[1]!r}") from exc
    raise ReconcileError(f"no Total line found in {path}")


def source_total(path: Path = ORDERS_PATH) -> int:
    """Sum the amount column in data/orders.csv."""
    if not path.exists():
        raise ReconcileError(f"missing source file: {path}")
    total = 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "amount" not in (reader.fieldnames or []):
            raise ReconcileError(f"no amount column in {path}")
        for row in reader:
            total += int(row["amount"])
    return total


def reconcile() -> dict:
    """Return report_total, source_total, difference and pass/fail status."""
    report = report_total()
    source = source_total()
    difference = report - source
    status = "PASS" if difference == 0 else "FAIL"
    return {
        "status": status,
        "report_total": report,
        "source_total": source,
        "difference": difference,
    }


def main() -> int:
    try:
        result = reconcile()
    except ReconcileError as exc:
        print(f"ERROR  {exc}")
        return 2
    print(
        "{status}  report {report_total}  source {source_total}  "
        "difference {difference}".format(**result)
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
