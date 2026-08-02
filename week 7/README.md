# Delta Lake MERGE Implementation

Week 7 assignment — incremental data processing using Delta Lake.

## What this project does

I have a customer dataset (`customer_master.csv`) and a second "incremental" dataset
(`customer_incremental.csv`) that simulates new signups and updates to existing customers.
The notebook loads both into Delta tables and applies a `MERGE` to combine them, using two
different strategies:

- **SCD Type 1** — the incoming record simply overwrites the old one. No history is kept.
- **SCD Type 2** — the old record is closed out (`is_current = False`, `end_date` set) and a
  new row is inserted for the updated version, so the full history of every customer is kept.

## Tech used

- Python, Pandas
- `deltalake` (delta-rs) for the actual Delta Lake tables + `MERGE` operations
- Jupyter Notebook

## Files

```
delta-lake-assignment/
│
├── data/
│   ├── customer_master.csv          # base dataset (has a few dupes/nulls on purpose, before cleaning)
│   └── customer_incremental.csv     # simulated new + updated records
│
├── notebooks/
│   └── delta_scd_assignment.ipynb   # main notebook, fully executed with outputs
│
├── screenshots/
│   ├── data_loading/
│   ├── data_cleaning/
│   ├── scd1/
│   ├── scd2/
│   ├── validation/
│   └── final_output/
│
├── report/
│   └── assignment_summary.pdf
│
└── README.md
```

## How to run it

```bash
pip install deltalake pandas pyarrow matplotlib jupyter
jupyter notebook notebooks/delta_scd_assignment.ipynb
```

Just run all cells top to bottom — the Delta tables get created fresh each run under a local
`delta_tables/` folder (not committed, since it's just generated output).

## Steps I followed

1. Loaded `customer_master.csv` and checked shape, dtypes, and nulls.
2. Cleaned it — dropped exact duplicate rows, filled missing `city`/`segment` with defaults,
   dropped rows with a missing `email`.
3. Wrote the cleaned data into a Delta table.
4. Loaded `customer_incremental.csv` (15 updates to existing customers + 20 new customers) and
   cleaned it the same way.
5. Ran a `MERGE` — SCD1 style — to update existing customers in place and insert the new ones.
6. Ran a second `MERGE` — SCD2 style — that keeps every version of a changed row instead of
   overwriting it.
7. Validated the results: row counts match what's expected, and there's no duplicate
   `customer_id` among the "current" records in either table.
8. Displayed the final tables and a short written summary at the end of the notebook.

## Result

- Master data: 106 raw rows → 95 clean rows after removing 6 duplicates + rows with missing email.
- Incremental batch: 35 rows (15 updates + 20 new customers).
- SCD1 final table: 117 rows, no duplicate customer IDs.
- SCD2 final table: 130 rows total (117 current + 13 closed-out historical versions).
- All validation checks passed.
