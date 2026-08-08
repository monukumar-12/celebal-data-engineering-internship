"""
Part 2: Data Cleaning
----------------------
Implements the cleaning functions required by the assignment:

  1. clean_orders()              - Fix date formats, handle NULL customer_ids
  2. clean_products()            - Normalize product names (trim spaces, title case)
  3. validate_emails()           - Return list of customer_ids with invalid emails
  4. check_referential_integrity() - Find order_items that reference non-existent orders

Output:
  - Cleaned CSV files written to data/cleaned/
  - A text report of every issue found written to reports/data_quality_report.txt
"""

import os
import re
import pandas as pd
from datetime import datetime

RAW_DIR = "data/raw"
CLEAN_DIR = "data/cleaned"
REPORT_PATH = "reports/data_quality_report.txt"

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ----------------------------------------------------------------------
# 1. clean_orders()
# ----------------------------------------------------------------------
def clean_orders(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Fixes:
      - order_date: parses both 'YYYY-MM-DD HH:MM:SS' and the malformed
        'DD-MM-YYYY' format, normalizes everything to 'YYYY-MM-DD HH:MM:SS'.
      - customer_id: NULL / empty values are kept as pandas NA (not silently
        dropped) so downstream SQL can treat them as unknown customers;
        the count is reported.
    """
    df = df.copy()
    issues = {"bad_date_format_fixed": 0, "unparseable_dates": 0, "null_customer_id": 0}

    def parse_date(value):
        value = str(value).strip()
        # Try the correct format first
        for fmt, is_correct in [("%Y-%m-%d %H:%M:%S", True), ("%d-%m-%Y", False)]:
            try:
                dt = datetime.strptime(value, fmt)
                if not is_correct:
                    issues["bad_date_format_fixed"] += 1
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        issues["unparseable_dates"] += 1
        return pd.NA

    df["order_date"] = df["order_date"].apply(parse_date)

    # Normalize missing customer_id (empty string, whitespace, "NULL", NaN) -> pd.NA
    def normalize_customer_id(value):
        if pd.isna(value):
            return pd.NA
        s = str(value).strip()
        if s == "" or s.upper() == "NULL":
            return pd.NA
        return s

    df["customer_id"] = df["customer_id"].apply(normalize_customer_id)
    issues["null_customer_id"] = int(df["customer_id"].isna().sum())

    return df, issues


# ----------------------------------------------------------------------
# 2. clean_products()
# ----------------------------------------------------------------------
def clean_products(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Normalizes product_name: trims leading/trailing/extra internal spaces
    and applies title case, e.g. '  premium flip phone  ' -> 'Premium Flip Phone'.
    """
    df = df.copy()
    issues = {"names_normalized": 0}

    def normalize_name(name):
        original = name
        # collapse multiple internal spaces, strip ends, apply title case
        cleaned = re.sub(r"\s+", " ", str(name)).strip().title()
        if cleaned != original:
            issues["names_normalized"] += 1
        return cleaned

    df["product_name"] = df["product_name"].apply(normalize_name)
    return df, issues


# ----------------------------------------------------------------------
# 3. validate_emails()
# ----------------------------------------------------------------------
def validate_emails(df: pd.DataFrame) -> list:
    """
    Returns a list of customer_ids whose email is invalid
    (missing '@', missing domain, or otherwise malformed).
    """
    invalid_ids = []
    for _, row in df.iterrows():
        email = str(row["email"])
        if not EMAIL_REGEX.match(email):
            invalid_ids.append(row["customer_id"])
    return invalid_ids


# ----------------------------------------------------------------------
# 4. check_referential_integrity()
# ----------------------------------------------------------------------
def check_referential_integrity(order_items_df: pd.DataFrame, orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the subset of order_items rows whose order_id does NOT exist
    in the orders table (orphaned rows).
    """
    valid_order_ids = set(orders_df["order_id"].astype(str))
    mask = ~order_items_df["order_id"].astype(str).isin(valid_order_ids)
    return order_items_df[mask]


# ----------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------
def main():
    os.makedirs(CLEAN_DIR, exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    orders = pd.read_csv(f"{RAW_DIR}/orders.csv", dtype={"customer_id": str})
    order_items = pd.read_csv(f"{RAW_DIR}/order_items.csv")
    products = pd.read_csv(f"{RAW_DIR}/products.csv")
    customers = pd.read_csv(f"{RAW_DIR}/customers.csv")

    report_lines = []
    report_lines.append("DATA QUALITY REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # 1. Clean orders
    cleaned_orders, order_issues = clean_orders(orders)
    report_lines.append("1. clean_orders()")
    report_lines.append(f"   - Bad-format dates fixed (DD-MM-YYYY -> YYYY-MM-DD HH:MM:SS): {order_issues['bad_date_format_fixed']}")
    report_lines.append(f"   - Unparseable dates (left blank / NaT): {order_issues['unparseable_dates']}")
    report_lines.append(f"   - NULL/missing customer_id rows: {order_issues['null_customer_id']}")
    report_lines.append("")

    # 2. Clean products
    cleaned_products, product_issues = clean_products(products)
    report_lines.append("2. clean_products()")
    report_lines.append(f"   - Product names normalized (spacing/case fixed): {product_issues['names_normalized']}")
    report_lines.append("")

    # 3. Validate emails
    invalid_email_ids = validate_emails(customers)
    report_lines.append("3. validate_emails()")
    report_lines.append(f"   - Invalid emails found: {len(invalid_email_ids)}")
    report_lines.append(f"   - Affected customer_ids: {invalid_email_ids}")
    report_lines.append("")

    # 4. Referential integrity
    orphaned = check_referential_integrity(order_items, orders)
    report_lines.append("4. check_referential_integrity()")
    report_lines.append(f"   - Orphaned order_items (order_id not in orders): {len(orphaned)}")
    if len(orphaned) > 0:
        report_lines.append(f"   - Orphaned item_ids: {orphaned['item_id'].tolist()}")
    report_lines.append("")

    # Extra useful checks (not strictly required, but valuable for a real report)
    neg_qty = order_items[order_items["quantity"] < 0]
    bad_discount = order_items[(order_items["discount_percent"] < 0) | (order_items["discount_percent"] > 100)]
    zero_qty = order_items[order_items["quantity"] == 0]
    report_lines.append("Additional checks")
    report_lines.append(f"   - Negative quantity rows (returns): {len(neg_qty)}")
    report_lines.append(f"   - discount_percent out of [0,100] range: {len(bad_discount)}")
    report_lines.append(f"   - Zero-quantity rows: {len(zero_qty)}")
    report_lines.append("")

    # Write cleaned CSVs
    cleaned_orders.to_csv(f"{CLEAN_DIR}/orders_cleaned.csv", index=False)
    cleaned_products.to_csv(f"{CLEAN_DIR}/products_cleaned.csv", index=False)
    order_items.to_csv(f"{CLEAN_DIR}/order_items_cleaned.csv", index=False)
    customers.to_csv(f"{CLEAN_DIR}/customers_cleaned.csv", index=False)

    report_lines.append("Cleaned files written to: " + CLEAN_DIR)
    report_text = "\n".join(report_lines)

    with open(REPORT_PATH, "w") as f:
        f.write(report_text)

    print(report_text)


if __name__ == "__main__":
    main()
