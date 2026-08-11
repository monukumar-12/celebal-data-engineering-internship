"""
SILVER LAYER - Cleaning & Standardization
===========================================
Maps to tech stack: "Pandas - Clean orders, delivery days"

What happens here:
  - de-duplicate customers (exact duplicate rows from Bronze)
  - standardize order status casing (Delivered / delivered / DELIVERED -> Delivered)
  - fix / flag bad delivery dates (delivery before order date)
  - compute delivery_days = delivery_date - order_date
  - drop rows with negative quantity in order_items (bad data), flag them
  - cast price/quantity to proper numeric types
  - fill missing email/phone with explicit "UNKNOWN" rather than blank
  - enforce referential sanity (order_items must reference a real order/product)

Run:
    python src/silver/clean_silver.py
"""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")
SILVER_DIR = os.path.join(BASE_DIR, "data", "silver")
os.makedirs(SILVER_DIR, exist_ok=True)


def clean_customers():
    df = pd.read_csv(os.path.join(BRONZE_DIR, "customers.csv"))
    before = len(df)

    # de-dup on business key (customer_id) - keep first occurrence
    df = df.drop_duplicates(subset=["customer_id"], keep="first")

    df["email"] = df["email"].fillna("UNKNOWN").replace("", "UNKNOWN")
    df["phone"] = df["phone"].fillna("UNKNOWN").replace("", "UNKNOWN")
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")

    df = df.drop(columns=["_ingested_at", "_source_file"])
    df.to_csv(os.path.join(SILVER_DIR, "customers.csv"), index=False)
    print(f"  customers: {before} -> {len(df)} rows after de-dup "
          f"({before - len(df)} duplicates removed)")
    return df


def clean_products():
    df = pd.read_csv(os.path.join(BRONZE_DIR, "products.csv"))
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["active"] = df["active"].map({"Y": True, "N": False}).fillna(True)
    df = df.drop(columns=["_ingested_at", "_source_file"])
    df.to_csv(os.path.join(SILVER_DIR, "products.csv"), index=False)
    print(f"  products: {len(df)} rows cleaned")
    return df


def clean_orders():
    df = pd.read_csv(os.path.join(BRONZE_DIR, "orders.csv"))

    # standardize status casing: Title Case
    df["status"] = df["status"].str.strip().str.title()

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["delivery_date"] = pd.to_datetime(df["delivery_date"], errors="coerce")

    # flag data-entry errors where delivery precedes order
    bad_mask = df["delivery_date"].notna() & (df["delivery_date"] < df["order_date"])
    n_bad = bad_mask.sum()
    df.loc[bad_mask, "delivery_date"] = pd.NaT  # null out impossible dates
    df["is_delivery_date_corrected"] = bad_mask

    # delivery_days = delivery_date - order_date (NaN if not delivered yet)
    df["delivery_days"] = (df["delivery_date"] - df["order_date"]).dt.days

    df = df.drop(columns=["_ingested_at", "_source_file"])
    df.to_csv(os.path.join(SILVER_DIR, "orders.csv"), index=False)
    print(f"  orders: {len(df)} rows cleaned, {n_bad} bad delivery dates corrected to null")
    return df


def clean_order_items(valid_order_ids, valid_product_ids):
    df = pd.read_csv(os.path.join(BRONZE_DIR, "order_items.csv"))
    before = len(df)

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    # drop bad-quality rows: negative/zero/null quantity, referential breaks
    df = df[df["quantity"] > 0]
    df = df[df["order_id"].isin(valid_order_ids)]
    df = df[df["product_id"].isin(valid_product_ids)]

    df["line_total"] = df["quantity"] * df["unit_price"]

    df = df.drop(columns=["_ingested_at", "_source_file"])
    df.to_csv(os.path.join(SILVER_DIR, "order_items.csv"), index=False)
    print(f"  order_items: {before} -> {len(df)} rows after quality filtering "
          f"({before - len(df)} dropped)")
    return df


def clean_payments(valid_order_ids):
    df = pd.read_csv(os.path.join(BRONZE_DIR, "payments.csv"))
    before = len(df)

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df[df["order_id"].isin(valid_order_ids)]
    df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")

    df = df.drop(columns=["_ingested_at", "_source_file"])
    df.to_csv(os.path.join(SILVER_DIR, "payments.csv"), index=False)
    print(f"  payments: {before} -> {len(df)} rows after referential filtering")
    return df


def main():
    print("=" * 60)
    print("SILVER CLEANING")
    print("=" * 60)
    customers = clean_customers()
    products = clean_products()
    orders = clean_orders()
    order_items = clean_order_items(
        valid_order_ids=set(orders["order_id"]),
        valid_product_ids=set(products["product_id"]),
    )
    payments = clean_payments(valid_order_ids=set(orders["order_id"]))

    print("\nSilver layer complete ->", SILVER_DIR)
    print(f"  customers      : {len(customers)}")
    print(f"  products       : {len(products)}")
    print(f"  orders         : {len(orders)}")
    print(f"  order_items    : {len(order_items)}")
    print(f"  payments       : {len(payments)}")


if __name__ == "__main__":
    main()
