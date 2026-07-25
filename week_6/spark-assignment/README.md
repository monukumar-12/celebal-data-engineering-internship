# Week 6 — Spark Assignment

**Objective:** Understand Spark architecture and perform efficient data processing using
transformations, filtering, schema handling, and optimized file formats.

## Folder Structure

```
spark-assignment/
├── data/
│   └── source.csv                # sample dataset used by the notebook
├── notebooks/
│   └── week6_spark_assignment.ipynb   # all 15 Q&A + end-to-end pipeline (runnable PySpark)
├── output/                       
├── screenshots/                  
└── README.md
```

## What's Inside the Notebook

1. Spark session setup
2. Q1–Q15 answered with explanation + runnable PySpark code:
   - Driver / Cluster Manager / Executor roles
   - Lazy Evaluation & DAG
   - Reading CSV with schema inference
   - CSV vs Parquet (storage, performance)
   - Column selection & filtering
   - Renaming & type casting
   - Lineage graph fault tolerance
   - Multi-condition filters (AND / OR)
   - Predicate pushdown
   - Derived columns
   - Transformations vs Actions
   - Parquet → filter → CSV pipeline
   - Client Mode vs Cluster Mode
   - Why `.show()` over `.collect()` on huge datasets
3. A combined end-to-end pipeline (read → transform → filter → write)
4. Performance & architecture insights section



