# Brief for the report-check agent (reference copy)

Goal:
Say why the report total and the order-data total do not match.

Limits:
Read only. Do not edit, write or run any file. Use the report_total,
source_total and difference given to you on stdin. Do not compute your own
numbers.

Files:
reports/revenue_report.txt, data/orders.csv, data/customers.csv,
analysis/revenue_by_region.sql, analysis/revenue_by_region.py

Done when:
Answer with exactly three lines:
CAUSE: <the one most likely reason for the difference>
EVIDENCE: <the file and the line or rows that support the cause>
NEXT STEP: <one short instruction for the person who owns this report>

Check:
A person re-runs course/s3/agent/reconcile.py after the fix and confirms
difference is 0.
