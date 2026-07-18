# Spark Basics — Data Cleaning, Transformation & Aggregation

**Week 5 Assignment — Data Engineering 003**

## Objective

Understand Spark fundamentals and perform data cleaning, transformation, and aggregation using DataFrames.

## What You Will Learn

- What Spark is and why it is faster than MapReduce
- How to use Spark DataFrames
- How to clean and process data
- How to perform basic data analysis using Spark

## Steps to Follow

**Step 1: Understand Basics**
- Learn what MapReduce is (slow, because it reads/writes from disk)
- Learn why Spark is better: works in-memory (faster), easier to use with DataFrames

**Step 2: Start Spark**
- Open PySpark or a Jupyter Notebook with Spark
- Import Spark libraries
- Create a Spark session

**Step 3: Load Data**
- Load a CSV file into a Spark DataFrame
- View: first few rows, column names, data types

**Step 4: Data Cleaning**
- Remove duplicate rows
- Handle missing values: drop rows with null values, or fill missing values
- Check for incorrect or inconsistent data

**Step 5: Filter Data**
- Apply simple conditions: filter by age, category, region

**Step 6: Transform Data**
- Rename columns if needed
- Change data types (e.g., string → integer/timestamp)

**Step 7: Aggregation**
- Perform basic calculations: count total rows, find average values, find min/max values

**Step 8: Group Data**
- Use `groupBy()` to group data
- Apply functions like `count()`, `sum()`, `avg()`

**Step 9: Understand Advanced Concepts (Basic Idea Only)**
- Wide transformations: operations that move data across partitions
- Shuffle: data movement (can slow things down)
- *(You don't need deep knowledge — just basic understanding)*

**Step 10: Build a Simple Pipeline**

Combine everything:
- Load data
- Clean data
- Filter data
- Apply transformations
- Perform aggregation

## Output Requirements

- Your Spark code (PySpark or Scala)
- Output results (tables or printed results)
- Short explanation of:
  - What steps you performed
  - What you observed

## Repository Structure

```
spark-assignment/
├── data/
│   └── dataset.csv
├── notebook/
│   └── spark_basics.ipynb
├── output/
│   └── results.csv
└── README.md
```

## How to Run

1. Place your source CSV file in `data/dataset.csv`.
2. Open `notebook/spark_basics.ipynb`.
3. Update the data-loading cell to point to your dataset path.
4. Uncomment and run each code cell in order (data load → cleaning → filtering → transformation → aggregation → pipeline).
5. Export final results to `output/results.csv`.

## Summary of Concepts Covered

| Concept | Where it's Applied |
|---|---|
| MapReduce vs. Spark | Q1, Q2 |
| Removing duplicates | Q3, Q15 |
| Filtering & grouping | Q4, Q6, Q8 |
| Handling null values | Q5, Q9, Q12 |
| Immutability | Q7 |
| Schema changes (casting, renaming) | Q10, Q14 |
| Shuffle & wide transformations | Q11 |
| Multi-stat aggregation | Q13 |
| Full pipeline | Q15 |

## Resources

- Spark Questions reference sheet (see assignment resources link)
