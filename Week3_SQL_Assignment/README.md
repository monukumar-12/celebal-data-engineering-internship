# Week 3 Assignment - SQL

## Celebal Technologies Data Engineering Internship

### Objective

The objective of this assignment is to practice advanced SQL concepts by analyzing the Sample Superstore dataset using:

- Subqueries
- Common Table Expressions (CTEs)
- Window Functions
- Joins
- Customer Sales Analysis

---

## Dataset

**Dataset Name:** Sample Superstore

The dataset was imported into a staging table named:

```
superstore_raw
```

---

## Database

```
superstore_db
```

---

## Tables Created

- customers
- products
- orders

---

## SQL Concepts Covered

### 1. Subqueries

- Orders with above average sales
- Highest sales order for each customer

### 2. Common Table Expressions (CTEs)

- Customer-wise total sales

### 3. Window Functions

- ROW_NUMBER()
- RANK()
- DENSE_RANK()

### 4. JOIN + CTE + Window Functions

- Customer sales ranking

### 5. Business Analysis

- Top 10 Customers
- Bottom 10 Customers
- Customers with only one order
- Product Ranking by Sales

---

## Technologies Used

- MySQL Workbench
- SQL

---

## Project Structure

```
Week3_SQL_Assignment/
│
├── Week3_Assignment.sql
└── README.md
```

---

## Learning Outcomes

After completing this assignment, I gained hands-on experience with:

- Data normalization using SELECT DISTINCT
- Writing nested SQL queries
- Using CTEs to simplify complex queries
- Applying Window Functions for ranking and analysis
- Performing customer sales analysis
- Generating business insights from transactional data

---

