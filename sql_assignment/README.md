# SQL Assignment – ShopEase Database

## Project Overview
This repository contains a SQL-based assignment completed as part of the Data Engineering Internship. The objective is to demonstrate understanding of SQL fundamentals, data filtering, aggregation, joins, database constraints, indexing, and advanced concepts such as CASE statements, ACID properties, and transactions.

The assignment is implemented using MySQL and tested in MySQL Workbench on the `shopease_db` database.

---

## Database Information

Database Name: `shopease_db`

### Tables
- customers
- products
- orders
- order_items

### Primary Keys
- customers: customer_id
- products: product_id
- orders: order_id
- order_items: item_id

### Foreign Key Relationships
- orders.customer_id → customers.customer_id
- order_items.order_id → orders.order_id
- order_items.product_id → products.product_id

---

## Folder Structure
sql_assignment/
├── dataset.sql
├── Section_A/
│ └── basic_queries.sql
├── Section_B/
│ └── filtering_queries.sql
├── Section_C/
│ └── aggregation_queries.sql
├── Section_D/
│ └── joins_queries.sql
├── Section_E/
│ └── advanced_queries.sql
└── README.md



---

## Section-wise Implementation

### Section A – SQL Basics
**SQL File:** `Section_A/basic_queries.sql`  
**Questions Covered:** Q1, Q2, Q3, Q6  

**README Explanation Questions:**  
- **Q4. Primary Key explanation**
- **Q5. Email constraint explanation**

**Q4. Why must a Primary Key be UNIQUE and NOT NULL?**  
A Primary Key uniquely identifies each row in a table.  
- UNIQUE ensures no two rows have the same identifier.  
- NOT NULL ensures every row is identifiable.  
Without these properties, data integrity and table relationships would break.

**Q5. Constraints on email column**  
The `email` column in the customers table has:
- UNIQUE constraint
- NOT NULL constraint  

If a duplicate email is inserted, MySQL throws a duplicate key error and rejects the insertion, preserving data integrity.

---

### Section B – Filtering and Optimization
**SQL File:** `Section_B/filtering_queries.sql`  
**Questions Covered:** Q7, Q8, Q9, Q10, Q11, Q12  

**README Explanation Questions:**  
- **Q11. Index explanation**
- **Q12. SARGability explanation**

**Q11. What does idx_orders_date index do?**  
The index `idx_orders_date` improves performance of queries filtering by `order_date` by allowing MySQL to locate rows quickly without scanning the entire table.

Example query that benefits from the index:

SELECT * FROM orders WHERE order_date >= '2024-08-15';




Q12. Why YEAR(join_date) prevents index usage?
Using a function like YEAR() on a column makes the query non-SARGable, so the index cannot be used efficiently.

Index-friendly rewrite:

SELECT * FROM customers
WHERE join_date BETWEEN '2024-01-01' AND '2024-12-31';



Section C – Aggregation

SQL File: Section_C/aggregation_queries.sql
Questions Covered: Q13, Q14, Q15, Q16, Q17, Q18

This section focuses on summarizing data using GROUP BY, HAVING, and aggregate functions such as COUNT, SUM, AVG, MIN, and MAX.


Section D – Joins and Relationships

SQL File: Section_D/joins_queries.sql
Questions Covered: Q19, Q20, Q21

README Explanation Questions:

Q22. LEFT JOIN vs RIGHT JOIN
Q23. Foreign key behavior

Q22. LEFT JOIN vs RIGHT JOIN

LEFT JOIN returns all records from the left table and matching records from the right table.
RIGHT JOIN returns all records from the right table and matching records from the left table.

A FULL OUTER JOIN would return all records from both tables, matching where possible. MySQL does not directly support FULL OUTER JOIN, but it can be simulated using UNION.

Q23. What happens if customer_id = 999 is inserted in orders?
Since customer_id 999 does not exist in the customers table, MySQL will raise a foreign key constraint error and prevent the insert, maintaining referential integrity.


SQL File: Section_E/advanced_queries.sql
Questions Covered: Q24, Q25, Q27

README Explanation Question:

Q26. ACID properties

Q26. ACID Properties Explanation

Atomicity: A transaction is all-or-nothing. If any step fails, all changes are rolled back.
Consistency: A transaction moves the database from one valid state to another.
Isolation: Concurrent transactions do not interfere with each other.
Durability: Once committed, changes persist even after a system failure.

Example: In a bank transfer, money should not be debited from one account unless it is successfully credited to another.

Tools Used
MySQL Workbench
MySQL 8.x
Git and GitHub


How to Execute
1.Run dataset.sql to create tables and insert data.
2.Execute each section’s SQL file individually in MySQL Workbench.
3.Review outputs and explanations in this README.
