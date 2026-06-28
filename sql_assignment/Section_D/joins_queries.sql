/* ================================
   Section D — Joins
   ================================ */

USE shopease_db;

/* Q19. Orders with customer names */
SELECT o.order_id, o.order_date,
       c.first_name, c.last_name,
       o.total_amount
FROM orders o
INNER JOIN customers c
ON o.customer_id = c.customer_id;

/* Q20. All customers with orders (LEFT JOIN) */
SELECT c.customer_id, c.first_name,
       o.order_id, o.total_amount
FROM customers c
LEFT JOIN orders o
ON c.customer_id = o.customer_id;

/* Q21. Orders → Items → Products */
SELECT o.order_id,
       p.product_name,
       oi.quantity,
       oi.unit_price,
       oi.discount_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id;

/* Q22. LEFT vs RIGHT JOIN explanation in README */

/* Q23. Foreign key violation example */
-- INSERT INTO orders VALUES (2000, 999, CURDATE(), 'Pending', 1000);