"""
DELTA LAKE - Product Catalog SCD2 (Slowly Changing Dimension Type 2)
========================================================================
Maps to tech stack: "Delta Lake - Product catalogue SCD2"

Why SCD2 matters for RetailMart: product prices change over time. If we
only keep the *current* price, historical revenue/margin analysis on old
orders becomes wrong (we'd re-price a $500 order from last year using
this year's price). SCD2 solves this by keeping every version of a
product row, each stamped with a validity window:

    product_id | price | ... | effective_start | effective_end | is_current

Data used:
    data/bronze/products.csv     -> initial catalog load (Day 1)
    data/bronze/products_v2.csv  -> a later extract with price changes,
                                     discontinued products, and new products

Run:
    pip install pyspark delta-spark
    python src/delta/scd2_product_catalog.py

Output:
    data/delta/product_catalog_scd2   (a real Delta Lake table on disk,
                                        readable with `spark.read.format("delta")`
                                        or any Delta-compatible engine)
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")
DELTA_DIR = os.path.join(BASE_DIR, "data", "delta")
TABLE_PATH = os.path.join(DELTA_DIR, "product_catalog_scd2")


def build_spark():
    builder = (
        SparkSession.builder
        .appName("RetailMart-SCD2-ProductCatalog")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()


def initial_load(spark):
    """Day 1: load the first product snapshot as the initial SCD2 state."""
    df = (
        spark.read.csv(os.path.join(BRONZE_DIR, "products.csv"), header=True, inferSchema=True)
        .select("product_id", "product_name", "category", "price", "active")
        .withColumn("effective_start", F.lit("2024-01-01").cast("date"))
        .withColumn("effective_end", F.lit(None).cast("date"))
        .withColumn("is_current", F.lit(True))
    )
    df.write.format("delta").mode("overwrite").save(TABLE_PATH)
    print(f"Initial SCD2 load complete: {df.count()} products -> {TABLE_PATH}")


def apply_scd2_merge(spark, as_of_date="2024-06-01"):
    """
    Day N: a new extract arrives (products_v2.csv). For every product whose
    price/active flag changed, we:
      1. close out the old row  (set effective_end + is_current = False)
      2. insert a new row       (new effective_start, is_current = True)
    Unchanged products are left untouched. This is the classic SCD2 pattern,
    implemented with Delta Lake's MERGE INTO.
    """
    new_extract = (
        spark.read.csv(os.path.join(BRONZE_DIR, "products_v2.csv"), header=True, inferSchema=True)
        .select("product_id", "product_name", "category", "price", "active")
    )

    delta_table = DeltaTable.forPath(spark, TABLE_PATH)
    current_rows = delta_table.toDF().filter("is_current = true")

    # detect which rows actually changed (price or active flag)
    changed = (
        new_extract.alias("new")
        .join(current_rows.alias("cur"), "product_id", "inner")
        .where(
            (F.col("new.price") != F.col("cur.price")) |
            (F.col("new.active") != F.col("cur.active"))
        )
        .select("new.product_id")
    )
    new_products = new_extract.join(current_rows, "product_id", "left_anti")

    changed_ids = [r.product_id for r in changed.collect()]
    print(f"Products with a real change (price/active): {len(changed_ids)}")
    print(f"Brand new products in this extract: {new_products.count()}")

    # ---- Step 1: close out old versions of changed products ----
    (
        delta_table.alias("t")
        .merge(
            changed.alias("c"),
            "t.product_id = c.product_id AND t.is_current = true",
        )
        .whenMatchedUpdate(set={
            "effective_end": F.lit(as_of_date).cast("date"),
            "is_current": F.lit(False),
        })
        .execute()
    )

    # ---- Step 2: insert new current versions for changed products ----
    new_versions = (
        new_extract.join(changed, "product_id", "inner")
        .withColumn("effective_start", F.lit(as_of_date).cast("date"))
        .withColumn("effective_end", F.lit(None).cast("date"))
        .withColumn("is_current", F.lit(True))
    )

    # ---- Step 3: insert brand-new products ----
    new_product_rows = (
        new_products
        .withColumn("effective_start", F.lit(as_of_date).cast("date"))
        .withColumn("effective_end", F.lit(None).cast("date"))
        .withColumn("is_current", F.lit(True))
    )

    to_insert = new_versions.unionByName(new_product_rows)
    to_insert.write.format("delta").mode("append").save(TABLE_PATH)
    print(f"Inserted {to_insert.count()} new SCD2 row-versions.")


def show_history_sample(spark, sample_ids=None):
    df = spark.read.format("delta").load(TABLE_PATH).orderBy("product_id", "effective_start")
    if sample_ids:
        df = df.filter(F.col("product_id").isin(sample_ids))
    df.show(30, truncate=False)

    # Delta Lake time travel: read the table as it looked at version 0
    print("\n-- Time travel: table as of version 0 (initial load) --")
    spark.read.format("delta").option("versionAsOf", 0).load(TABLE_PATH) \
        .filter(F.col("product_id").isin(sample_ids) if sample_ids else F.lit(True)) \
        .show(10, truncate=False)


def main():
    os.makedirs(DELTA_DIR, exist_ok=True)
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    initial_load(spark)

    # find a couple of product_ids that actually changed, for a readable demo
    v1 = spark.read.csv(os.path.join(BRONZE_DIR, "products.csv"), header=True, inferSchema=True)
    v2 = spark.read.csv(os.path.join(BRONZE_DIR, "products_v2.csv"), header=True, inferSchema=True)
    changed_sample = (
        v1.alias("a").join(v2.alias("b"), "product_id")
        .where(F.col("a.price") != F.col("b.price"))
        .select("product_id").limit(3).toPandas()["product_id"].tolist()
    )

    apply_scd2_merge(spark, as_of_date="2024-06-01")

    print("\n=== SCD2 history for a few changed products ===")
    show_history_sample(spark, sample_ids=changed_sample)

    print(f"\nDelta table ready at: {TABLE_PATH}")
    print("Query it any time with:")
    print('  spark.read.format("delta").load(TABLE_PATH)')

    spark.stop()


if __name__ == "__main__":
    main()
