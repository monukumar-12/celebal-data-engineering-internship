"""
Part 4: Python + SQL Integration
----------------------------------
A command-line tool that:
  1. Takes user input for report type (daily/weekly/monthly)
  2. Takes a date range as input
  3. Connects to the SQLite database
  4. Generates a summary report showing:
       - Total orders, revenue, unique customers
       - Top 3 products
       - Comparison with the previous period (% change)

No external libraries except sqlite3 (standard library only).

Usage (interactive):
    python3 cli_report.py

Usage (non-interactive, for scripting/testing):
    python3 cli_report.py --type monthly --start 2024-01-01 --end 2024-01-31
"""

import sqlite3
import sys
import argparse
from datetime import datetime, timedelta

DB_PATH = "database/ecommerce.db"

REVENUE_EXPR = "oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)"


def parse_date(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y-%m-%d")


def get_period_summary(conn, start_date: str, end_date: str) -> dict:
    """Returns total orders, revenue, unique customers, and top 3 products
    for a given [start_date, end_date] range (inclusive, date-only)."""
    cur = conn.cursor()

    cur.execute(f"""
        SELECT
            COUNT(DISTINCT o.order_id)   AS total_orders,
            COALESCE(SUM({REVENUE_EXPR}), 0) AS total_revenue,
            COUNT(DISTINCT o.customer_id) AS unique_customers
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE date(o.order_date) BETWEEN date(?) AND date(?)
    """, (start_date, end_date))
    total_orders, total_revenue, unique_customers = cur.fetchone()

    cur.execute(f"""
        SELECT p.product_name, SUM({REVENUE_EXPR}) AS product_revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE date(o.order_date) BETWEEN date(?) AND date(?)
        GROUP BY p.product_name
        ORDER BY product_revenue DESC
        LIMIT 3
    """, (start_date, end_date))
    top_products = cur.fetchall()

    return {
        "total_orders": total_orders or 0,
        "total_revenue": round(total_revenue or 0, 2),
        "unique_customers": unique_customers or 0,
        "top_products": top_products,
    }


def previous_period(start_date: datetime, end_date: datetime) -> tuple:
    """Given a period, returns the immediately preceding period of the same length."""
    period_length = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)
    return prev_start.strftime("%Y-%m-%d"), prev_end.strftime("%Y-%m-%d")


def pct_change(current: float, previous: float):
    if previous in (0, None):
        return None
    return round((current - previous) * 100.0 / previous, 2)


def print_report(report_type: str, start_date: str, end_date: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        current = get_period_summary(conn, start_date, end_date)

        sd = parse_date(start_date)
        ed = parse_date(end_date)
        prev_start, prev_end = previous_period(sd, ed)
        previous = get_period_summary(conn, prev_start, prev_end)

        orders_change = pct_change(current["total_orders"], previous["total_orders"])
        revenue_change = pct_change(current["total_revenue"], previous["total_revenue"])
        customers_change = pct_change(current["unique_customers"], previous["unique_customers"])

        print("=" * 60)
        print(f"{report_type.upper()} SUMMARY REPORT")
        print(f"Period: {start_date} to {end_date}")
        print("=" * 60)
        print(f"Total Orders      : {current['total_orders']}")
        print(f"Total Revenue     : Rs. {current['total_revenue']:,.2f}")
        print(f"Unique Customers  : {current['unique_customers']}")
        print()
        print("Top 3 Products by Revenue:")
        if current["top_products"]:
            for i, (name, rev) in enumerate(current["top_products"], start=1):
                print(f"  {i}. {name} - Rs. {rev:,.2f}")
        else:
            print("  (no orders in this period)")
        print()
        print(f"Comparison with previous period ({prev_start} to {prev_end}):")
        print(f"  Orders    : {previous['total_orders']} -> {current['total_orders']} "
              f"({_fmt_pct(orders_change)})")
        print(f"  Revenue   : Rs. {previous['total_revenue']:,.2f} -> Rs. {current['total_revenue']:,.2f} "
              f"({_fmt_pct(revenue_change)})")
        print(f"  Customers : {previous['unique_customers']} -> {current['unique_customers']} "
              f"({_fmt_pct(customers_change)})")
        print("=" * 60)
    finally:
        conn.close()


def _fmt_pct(value):
    if value is None:
        return "N/A (no prior data)"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value}%"


def compute_default_range(report_type: str) -> tuple:
    """Provides a sensible default end date (latest order date in DB) and
    a start date based on the chosen report type, used when the user doesn't
    supply an explicit range in interactive mode."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT MAX(date(order_date)) FROM orders")
    latest = cur.fetchone()[0]
    conn.close()

    end_date = parse_date(latest)
    if report_type == "daily":
        start_date = end_date
    elif report_type == "weekly":
        start_date = end_date - timedelta(days=6)
    else:  # monthly
        start_date = end_date - timedelta(days=29)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def run_interactive():
    print("E-Commerce CLI Reporting Tool")
    print("-" * 40)
    report_type = ""
    while report_type not in ("daily", "weekly", "monthly"):
        report_type = input("Report type (daily/weekly/monthly): ").strip().lower()

    use_default = input("Use latest available date range for this report type? (y/n): ").strip().lower()
    if use_default == "y":
        start_date, end_date = compute_default_range(report_type)
        print(f"Using range: {start_date} to {end_date}")
    else:
        start_date = input("Start date (YYYY-MM-DD): ").strip()
        end_date = input("End date (YYYY-MM-DD): ").strip()
        try:
            parse_date(start_date)
            parse_date(end_date)
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)

    print_report(report_type, start_date, end_date)


def main():
    parser = argparse.ArgumentParser(description="E-Commerce CLI Reporting Tool")
    parser.add_argument("--type", choices=["daily", "weekly", "monthly"], help="Report type")
    parser.add_argument("--start", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    args = parser.parse_args()

    if args.type and args.start and args.end:
        print_report(args.type, args.start, args.end)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
