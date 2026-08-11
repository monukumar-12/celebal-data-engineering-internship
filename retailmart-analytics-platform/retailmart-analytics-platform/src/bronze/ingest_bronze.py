"""
BRONZE LAYER - Raw Ingestion
=============================
Maps to tech stack: "Python Basics - Load CSVs, count orders"

Responsibility of Bronze: land the raw data AS-IS (no cleaning, no dedup),
just add minimal metadata (ingestion timestamp, source file name) so we
always have an unmodified audit trail of what RetailMart's systems sent us.

Run:
    python src/bronze/ingest_bronze.py
"""

import csv
import os
import shutil
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")
os.makedirs(BRONZE_DIR, exist_ok=True)

SOURCE_FILES = ["customers.csv", "products.csv", "orders.csv",
                "order_items.csv", "payments.csv"]


def load_csv(path):
    """Basic Python: load a CSV into a list of dicts."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def add_ingestion_metadata(rows, source_file):
    ts = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["_ingested_at"] = ts
        row["_source_file"] = source_file
    return rows


def write_csv(rows, path):
    if not rows:
        print(f"  [skip] no rows for {path}")
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def count_orders(orders_rows):
    """The exact business ask from the problem statement: count orders."""
    return len(orders_rows)


def count_orders_by_status(orders_rows):
    counts = {}
    for row in orders_rows:
        status = row["status"].strip().lower()
        counts[status] = counts.get(status, 0) + 1
    return counts


def main():
    print("=" * 60)
    print("BRONZE INGESTION")
    print("=" * 60)

    all_tables = {}
    for fname in SOURCE_FILES:
        src_path = os.path.join(RAW_DIR, fname)
        rows = load_csv(src_path)
        rows = add_ingestion_metadata(rows, fname)
        out_path = os.path.join(BRONZE_DIR, fname)
        write_csv(rows, out_path)
        all_tables[fname] = rows
        print(f"  Ingested {fname:<20} -> {len(rows):>6} rows -> {out_path}")

    # also copy products_v2 into bronze (represents "today's" catalog extract)
    v2_rows = load_csv(os.path.join(RAW_DIR, "products_v2.csv"))
    v2_rows = add_ingestion_metadata(v2_rows, "products_v2.csv")
    write_csv(v2_rows, os.path.join(BRONZE_DIR, "products_v2.csv"))
    print(f"  Ingested products_v2.csv    -> {len(v2_rows):>6} rows")

    # ---- basic business question straight from the problem statement ----
    orders_rows = all_tables["orders.csv"]
    total_orders = count_orders(orders_rows)
    by_status = count_orders_by_status(orders_rows)

    print("\nBasic checks:")
    print(f"  Total orders ingested: {total_orders}")
    print("  Orders by status (raw, messy casing folded to lower for counting):")
    for status, cnt in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f"    {status:<12}: {cnt}")

    print("\nBronze layer complete ->", BRONZE_DIR)


if __name__ == "__main__":
    main()
