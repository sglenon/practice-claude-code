---
name: reconcile
description: Check the numbers in a report against the source database, using the ops-db MCP server. Use when a person asks to reconcile, verify, or double-check a report's numbers, and the ops-db server is connected.
---

# Reconcile a report against its source, through the ops-db server

Input: the path of a report (for example, `reports/ops_weekly.md`).

This is the Exercise 7 version. Use only the `run_select` tool of the
`ops-db` MCP server. Do not run `python3` directly.

Steps:

1. List each number in the report, with its definition in words, as written
   in the report.
2. For each number, write one SELECT query from the definition. Do not copy
   the query from the report's `.sql` file. Write your own, from the words.
3. Rule: a date range that ends on a day includes the full last day. For
   example, "through 2026-10-14" means up to, and including, all of
   2026-10-14, not just the start of that day.
4. Run each query by calling the `run_select` tool of the `ops-db` server.
   Do not use `python3` or the `sqlite3` command for this skill.
5. Show a table: `Metric | Report | Source | Query | PASS or FAIL`.
   - `Report` is the number from the report.
   - `Source` is the number `run_select` returned.
   - `PASS` when they match, `FAIL` when they do not.
6. For each `FAIL`, open `reports/ops_weekly.sql`, find the query that made
   the report's number, and say what is different from your query. Name
   the ticket or tickets that make the difference.
7. Never change data or files. `run_select` only accepts SELECT and WITH
   queries; it refuses anything else.
