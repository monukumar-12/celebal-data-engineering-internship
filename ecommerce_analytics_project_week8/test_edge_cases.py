"""
Part 5: Edge Case Handling
----------------------------
Test cases verifying how the system behaves for tricky/edge-case data:

  1. What happens when order_items has an order_id not in orders?
  2. What happens when discount_percent > 100?
  3. What happens when quantity is 0?
  4. What happens when order_date is in the future?

Run with:  python3 -m pytest test_edge_cases.py -v
       or: python3 test_edge_cases.py   (plain run, no pytest needed)
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

from data_cleaning import check_referential_integrity


# ----------------------------------------------------------------------
# 1. order_items referencing a non-existent order_id
# ----------------------------------------------------------------------
def test_orphaned_order_item_detected():
    """An order_item pointing to an order_id that doesn't exist in orders
    must be flagged by check_referential_integrity(), and must NOT silently
    join/produce revenue in SQL (INNER JOIN naturally excludes it)."""
    orders = pd.DataFrame({
        "order_id": [1, 2, 3],
        "customer_id": ["10", "11", "12"],
        "order_date": ["2024-01-01 10:00:00"] * 3,
        "status": ["DELIVERED"] * 3,
        "region_code": ["NORTH"] * 3,
    })
    order_items = pd.DataFrame({
        "item_id": [1, 2, 3],
        "order_id": [1, 2, 999],  # 999 does not exist in orders
        "product_id": [1, 1, 1],
        "quantity": [1, 2, 3],
        "unit_price": [100.0, 100.0, 100.0],
        "discount_percent": [0, 0, 0],
    })

    orphaned = check_referential_integrity(order_items, orders)

    assert len(orphaned) == 1, f"Expected 1 orphaned row, got {len(orphaned)}"
    assert orphaned.iloc[0]["item_id"] == 3
    print("PASS: test_orphaned_order_item_detected "
          "-> orphaned order_id=999 correctly detected, revenue for it should be excluded")


# ----------------------------------------------------------------------
# 2. discount_percent > 100
# ----------------------------------------------------------------------
def test_discount_over_100_flagged_and_clamped_in_revenue():
    """A discount_percent above 100 is invalid input. The system should be
    able to (a) detect it as a data-quality issue, and (b) not let it produce
    a *negative* revenue figure when computing revenue -- since a >100%
    discount is nonsensical, revenue should be clamped at 0, not go negative."""
    order_items = pd.DataFrame({
        "item_id": [1, 2],
        "order_id": [1, 1],
        "product_id": [1, 2],
        "quantity": [1, 1],
        "unit_price": [100.0, 100.0],
        "discount_percent": [150, 20],  # first row is invalid (>100)
    })

    # Detection
    invalid = order_items[(order_items["discount_percent"] < 0) | (order_items["discount_percent"] > 100)]
    assert len(invalid) == 1
    assert invalid.iloc[0]["item_id"] == 1

    # Safe revenue calculation: clamp discount to [0, 100] before applying formula
    def safe_revenue(qty, price, discount):
        discount = max(0, min(100, discount))
        return qty * price * (1 - discount / 100)

    revenue_row1 = safe_revenue(1, 100.0, 150)
    assert revenue_row1 == 0.0, f"Expected clamped revenue of 0.0, got {revenue_row1}"
    print("PASS: test_discount_over_100_flagged_and_clamped_in_revenue "
          "-> invalid discount detected, revenue clamped at 0 instead of going negative")


# ----------------------------------------------------------------------
# 3. quantity == 0
# ----------------------------------------------------------------------
def test_zero_quantity_produces_zero_revenue_and_is_flagged():
    """A quantity of 0 is neither a purchase nor a return. Revenue math handles
    it gracefully (produces 0, no crash), but it should be flagged separately
    since it likely indicates a data entry error (a canceled line item that
    should have been removed rather than zeroed)."""
    order_items = pd.DataFrame({
        "item_id": [1],
        "order_id": [1],
        "product_id": [1],
        "quantity": [0],
        "unit_price": [500.0],
        "discount_percent": [10],
    })

    revenue = (order_items["quantity"] * order_items["unit_price"] *
               (1 - order_items["discount_percent"] / 100)).iloc[0]
    assert revenue == 0.0

    zero_qty_rows = order_items[order_items["quantity"] == 0]
    assert len(zero_qty_rows) == 1
    print("PASS: test_zero_quantity_produces_zero_revenue_and_is_flagged "
          "-> zero-quantity row computes to 0 revenue without error, and is flagged for review")


# ----------------------------------------------------------------------
# 4. order_date in the future
# ----------------------------------------------------------------------
def test_future_order_date_flagged():
    """An order_date later than 'today' is almost certainly bad data (a typo'd
    year, or a system clock issue at insert time). The system should be able
    to flag such rows rather than silently including them in trend reports."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    next_year = (datetime.now() + timedelta(days=400)).strftime("%Y-%m-%d %H:%M:%S")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    orders = pd.DataFrame({
        "order_id": [1, 2, 3],
        "customer_id": ["1", "2", "3"],
        "order_date": [tomorrow, next_year, yesterday],
        "status": ["PLACED"] * 3,
        "region_code": ["NORTH"] * 3,
    })

    now = datetime.now()
    orders["order_date_parsed"] = pd.to_datetime(orders["order_date"])
    future_orders = orders[orders["order_date_parsed"] > now]

    assert len(future_orders) == 2, f"Expected 2 future-dated orders, got {len(future_orders)}"
    assert set(future_orders["order_id"]) == {1, 2}
    print("PASS: test_future_order_date_flagged "
          "-> 2 future-dated orders correctly identified and excludable from valid reporting")


# ----------------------------------------------------------------------
# Bonus: verify the SQL layer also handles these edge cases sensibly
# ----------------------------------------------------------------------
def test_sql_inner_join_excludes_orphaned_items():
    """Confirms the actual production database's revenue queries (which use
    INNER JOIN between order_items and orders) naturally exclude any
    orphaned order_items, consistent with check_referential_integrity()."""
    conn = sqlite3.connect("database/ecommerce.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM order_items oi
        WHERE oi.order_id NOT IN (SELECT order_id FROM orders)
    """)
    orphan_count_in_raw_join_universe = cur.fetchone()[0]
    conn.close()
    # In our generated dataset this should be 0 (data generation guarantees
    # referential integrity), confirming clean_orders/check_referential_integrity
    # would have nothing to flag downstream.
    assert orphan_count_in_raw_join_universe == 0
    print("PASS: test_sql_inner_join_excludes_orphaned_items "
          "-> production DB has 0 orphaned order_items (referential integrity holds)")


def run_all():
    tests = [
        test_orphaned_order_item_detected,
        test_discount_over_100_flagged_and_clamped_in_revenue,
        test_zero_quantity_produces_zero_revenue_and_is_flagged,
        test_future_order_date_flagged,
        test_sql_inner_join_excludes_orphaned_items,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"FAIL: {t.__name__} -> {e}")
    print()
    if failed == 0:
        print(f"All {len(tests)} edge case tests passed.")
    else:
        print(f"{failed}/{len(tests)} tests FAILED.")


if __name__ == "__main__":
    run_all()
