"""
SCD2 LOGIC DEMO (pandas version - no Spark cluster / internet required)
===========================================================================
This mirrors the EXACT same SCD2 merge logic as src/delta/scd2_product_catalog.py,
implemented in pandas so you can run and verify it instantly, anywhere,
with no Java/Spark/Delta JAR downloads needed.

Use this to sanity-check the SCD2 business logic. For the real, production
pattern (Delta Lake MERGE INTO, ACID transactions, time travel, table
versioning), use src/delta/scd2_product_catalog.py on a machine/cluster
with internet access to Maven Central (Databricks, EMR, or local Spark
with normal internet access).

Run:
    python src/delta/scd2_pandas_demo.py
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")
DELTA_DEMO_DIR = os.path.join(BASE_DIR, "data", "delta_pandas_demo")
os.makedirs(DELTA_DEMO_DIR, exist_ok=True)


def initial_load(v1):
    df = v1[["product_id", "product_name", "category", "price", "active"]].copy()
    df["effective_start"] = pd.Timestamp("2024-01-01")
    df["effective_end"] = pd.NaT
    df["is_current"] = True
    return df


def scd2_merge(scd_table, v2, as_of_date="2024-06-01"):
    as_of = pd.Timestamp(as_of_date)
    current = scd_table[scd_table["is_current"]].set_index("product_id")

    v2 = v2[["product_id", "product_name", "category", "price", "active"]].copy()
    v2_idx = v2.set_index("product_id")

    common_ids = current.index.intersection(v2_idx.index)
    changed_mask = (
        (current.loc[common_ids, "price"].round(2) != v2_idx.loc[common_ids, "price"].round(2)) |
        (current.loc[common_ids, "active"] != v2_idx.loc[common_ids, "active"])
    )
    changed_ids = common_ids[changed_mask]
    new_ids = v2_idx.index.difference(current.index)

    print(f"  Changed products (price/active flip): {len(changed_ids)}")
    print(f"  Brand-new products in this extract:    {len(new_ids)}")

    # Step 1: close out old current rows for changed products
    close_mask = scd_table["is_current"] & scd_table["product_id"].isin(changed_ids)
    scd_table.loc[close_mask, "effective_end"] = as_of
    scd_table.loc[close_mask, "is_current"] = False

    # Step 2: new versions for changed products
    new_versions = v2[v2["product_id"].isin(changed_ids)].copy()
    new_versions["effective_start"] = as_of
    new_versions["effective_end"] = pd.NaT
    new_versions["is_current"] = True

    # Step 3: brand new products
    new_rows = v2[v2["product_id"].isin(new_ids)].copy()
    new_rows["effective_start"] = as_of
    new_rows["effective_end"] = pd.NaT
    new_rows["is_current"] = True

    scd_table = pd.concat([scd_table, new_versions, new_rows], ignore_index=True)
    return scd_table


def main():
    print("=" * 60)
    print("SCD2 DEMO (pandas) - Product Catalog")
    print("=" * 60)

    v1 = pd.read_csv(os.path.join(BRONZE_DIR, "products.csv"))
    v2 = pd.read_csv(os.path.join(BRONZE_DIR, "products_v2.csv"))

    scd_table = initial_load(v1)
    print(f"\nInitial load: {len(scd_table)} products (version 1, effective_start=2024-01-01)")

    print("\nApplying SCD2 merge against products_v2.csv (as_of=2024-06-01)...")
    scd_table = scd2_merge(scd_table, v2, as_of_date="2024-06-01")

    out_path = os.path.join(DELTA_DEMO_DIR, "product_catalog_scd2.csv")
    scd_table.sort_values(["product_id", "effective_start"]).to_csv(out_path, index=False)
    print(f"\nFinal SCD2 table: {len(scd_table)} row-versions -> {out_path}")

    # show a readable sample of products that actually changed
    dup_ids = scd_table["product_id"].value_counts()
    sample_ids = dup_ids[dup_ids > 1].index[:4]
    sample = scd_table[scd_table["product_id"].isin(sample_ids)] \
        .sort_values(["product_id", "effective_start"])
    print("\nSample SCD2 history (products with more than one version):")
    print(sample.to_string(index=False))


if __name__ == "__main__":
    main()
