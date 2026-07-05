-- ============================================================
-- Week 3 Assignment
-- Celebal Technologies - Data Engineering Internship
-- Topic: Subqueries, CTEs & Window Functions
-- Dataset: Sample Superstore
-- ============================================================


-- ============================================================
-- STEP 1: Create and Use Database
-- ============================================================
CREATE DATABASE IF NOT EXISTS superstore_db;
USE superstore_db;


-- ============================================================
-- STEP 2: Verify Imported Dataset
-- (The CSV should already be imported as superstore_raw)
-- ============================================================

SELECT COUNT(*) AS Total_Rows
FROM superstore_raw;

SELECT *
FROM superstore_raw
LIMIT 10;


-- ============================================================
-- STEP 3: Create Customers Table
-- ============================================================

DROP TABLE IF EXISTS customers;

CREATE TABLE customers AS
SELECT DISTINCT
    `Customer ID`,
    `Customer Name`,
    Segment
FROM superstore_raw;

SELECT *
FROM customers
LIMIT 10;


-- ============================================================
-- STEP 4: Create Products Table
-- ============================================================

DROP TABLE IF EXISTS products;

CREATE TABLE products AS
SELECT DISTINCT
    `Product ID`,
    `Product Name`,
    Category,
    `Sub-Category`
FROM superstore_raw;

SELECT *
FROM products
LIMIT 10;


-- ============================================================
-- STEP 5: Create Orders Table
-- ============================================================

DROP TABLE IF EXISTS orders;

CREATE TABLE orders AS
SELECT
    `Order ID`,
    `Order Date`,
    `Ship Date`,
    `Ship Mode`,
    `Customer ID`,
    `Product ID`,
    Sales,
    Quantity,
    Profit,
    Region,
    State,
    City
FROM superstore_raw;

SELECT *
FROM orders
LIMIT 10;


-- ============================================================
-- SUBQUERY 1
-- Find Orders Above Average Sales
-- ============================================================

SELECT *
FROM orders
WHERE Sales >
(
    SELECT AVG(Sales)
    FROM orders
);


-- ============================================================
-- SUBQUERY 2
-- Highest Sale Made By Each Customer
-- ============================================================

SELECT *
FROM orders o
WHERE Sales =
(
    SELECT MAX(Sales)
    FROM orders
    WHERE `Customer ID` = o.`Customer ID`
);


-- ============================================================
-- CTE
-- Calculate Total Sales Per Customer
-- ============================================================

WITH customer_sales AS
(
    SELECT
        `Customer ID`,
        SUM(Sales) AS TotalSales
    FROM orders
    GROUP BY `Customer ID`
)

SELECT *
FROM customer_sales
ORDER BY TotalSales DESC;


-- ============================================================
-- WINDOW FUNCTION
-- ROW_NUMBER()
-- ============================================================

SELECT
    `Customer ID`,
    Sales,
    ROW_NUMBER() OVER
    (
        PARTITION BY `Customer ID`
        ORDER BY Sales DESC
    ) AS Row_Number
FROM orders;


-- ============================================================
-- WINDOW FUNCTION
-- RANK()
-- ============================================================

SELECT
    `Customer ID`,
    SUM(Sales) AS TotalSales,
    RANK() OVER
    (
        ORDER BY SUM(Sales) DESC
    ) AS Customer_Rank
FROM orders
GROUP BY `Customer ID`;


-- ============================================================
-- JOIN + CTE + WINDOW FUNCTION
-- Rank Customers Based On Total Sales
-- ============================================================

WITH customer_sales AS
(
    SELECT
        `Customer ID`,
        SUM(Sales) AS TotalSales
    FROM orders
    GROUP BY `Customer ID`
)

SELECT
    c.`Customer Name`,
    cs.TotalSales,
    RANK() OVER
    (
        ORDER BY cs.TotalSales DESC
    ) AS Customer_Rank
FROM customer_sales cs
JOIN customers c
ON cs.`Customer ID` = c.`Customer ID`;


-- ============================================================
-- BUSINESS QUERY 1
-- Top 10 Customers By Sales
-- ============================================================

SELECT
    `Customer ID`,
    SUM(Sales) AS TotalSales
FROM orders
GROUP BY `Customer ID`
ORDER BY TotalSales DESC
LIMIT 10;


-- ============================================================
-- BUSINESS QUERY 2
-- Bottom 10 Customers By Sales
-- ============================================================

SELECT
    `Customer ID`,
    SUM(Sales) AS TotalSales
FROM orders
GROUP BY `Customer ID`
ORDER BY TotalSales ASC
LIMIT 10;


-- ============================================================
-- BUSINESS QUERY 3
-- Customers Who Placed Only One Order
-- ============================================================

SELECT
    `Customer ID`,
    COUNT(DISTINCT `Order ID`) AS OrdersCount
FROM orders
GROUP BY `Customer ID`
HAVING COUNT(DISTINCT `Order ID`) = 1;


-- ============================================================
-- BUSINESS QUERY 4
-- Product Ranking By Sales
-- ============================================================

SELECT
    `Product ID`,
    SUM(Sales) AS TotalSales,
    RANK() OVER
    (
        ORDER BY SUM(Sales) DESC
    ) AS Product_Rank
FROM orders
GROUP BY `Product ID`;


-- ============================================================
-- WINDOW FUNCTION
-- DENSE_RANK()
-- ============================================================

SELECT
    `Customer ID`,
    SUM(Sales) AS TotalSales,
    DENSE_RANK() OVER (
        ORDER BY SUM(Sales) DESC
    ) AS Customer_Dense_Rank
FROM orders
GROUP BY `Customer ID`;

-- ============================================================
-- END OF ASSIGNMENT
-- ============================================================

