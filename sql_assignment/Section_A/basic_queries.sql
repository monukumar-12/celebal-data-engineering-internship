/* ================================
   Section A — SQL Basics
   Database: shopease_db
   ================================ */

USE shopease_db;

/* Q1. Display all customers */
SELECT * FROM customers;

/* Q2. Display first name, last name, city */
SELECT first_name, last_name, city
FROM customers;

/* Q3. Unique product categories */
SELECT DISTINCT category
FROM products;

/* Q4. Primary Keys (schema reference)
   customers(customer_id)
   products(product_id)
   orders(order_id)
   order_items(item_id)
*/

/* Q5. Email constraints check */
-- UNIQUE + NOT NULL already applied on email column

/* Q6. Invalid product insert (CHECK constraint test) */
INSERT INTO products
VALUES (999, 'Invalid Product', 'Test', 'TestBrand', -50, 10);