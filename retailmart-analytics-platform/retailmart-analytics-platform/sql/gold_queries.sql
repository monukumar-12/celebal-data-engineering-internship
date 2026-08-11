-- =====================================================================
-- RetailMart GOLD LAYER - SQL Query Library
-- =====================================================================
-- Engine: DuckDB (ANSI SQL, runs standalone - no server needed)
-- Tables available (loaded from Silver-layer CSVs by build_gold.py):
--   customers(customer_id, first_name, last_name, email, phone, city, signup_date)
--   products(product_id, product_name, category, price, active)
--   orders(order_id, customer_id, order_date, status, delivery_date,
--          is_delivery_date_corrected, delivery_days)
--   order_items(order_item_id, order_id, product_id, quantity, unit_price, line_total)
--   payments(payment_id, order_id, amount, method, payment_status, payment_date)
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. SELECT / KEYS  -->  "Order-customer joins" (basic SELECT + primary/foreign keys)
-- ---------------------------------------------------------------------
-- customer_id is the primary key of customers and the foreign key on orders
SELECT
    o.order_id,
    o.order_date,
    o.status,
    c.customer_id,
    c.first_name,
    c.last_name,
    c.city
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
ORDER BY o.order_date
LIMIT 20;


-- ---------------------------------------------------------------------
-- 2. WHERE + INDEXES  -->  "Filter by order status"
-- ---------------------------------------------------------------------
-- DuckDB auto-indexes primary/foreign keys used in joins; for large
-- Postgres/MySQL deployments you would additionally run:
--   CREATE INDEX idx_orders_status ON orders(status);
--   CREATE INDEX idx_orders_customer_id ON orders(customer_id);
SELECT order_id, customer_id, order_date, status
FROM orders
WHERE status = 'Delivered'
ORDER BY order_date DESC
LIMIT 20;


-- ---------------------------------------------------------------------
-- 3. GROUP BY  -->  "Monthly revenue"
-- ---------------------------------------------------------------------
SELECT
    strftime(o.order_date, '%Y-%m') AS revenue_month,
    ROUND(SUM(oi.line_total), 2)     AS total_revenue,
    COUNT(DISTINCT o.order_id)       AS num_orders
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY revenue_month
ORDER BY revenue_month;


-- ---------------------------------------------------------------------
-- 4. JOINS  -->  "Customer 360 (Unified view)"
-- ---------------------------------------------------------------------
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.city,
    c.signup_date,
    COUNT(DISTINCT o.order_id)                         AS total_orders,
    COALESCE(SUM(oi.line_total), 0)                    AS lifetime_spend,
    COALESCE(SUM(CASE WHEN p.payment_status = 'Success'
                       THEN p.amount ELSE 0 END), 0)    AS confirmed_paid,
    MAX(o.order_date)                                   AS last_order_date
FROM customers c
LEFT JOIN orders o        ON c.customer_id = o.customer_id
LEFT JOIN order_items oi  ON o.order_id = oi.order_id
LEFT JOIN payments p      ON o.order_id = p.order_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.city,
         c.signup_date
ORDER BY lifetime_spend DESC;


-- ---------------------------------------------------------------------
-- 5. CASE  -->  "Customer segments"
-- ---------------------------------------------------------------------
-- Churn/activity windows are relative to the most recent order_date in the
-- dataset (an "as-of" snapshot date), not the real wall-clock date -- this
-- is standard practice when analyzing a fixed historical dataset.
WITH as_of AS (
    SELECT MAX(order_date) AS snapshot_date FROM orders
),
customer_spend AS (
    SELECT
        c.customer_id,
        COALESCE(SUM(oi.line_total), 0) AS lifetime_spend,
        COUNT(DISTINCT o.order_id)       AS total_orders,
        MAX(o.order_date)                AS last_order_date
    FROM customers c
    LEFT JOIN orders o       ON c.customer_id = o.customer_id
                             AND o.status NOT IN ('Cancelled', 'Returned')
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id
)
SELECT
    customer_id,
    lifetime_spend,
    total_orders,
    last_order_date,
    CASE
        WHEN lifetime_spend >= 50000 THEN 'VIP'
        WHEN lifetime_spend >= 15000 THEN 'Gold'
        WHEN lifetime_spend >= 3000  THEN 'Silver'
        WHEN lifetime_spend > 0      THEN 'Bronze'
        ELSE 'No Purchase'
    END AS spend_segment,
    CASE
        WHEN last_order_date IS NULL THEN 'Never Purchased'
        WHEN last_order_date < (SELECT snapshot_date FROM as_of) - INTERVAL 180 DAY THEN 'At Risk / Churn Candidate'
        WHEN last_order_date < (SELECT snapshot_date FROM as_of) - INTERVAL 90 DAY  THEN 'Cooling Off'
        ELSE 'Active'
    END AS activity_segment
FROM customer_spend
ORDER BY lifetime_spend DESC;


-- ---------------------------------------------------------------------
-- 6. SUBQUERIES  -->  "Above-average spenders"
-- ---------------------------------------------------------------------
SELECT
    customer_id,
    lifetime_spend
FROM (
    SELECT
        c.customer_id,
        COALESCE(SUM(oi.line_total), 0) AS lifetime_spend
    FROM customers c
    LEFT JOIN orders o       ON c.customer_id = o.customer_id
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id
) AS spend_per_customer
WHERE lifetime_spend > (
    -- correlated business rule: overall average lifetime spend across all customers
    SELECT AVG(customer_total)
    FROM (
        SELECT COALESCE(SUM(oi.line_total), 0) AS customer_total
        FROM customers c
        LEFT JOIN orders o       ON c.customer_id = o.customer_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY c.customer_id
    )
)
ORDER BY lifetime_spend DESC;


-- ---------------------------------------------------------------------
-- 7. CTEs  -->  "Funnel analysis"
-- ---------------------------------------------------------------------
-- Order funnel: Placed -> Shipped -> Delivered vs Cancelled/Returned drop-off
WITH funnel_base AS (
    SELECT order_id, status FROM orders
),
funnel_counts AS (
    SELECT
        COUNT(*)                                              AS total_orders,
        COUNT(*) FILTER (WHERE status IN
            ('Placed','Shipped','Delivered','Returned'))      AS reached_placed,
        COUNT(*) FILTER (WHERE status IN
            ('Shipped','Delivered','Returned'))                AS reached_shipped,
        COUNT(*) FILTER (WHERE status IN
            ('Delivered','Returned'))                          AS reached_delivered,
        COUNT(*) FILTER (WHERE status = 'Cancelled')           AS cancelled,
        COUNT(*) FILTER (WHERE status = 'Returned')            AS returned
    FROM funnel_base
)
SELECT
    total_orders,
    reached_placed,
    reached_shipped,
    reached_delivered,
    cancelled,
    returned,
    ROUND(100.0 * reached_shipped   / NULLIF(reached_placed, 0), 1)   AS pct_placed_to_shipped,
    ROUND(100.0 * reached_delivered / NULLIF(reached_shipped, 0), 1)  AS pct_shipped_to_delivered,
    ROUND(100.0 * cancelled / NULLIF(total_orders, 0), 1)             AS pct_cancelled,
    ROUND(100.0 * returned  / NULLIF(total_orders, 0), 1)             AS pct_returned
FROM funnel_counts;


-- ---------------------------------------------------------------------
-- 8. WINDOW FUNCTIONS  -->  "Product rank by category"
-- ---------------------------------------------------------------------
WITH product_sales AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        SUM(oi.quantity)      AS units_sold,
        SUM(oi.line_total)    AS revenue
    FROM products p
    JOIN order_items oi ON p.product_id = oi.product_id
    JOIN orders o       ON oi.order_id = o.order_id
    WHERE o.status NOT IN ('Cancelled', 'Returned')
    GROUP BY p.product_id, p.product_name, p.category
)
SELECT
    category,
    product_id,
    product_name,
    units_sold,
    ROUND(revenue, 2) AS revenue,
    RANK()        OVER (PARTITION BY category ORDER BY revenue DESC) AS revenue_rank_in_category,
    DENSE_RANK()  OVER (PARTITION BY category ORDER BY units_sold DESC) AS units_rank_in_category,
    ROUND(
      100.0 * revenue / SUM(revenue) OVER (PARTITION BY category), 2
    ) AS pct_of_category_revenue
FROM product_sales
QUALIFY revenue_rank_in_category <= 5
ORDER BY category, revenue_rank_in_category;
