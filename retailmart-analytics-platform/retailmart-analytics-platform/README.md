# RetailMart Centralized Data Analytics Platform

A complete, runnable data engineering project that solves RetailMart's problem
statement: scattered raw CSVs (orders, customers, products, payments) with no
central place to analyze them. This builds a **Medallion Architecture**
(Bronze -> Silver -> Gold) that answers the business team's actual questions:

- Which products are trending?
- Which customers are about to churn?
- What was last month's revenue?

Every item in your tech-stack list has a corresponding, working piece of code
in this repo — see the mapping table below.

## Tech stack -> code mapping

| Tech stack item                          | File                                          |
|-------------------------------------------|------------------------------------------------|
| Python Basics - Load CSVs, count orders    | `src/bronze/ingest_bronze.py`                  |
| Pandas - Clean orders, delivery days       | `src/silver/clean_silver.py`                   |
| SQL SELECT/Keys - Order-customer joins     | `sql/gold_queries.sql` §1, `src/gold/build_gold.py` |
| WHERE + Indexes - Filter by order status   | `sql/gold_queries.sql` §2                      |
| GROUP BY - Monthly revenue                 | `sql/gold_queries.sql` §3                      |
| JOINs - Customer 360                       | `sql/gold_queries.sql` §4                      |
| CASE - Customer segments                   | `sql/gold_queries.sql` §5                      |
| Subqueries - Above-average spenders        | `sql/gold_queries.sql` §6                      |
| CTEs - Funnel analysis                     | `sql/gold_queries.sql` §7                      |
| Window Functions - Product rank by category| `sql/gold_queries.sql` §8                      |
| PySpark - Revenue at scale                 | `src/spark/revenue_at_scale.py`                |
| Delta Lake - Product catalogue SCD2        | `src/delta/scd2_product_catalog.py`            |
| Medallion - Bronze/Silver/Gold orders      | `data/bronze/`, `data/silver/`, `data/gold/`   |

## Architecture

```
data/raw/        <- messy synthetic CSVs (simulates RetailMart's scattered source systems)
      |
      v
data/bronze/     <- raw data landed as-is + ingestion metadata (Python, csv module)
      |
      v
data/silver/     <- cleaned, deduped, typed, standardized (Pandas)
      |
      v
data/gold/       <- business-ready aggregates (SQL via DuckDB): revenue,
                     customer 360, segments, churn candidates, funnel, product rank
```

Two extra tracks plug into the same Silver data to show the "at scale" and
"historical tracking" tech stack items:

- **`src/spark/revenue_at_scale.py`** — the same revenue/ranking logic,
  written in PySpark, so it scales from thousands of rows (this demo) to
  billions of rows (production) without changing the logic — just point it
  at distributed storage (S3/ADLS) and run on a cluster.
- **`src/delta/scd2_product_catalog.py`** — Delta Lake SCD2 for the product
  catalog, so historical orders always price against the price that was
  active *at the time*, not today's price.

## Quick start

```bash
python -m venv venv && source venv/bin/activate     # optional but recommended
pip install -r requirements.txt

python run_pipeline.py
```

This single command runs the full Bronze -> Silver -> Gold pipeline and
prints every Gold-layer result set to the console. Output CSVs land in
`data/gold/`:

| File                              | Business question it answers                  |
|-------------------------------------|-----------------------------------------------|
| `order_customer_join.csv`         | Basic order + customer lookup                 |
| `delivered_orders.csv`            | Which orders have been delivered               |
| `monthly_revenue.csv`             | What was last month's (and every month's) revenue |
| `customer_360.csv`                 | Unified view of every customer                |
| `customer_segments.csv`           | VIP/Gold/Silver/Bronze + churn-risk flag       |
| `above_average_spenders.csv`      | Customers spending above the average           |
| `funnel_analysis.csv`             | Placed -> Shipped -> Delivered drop-off rates  |
| `product_rank_by_category.csv`    | Top 5 trending products per category           |

### Run the individual layers separately

```bash
python src/generate_data.py            # regenerate synthetic raw CSVs
python src/bronze/ingest_bronze.py      # Bronze
python src/silver/clean_silver.py       # Silver
python src/gold/build_gold.py           # Gold (DuckDB SQL)
```

### PySpark (revenue at scale)

Requires a JDK (11 or 17) on your PATH.

```bash
pip install pyspark==3.5.3
python src/spark/revenue_at_scale.py
```

Outputs land in `data/gold_spark/` (Spark writes partitioned CSV folders).

### Delta Lake SCD2 (product catalog)

Requires a JDK **and** normal internet access, since Spark downloads the
Delta Lake JARs from Maven Central the first time it runs.

```bash
pip install pyspark==3.5.3 delta-spark==3.2.0
python src/delta/scd2_product_catalog.py
```

This builds a real Delta Lake table at `data/delta/product_catalog_scd2`
with `effective_start` / `effective_end` / `is_current` columns, using
Delta's `MERGE INTO` to close out old price versions and insert new ones —
and demonstrates Delta's time-travel feature (`.option("versionAsOf", 0)`).

If you don't have internet access handy (e.g. running in a locked-down
sandbox), run the pure-pandas equivalent instead — same SCD2 merge logic,
no Spark/Delta/JDK required:

```bash
python src/delta/scd2_pandas_demo.py
```

## Why the data looks "messy" on purpose

`src/generate_data.py` deliberately injects realistic data-quality problems
so the Silver-layer cleaning step has real work to do, matching what
RetailMart would actually see in production:

- duplicate customer rows
- missing emails/phone numbers
- inconsistent order-status casing (`Delivered` / `delivered` / `DELIVERED`)
- a few negative order quantities
- a few delivery dates recorded *before* the order date (data-entry errors)
- ~3% of orders with no matching payment record
- a second product catalog snapshot (`products_v2.csv`) with price changes,
  discontinued products, and new products — this is what feeds the SCD2 demo

## Project layout

```
retailmart-analytics-platform/
├── README.md
├── requirements.txt
├── run_pipeline.py              <- runs Bronze -> Silver -> Gold end-to-end
├── data/
│   ├── raw/                     <- synthetic source CSVs
│   ├── bronze/                  <- raw landed data + ingestion metadata
│   ├── silver/                  <- cleaned data
│   ├── gold/                    <- business-ready CSVs (from DuckDB SQL)
│   ├── gold_spark/               <- sample output from the PySpark job
│   └── delta_pandas_demo/       <- sample output from the SCD2 pandas demo
├── sql/
│   └── gold_queries.sql         <- every SQL concept, documented and runnable in DuckDB
└── src/
    ├── generate_data.py
    ├── bronze/ingest_bronze.py
    ├── silver/clean_silver.py
    ├── gold/build_gold.py
    ├── spark/revenue_at_scale.py
    └── delta/
        ├── scd2_product_catalog.py   <- real Delta Lake (needs internet + JDK)
        └── scd2_pandas_demo.py       <- same logic, pandas-only, runs anywhere
```

## Notes / next steps if you extend this

- Swap DuckDB for a real warehouse (Snowflake/BigQuery/Postgres) by pointing
  `build_gold.py` at a connection string instead of local CSVs — the SQL in
  `sql/gold_queries.sql` is ANSI-standard and will run with minimal changes.
- Swap local Spark for Databricks/EMR by changing `--silver-dir`/`--out-dir`
  to S3/ADLS paths — no logic changes needed.
- Add an orchestrator (Airflow/Dagster) to schedule
  `generate_data -> bronze -> silver -> gold -> spark -> delta` daily.
