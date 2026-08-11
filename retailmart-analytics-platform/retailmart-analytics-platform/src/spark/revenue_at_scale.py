"""
PYSPARK - Revenue at Scale
=============================
Maps to tech stack: "PySpark - Revenue at scale"

Why PySpark here: pandas/DuckDB comfortably handle RetailMart's current
volume (thousands of rows), but the pipeline is written so that swapping
the Silver CSVs for millions/billions of rows (e.g. partitioned Parquet
in S3/ADLS) needs no logic change -- just point `SILVER_DIR` at the
distributed storage location and run this same script on a cluster.

What it computes (distributed, scalable versions of the same business
questions as the Gold SQL layer):
  - total & monthly revenue
  - revenue by category
  - top products by revenue (Spark window functions)
  - customer lifetime value at scale

Run locally (single-node, still real distributed execution engine):
    pip install pyspark
    python src/spark/revenue_at_scale.py

Run on a cluster (Databricks / EMR / on-prem):
    spark-submit src/spark/revenue_at_scale.py --silver-dir s3://bucket/silver --out-dir s3://bucket/gold_spark
"""

import argparse
import os

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--silver-dir", default=os.path.join(BASE_DIR, "data", "silver"))
    parser.add_argument("--out-dir", default=os.path.join(BASE_DIR, "data", "gold_spark"))
    return parser.parse_args()


def main():
    args = get_args()
    os.makedirs(args.out_dir, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("RetailMart-RevenueAtScale")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "8")  # small for local dev; raise on a real cluster
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    orders = spark.read.csv(os.path.join(args.silver_dir, "orders.csv"), header=True, inferSchema=True)
    order_items = spark.read.csv(os.path.join(args.silver_dir, "order_items.csv"), header=True, inferSchema=True)
    products = spark.read.csv(os.path.join(args.silver_dir, "products.csv"), header=True, inferSchema=True)
    customers = spark.read.csv(os.path.join(args.silver_dir, "customers.csv"), header=True, inferSchema=True)

    valid_orders = orders.filter(~F.col("status").isin("Cancelled", "Returned"))

    sales = (
        order_items
        .join(valid_orders, "order_id", "inner")
        .join(products, "product_id", "inner")
    )

    # ---- 1. Total revenue ----
    total_revenue = sales.agg(F.round(F.sum("line_total"), 2).alias("total_revenue")).collect()[0][0]
    print(f"TOTAL REVENUE (non-cancelled/returned orders): {total_revenue}")

    # ---- 2. Monthly revenue at scale ----
    monthly_revenue = (
        sales
        .withColumn("revenue_month", F.date_format("order_date", "yyyy-MM"))
        .groupBy("revenue_month")
        .agg(
            F.round(F.sum("line_total"), 2).alias("total_revenue"),
            F.countDistinct("order_id").alias("num_orders"),
        )
        .orderBy("revenue_month")
    )
    monthly_revenue.show(12, truncate=False)
    monthly_revenue.coalesce(1).write.mode("overwrite").option("header", True) \
        .csv(os.path.join(args.out_dir, "monthly_revenue"))

    # ---- 3. Revenue by category ----
    revenue_by_category = (
        sales.groupBy("category")
        .agg(F.round(F.sum("line_total"), 2).alias("revenue"))
        .orderBy(F.desc("revenue"))
    )
    revenue_by_category.show(truncate=False)
    revenue_by_category.coalesce(1).write.mode("overwrite").option("header", True) \
        .csv(os.path.join(args.out_dir, "revenue_by_category"))

    # ---- 4. Top products by revenue - Spark window function ----
    product_revenue = (
        sales.groupBy("product_id", "product_name", "category")
        .agg(
            F.sum("quantity").alias("units_sold"),
            F.round(F.sum("line_total"), 2).alias("revenue"),
        )
    )
    w = Window.partitionBy("category").orderBy(F.desc("revenue"))
    top_products = (
        product_revenue
        .withColumn("rank_in_category", F.rank().over(w))
        .filter(F.col("rank_in_category") <= 5)
        .orderBy("category", "rank_in_category")
    )
    top_products.show(20, truncate=False)
    top_products.coalesce(1).write.mode("overwrite").option("header", True) \
        .csv(os.path.join(args.out_dir, "top_products_by_category"))

    # ---- 5. Customer lifetime value at scale ----
    clv = (
        sales.join(customers, "customer_id", "inner")
        .groupBy("customer_id", "first_name", "last_name", "city")
        .agg(F.round(F.sum("line_total"), 2).alias("lifetime_value"))
        .orderBy(F.desc("lifetime_value"))
    )
    clv.show(10, truncate=False)
    clv.coalesce(1).write.mode("overwrite").option("header", True) \
        .csv(os.path.join(args.out_dir, "customer_lifetime_value"))

    print(f"\nSpark revenue-at-scale outputs written to: {args.out_dir}")
    spark.stop()


if __name__ == "__main__":
    main()
