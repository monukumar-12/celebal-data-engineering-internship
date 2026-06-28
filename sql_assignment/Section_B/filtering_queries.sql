/* ================================
   Section B — Filtering & Indexes
   ================================ */

USE shopease_db;

/* Q7. Delivered orders */
SELECT *
FROM orders
WHERE status = 'Delivered';

/* Q8. Electronics products above 2000 */
SELECT *
FROM products
WHERE category = 'Electronics'
  AND unit_price > 2000;

/* Q9. Customers joined in 2024 from Maharashtra */
SELECT *
FROM customers
WHERE state = 'Maharashtra'
  AND join_date BETWEEN '2024-01-01' AND '2024-12-31';

/* Q10. Orders between dates and not cancelled */
SELECT *
FROM orders
WHERE order_date BETWEEN '2024-08-10' AND '2024-08-25'
  AND status <> 'Cancelled';

/* Q11. Index usage example */
SELECT *
FROM orders
WHERE order_date >= '2024-08-15';

/* Q12. SARGable query */
SELECT *
FROM customers
WHERE join_date BETWEEN '2024-01-01' AND '2024-12-31';