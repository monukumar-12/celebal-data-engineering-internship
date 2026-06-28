/* ================================
   Section C — Aggregation
   ================================ */

USE shopease_db;

/* Q13. Total number of orders */
SELECT COUNT(*) AS total_orders
FROM orders;

/* Q14. Revenue from delivered orders */
SELECT SUM(total_amount) AS delivered_revenue
FROM orders
WHERE status = 'Delivered';

/* Q15. Average product price per category */
SELECT category, AVG(unit_price) AS avg_price
FROM products
GROUP BY category;

/* Q16. Orders and revenue per status */
SELECT status,
       COUNT(*) AS order_count,
       SUM(total_amount) AS total_revenue
FROM orders
GROUP BY status
ORDER BY total_revenue DESC;

/* Q17. Max & Min price per category */
SELECT category,
       MAX(unit_price) AS max_price,
       MIN(unit_price) AS min_price
FROM products
GROUP BY category;

/* Q18. Categories with avg price > 2000 */
SELECT category, AVG(unit_price) AS avg_price
FROM products
GROUP BY category
HAVING AVG(unit_price) > 2000;