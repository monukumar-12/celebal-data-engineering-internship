"""
Loads the cleaned CSV files into a SQLite database (database/ecommerce.db)
so that Part 3 (SQL Analysis) and Part 4 (CLI tool) can query it directly.
"""

import os
import sqlite3
import pandas as pd

CLEAN_DIR = "data/cleaned"
DB_PATH = "database/ecommerce.db"


def main():
    os.makedirs("database", exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)

    customers = pd.read_csv(f"{CLEAN_DIR}/customers_cleaned.csv")
    products = pd.read_csv(f"{CLEAN_DIR}/products_cleaned.csv")
    orders = pd.read_csv(f"{CLEAN_DIR}/orders_cleaned.csv")
    order_items = pd.read_csv(f"{CLEAN_DIR}/order_items_cleaned.csv")

    customers.to_sql("customers", conn, if_exists="replace", index=False)
    products.to_sql("products", conn, if_exists="replace", index=False)
    orders.to_sql("orders", conn, if_exists="replace", index=False)
    order_items.to_sql("order_items", conn, if_exists="replace", index=False)

    # Helpful indexes for join/window-function performance
    cur = conn.cursor()
    cur.execute("CREATE INDEX idx_orders_customer ON orders(customer_id)")
    cur.execute("CREATE INDEX idx_orders_date ON orders(order_date)")
    cur.execute("CREATE INDEX idx_items_order ON order_items(order_id)")
    cur.execute("CREATE INDEX idx_items_product ON order_items(product_id)")
    conn.commit()

    for table in ["customers", "products", "orders", "order_items"]:
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count} rows loaded")

    conn.close()
    print(f"\nDatabase created at {DB_PATH}")


if __name__ == "__main__":
    main()
