# Ops weekly report

Three numbers from `ops/ops.db`. Each number has its definition in words.

1. **Open tickets: 5**
   Definition: tickets with no `closed_at` value.

2. **Tickets closed from 2026-10-01 through 2026-10-14 (the full last day): 7**
   Definition: tickets closed on or after 2026-10-01 and on or before the
   end of 2026-10-14.

3. **Open high-priority tickets: 2**
   Definition: tickets with no `closed_at` value and `priority = high`.

Queries: reports/ops_weekly.sql
