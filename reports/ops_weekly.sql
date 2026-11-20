-- Queries behind reports/ops_weekly.md
-- Run with: python3 -c "import sqlite3; ..." or any SELECT-only tool.
-- Database: ops/ops.db, table tickets(id, team, priority, opened_at, closed_at).

-- 1. Open tickets: closed_at is empty.
SELECT COUNT(*) AS open_tickets
FROM tickets
WHERE closed_at IS NULL;

-- 2. Tickets closed from 2026-10-01 through 2026-10-14.
SELECT COUNT(*) AS closed_in_range
FROM tickets
WHERE closed_at BETWEEN '2026-10-01' AND '2026-10-14';

-- 3. Open high-priority tickets.
SELECT COUNT(*) AS open_high_priority
FROM tickets
WHERE closed_at IS NULL AND priority = 'high';
