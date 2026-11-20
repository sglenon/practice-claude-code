---
name: reconcile
description: Check the numbers in a report against the source database. Use when a person asks to reconcile, verify, or double-check a report's numbers.
---

# Reconcile a report against its source

Input: the path of a report (for example, `reports/ops_weekly.md`).

Steps:

1. List each number in the report, with its definition in words, as written
   in the report.
2. For each number, write one SELECT query for `ops/ops.db` from the
   definition. Do not copy the query from the report's `.sql` file. Write
   your own, from the words.
3. Rule: a date range that ends on a day includes the full last day. For
   example, "through 2026-10-14" means up to, and including, all of
   2026-10-14, not just the start of that day.
4. Run each SELECT with `python3` and the `sqlite3` module, read-only.
   Windows: use `python` if `python3` is not found.
5. Show a table: `Metric | Report | Source | Query | PASS or FAIL`.
   - `Report` is the number from the report.
   - `Source` is the number your query returned.
   - `PASS` when they match, `FAIL` when they do not.
6. For each `FAIL`, open `reports/ops_weekly.sql`, find the query that made
   the report's number, and say what is different from your query. Name
   the ticket or tickets that make the difference.
7. Never change data or files. Only read `ops/ops.db` and the report.

## Example query shape

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('file:ops/ops.db?mode=ro', uri=True)
conn.execute('PRAGMA query_only = ON')
print(conn.execute('SELECT COUNT(*) FROM tickets WHERE closed_at IS NULL').fetchone())
"
```
