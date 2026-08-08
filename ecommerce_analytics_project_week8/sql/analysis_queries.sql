-- ============================================================================
-- Part 3: SQL Analysis
-- Database: SQLite (database/ecommerce.db)
-- Revenue formula used throughout: quantity * unit_price * (1 - discount_percent/100)
-- ============================================================================


-- ----------------------------------------------------------------------------
-- BASIC QUERIES
-- ----------------------------------------------------------------------------

-- 1. Total revenue per category
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;


-- 2. Top 10 customers by total order value
SELECT
    o.customer_id,
    c.customer_name,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_order_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.customer_id IS NOT NULL
GROUP BY o.customer_id, c.customer_name
ORDER BY total_order_value DESC
LIMIT 10;


-- 3. Month-wise order count for the last 12 months
-- (relative to the most recent order date in the dataset)
WITH max_date AS (
    SELECT MAX(order_date) AS latest FROM orders
)
SELECT
    strftime('%Y-%m', o.order_date) AS year_month,
    COUNT(*) AS order_count
FROM orders o, max_date m
WHERE o.order_date >= date(m.latest, '-12 months')
GROUP BY year_month
ORDER BY year_month;


-- ----------------------------------------------------------------------------
-- INTERMEDIATE QUERIES
-- ----------------------------------------------------------------------------

-- 4. Customers who placed orders but never had any item delivered
SELECT DISTINCT o.customer_id, c.customer_name
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.customer_id IS NOT NULL
  AND o.customer_id NOT IN (
        SELECT customer_id FROM orders WHERE status = 'DELIVERED' AND customer_id IS NOT NULL
  );


-- 5. Products that were ordered but had more returns than purchases
-- (negative quantity rows = returns; positive quantity rows = purchases)
SELECT
    p.product_id,
    p.product_name,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS total_purchased,
    SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS total_returned
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
HAVING total_returned > total_purchased;


-- 6. Return rate (returned items / total items) per category
SELECT
    p.category,
    SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS returned_items,
    SUM(ABS(oi.quantity)) AS total_items,
    ROUND(
        1.0 * SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END)
        / NULLIF(SUM(ABS(oi.quantity)), 0), 4
    ) AS return_rate
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY return_rate DESC;


-- ----------------------------------------------------------------------------
-- ADVANCED QUERIES (Window Functions, CTEs, Subqueries)
-- ----------------------------------------------------------------------------

-- 7. Running Totals with Window Functions
-- Running total of revenue per region, ordered by date.
WITH daily_region_revenue AS (
    SELECT
        o.region_code,
        date(o.order_date) AS order_date,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS daily_revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY o.region_code, date(o.order_date)
)
SELECT
    region_code,
    order_date,
    ROUND(daily_revenue, 2) AS daily_revenue,
    ROUND(SUM(daily_revenue) OVER (
        PARTITION BY region_code ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_total
FROM daily_region_revenue
ORDER BY region_code, order_date;


-- 8. Ranking with DENSE_RANK
-- For each category, rank products by total revenue. Ties share the same rank.
WITH product_revenue AS (
    SELECT
        p.category,
        p.product_name,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS total_revenue
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    GROUP BY p.category, p.product_name
)
SELECT
    category,
    product_name,
    ROUND(total_revenue, 2) AS total_revenue,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rank_in_category
FROM product_revenue
ORDER BY category, rank_in_category;


-- 9. LAG/LEAD Analysis
-- For each customer, days between consecutive orders. Flag "At Risk" if avg gap > 30 days.
WITH customer_orders AS (
    SELECT
        customer_id,
        order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS previous_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
),
gaps AS (
    SELECT
        customer_id,
        order_date,
        previous_order_date,
        CASE WHEN previous_order_date IS NOT NULL
             THEN julianday(order_date) - julianday(previous_order_date)
             ELSE NULL END AS days_gap
    FROM customer_orders
),
avg_gaps AS (
    SELECT customer_id, AVG(days_gap) AS avg_gap
    FROM gaps
    WHERE days_gap IS NOT NULL
    GROUP BY customer_id
)
SELECT
    g.customer_id,
    g.order_date,
    g.previous_order_date,
    ROUND(g.days_gap, 2) AS days_gap,
    CASE WHEN a.avg_gap > 30 THEN 'At Risk' ELSE 'Active' END AS risk_flag
FROM gaps g
LEFT JOIN avg_gaps a ON a.customer_id = g.customer_id
ORDER BY g.customer_id, g.order_date;


-- 10. CTE with Multiple Levels
-- Monthly revenue per customer -> categorize (High/Medium/Low) -> count per category per month
WITH monthly_customer_revenue AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS year_month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id, year_month
),
categorized AS (
    SELECT
        customer_id,
        year_month,
        revenue,
        CASE
            WHEN revenue > 10000 THEN 'High'
            WHEN revenue >= 5000 THEN 'Medium'
            ELSE 'Low'
        END AS revenue_category
    FROM monthly_customer_revenue
)
SELECT
    year_month,
    revenue_category,
    COUNT(DISTINCT customer_id) AS customer_count
FROM categorized
GROUP BY year_month, revenue_category
ORDER BY year_month, revenue_category;


-- 11. NTILE for Segmentation
-- Divide customers into 4 quartiles based on total lifetime value.
WITH customer_ltv AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS total_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    ROUND(total_value, 2) AS total_value,
    NTILE(4) OVER (ORDER BY total_value DESC) AS quartile,
    CASE NTILE(4) OVER (ORDER BY total_value DESC)
        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        WHEN 4 THEN 'Bronze'
    END AS quartile_label
FROM customer_ltv
ORDER BY total_value DESC;


-- 12. Year-over-Year Comparison
-- Compare each month's revenue with the same month in the previous year.
WITH monthly_revenue AS (
    SELECT
        CAST(strftime('%Y', o.order_date) AS INTEGER) AS year,
        CAST(strftime('%m', o.order_date) AS INTEGER) AS month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY year, month
)
SELECT
    curr.year,
    curr.month,
    ROUND(curr.revenue, 2) AS revenue,
    ROUND(prev.revenue, 2) AS prev_year_revenue,
    CASE
        WHEN prev.revenue IS NULL OR prev.revenue = 0 THEN NULL
        ELSE ROUND((curr.revenue - prev.revenue) * 100.0 / prev.revenue, 2)
    END AS yoy_growth_percent
FROM monthly_revenue curr
LEFT JOIN monthly_revenue prev
    ON prev.year = curr.year - 1 AND prev.month = curr.month
ORDER BY curr.year, curr.month;


-- 13. First/Last Value Analysis
-- For each customer, first purchased category vs most recent purchased category.
WITH customer_category_orders AS (
    SELECT
        o.customer_id,
        o.order_date,
        p.category,
        FIRST_VALUE(p.category) OVER (
            PARTITION BY o.customer_id ORDER BY o.order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS first_category,
        LAST_VALUE(p.category) OVER (
            PARTITION BY o.customer_id ORDER BY o.order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS last_category
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.customer_id IS NOT NULL
)
SELECT DISTINCT
    customer_id,
    first_category,
    last_category,
    CASE WHEN first_category != last_category THEN 'Yes' ELSE 'No' END AS category_shift
FROM customer_category_orders
ORDER BY customer_id;


-- 14. Cumulative Distribution
-- What percentage of total revenue comes from the top N% of customers.
WITH customer_revenue AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
),
totals AS (
    SELECT SUM(revenue) AS grand_total FROM customer_revenue
)
SELECT
    cr.customer_id,
    ROUND(cr.revenue, 2) AS revenue,
    ROUND(SUM(cr.revenue) OVER (ORDER BY cr.revenue DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_revenue,
    ROUND(100.0 * SUM(cr.revenue) OVER (ORDER BY cr.revenue DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / t.grand_total, 2) AS cumulative_percent
FROM customer_revenue cr, totals t
ORDER BY cr.revenue DESC;


-- 15. Complex CTE: Cohort Analysis
-- Group customers by registration month; track ordering activity in months 0-3 after registration.
WITH cohorts AS (
    SELECT
        customer_id,
        strftime('%Y-%m', registration_date) AS cohort_month,
        date(registration_date) AS reg_date
    FROM customers
),
customer_orders AS (
    SELECT
        o.customer_id,
        o.order_date,
        c.cohort_month,
        c.reg_date,
        CAST(
            (strftime('%Y', o.order_date) - strftime('%Y', c.reg_date)) * 12
            + (strftime('%m', o.order_date) - strftime('%m', c.reg_date))
        AS INTEGER) AS months_since_registration
    FROM orders o
    JOIN cohorts c ON c.customer_id = o.customer_id
    WHERE o.customer_id IS NOT NULL
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohorts
    GROUP BY cohort_month
),
cohort_activity AS (
    SELECT
        cohort_month,
        months_since_registration,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM customer_orders
    WHERE months_since_registration BETWEEN 0 AND 3
    GROUP BY cohort_month, months_since_registration
)
SELECT
    ca.cohort_month,
    ca.months_since_registration AS month_number,
    ca.active_customers,
    cs.cohort_size,
    ROUND(100.0 * ca.active_customers / cs.cohort_size, 2) AS retention_rate_percent
FROM cohort_activity ca
JOIN cohort_sizes cs ON cs.cohort_month = ca.cohort_month
ORDER BY ca.cohort_month, ca.months_since_registration;


-- 16. Self-Join with Window Function
-- Products frequently bought together (same order), pairs deduplicated (A-B == B-A, appears once).
SELECT
    pa.product_name AS product_a,
    pb.product_name AS product_b,
    COUNT(*) AS times_bought_together
FROM order_items oi1
JOIN order_items oi2
    ON oi1.order_id = oi2.order_id
    AND oi1.product_id < oi2.product_id   -- enforce ordering to avoid duplicate pairs & self-pairs
JOIN products pa ON pa.product_id = oi1.product_id
JOIN products pb ON pb.product_id = oi2.product_id
GROUP BY pa.product_name, pb.product_name
ORDER BY times_bought_together DESC
LIMIT 50;
