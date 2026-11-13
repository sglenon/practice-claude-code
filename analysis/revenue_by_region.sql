-- Revenue by region, Q3 2026
SELECT c.region, SUM(o.amount) AS revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date BETWEEN '2026-07-01' AND '2026-09-30'
GROUP BY c.region
ORDER BY c.region;
