/* ================================
   Section E — Advanced SQL
   ================================ */

USE shopease_db;

/* Q24. CASE for price tiers */
SELECT product_name, unit_price,
CASE
    WHEN unit_price < 1000 THEN 'Budget'
    WHEN unit_price BETWEEN 1000 AND 3000 THEN 'Mid-Range'
    ELSE 'Premium'
END AS price_tier
FROM products;

/* Q25. Delivered vs Not Delivered */
SELECT
SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS delivered_orders,
SUM(CASE WHEN status <> 'Delivered' THEN 1 ELSE 0 END) AS not_delivered_orders
FROM orders;

/* Q27. Transaction example */
START TRANSACTION;

INSERT INTO orders
VALUES (1011, 102, CURDATE(), 'Pending', 1598.00);

INSERT INTO order_items
VALUES
(6001, 1011, 206, 1, 1299.00, 0),
(6002, 1011, 208, 1, 599.00, 0);

UPDATE products
SET stock_qty = stock_qty - 1
WHERE product_id IN (206, 208);

COMMIT;