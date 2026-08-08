"""
Part 1: Data Generation
------------------------
Generates 4 CSV files with realistic, intentionally-messy e-commerce data:
  - customers.csv
  - products.csv
  - orders.csv
  - order_items.csv

Intentional data quality issues introduced:
  - 5% of orders have NULL customer_id
  - 3% of order_items have negative quantity (returns)
  - Some orders have order_date in wrong format (DD-MM-YYYY instead of YYYY-MM-DD HH:MM:SS)
  - Some product names have extra spaces / mixed case
  - 2% of emails are invalid (missing @ or domain)

Referential integrity: every order_id used in order_items.csv is guaranteed to
exist in orders.csv, because order_items are generated FROM the orders table
(we loop over already-created order_ids rather than inventing new ones).
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)  # reproducible runs

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
N_CUSTOMERS = 600
N_PRODUCTS = 150
N_ORDERS = 2500
AVG_ITEMS_PER_ORDER = 2.3  # -> generates well over 500 rows in order_items.csv

OUTPUT_DIR = "data/raw"

FIRST_NAMES = ["Amit", "Priya", "Rahul", "Sneha", "Vikram", "Anita", "Rohan", "Kavya",
               "Arjun", "Neha", "Suresh", "Divya", "Karan", "Pooja", "Manoj", "Ritu",
               "Sanjay", "Meera", "Ajay", "Isha", "Deepak", "Shreya", "Nikhil", "Tanvi",
               "Rajesh", "Swati", "Vivek", "Ananya", "Gaurav", "Payal"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Gupta", "Reddy", "Nair", "Iyer", "Singh",
              "Mishra", "Das", "Rao", "Menon", "Kapoor", "Chatterjee", "Joshi", "Bose",
              "Agarwal", "Chauhan", "Mehta", "Pillai"]

CATEGORY_MAP = {
    "Electronics": ["Mobiles", "Laptops", "Headphones", "Cameras", "Accessories"],
    "Clothing": ["Men", "Women", "Kids", "Footwear", "Winterwear"],
    "Home": ["Kitchen", "Furniture", "Decor", "Bedding", "Storage"],
    "Books": ["Fiction", "Non-Fiction", "Academic", "Comics", "Children"],
}

PRODUCT_ADJECTIVES = ["Premium", "Classic", "Pro", "Mini", "Deluxe", "Essential",
                      "Ultra", "Compact", "Smart", "Everyday"]
PRODUCT_NOUNS = {
    "Mobiles": ["Smartphone X1", "Smartphone Z2", "Flip Phone", "Tablet Mini"],
    "Laptops": ["Notebook 14", "Ultrabook Air", "Gaming Laptop", "Chromebook"],
    "Headphones": ["Wireless Earbuds", "Over-Ear Headphones", "Neckband", "Speaker"],
    "Cameras": ["DSLR Camera", "Action Camera", "Instant Camera", "Webcam"],
    "Accessories": ["Charger Cable", "Power Bank", "Phone Case", "Screen Guard"],
    "Men": ["Cotton Shirt", "Denim Jeans", "Formal Trousers", "Polo T-Shirt"],
    "Women": ["Kurti", "Maxi Dress", "Palazzo Pants", "Denim Jacket"],
    "Kids": ["Graphic T-Shirt", "Shorts Set", "School Uniform", "Raincoat"],
    "Footwear": ["Running Shoes", "Sandals", "Formal Shoes", "Sneakers"],
    "Winterwear": ["Wool Sweater", "Puffer Jacket", "Fleece Hoodie", "Muffler"],
    "Kitchen": ["Non-Stick Pan", "Blender", "Cutlery Set", "Pressure Cooker"],
    "Furniture": ["Study Table", "Bookshelf", "Office Chair", "Bed Frame"],
    "Decor": ["Wall Clock", "Table Lamp", "Photo Frame", "Wall Art"],
    "Bedding": ["Cotton Bedsheet", "Pillow Set", "Comforter", "Mattress Protector"],
    "Storage": ["Plastic Organizer", "Shoe Rack", "Storage Box", "Wardrobe"],
    "Fiction": ["Mystery Novel", "Fantasy Epic", "Thriller Paperback", "Romance Novel"],
    "Non-Fiction": ["Biography", "Self-Help Guide", "History Book", "Travel Memoir"],
    "Academic": ["Textbook", "Reference Guide", "Exam Prep Book", "Workbook"],
    "Comics": ["Graphic Novel", "Comic Anthology", "Manga Volume", "Superhero Comic"],
    "Children": ["Picture Book", "Story Collection", "Activity Book", "Board Book"],
}

STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
STATUS_WEIGHTS = [0.15, 0.15, 0.50, 0.10, 0.10]
CUSTOMER_TYPES = ["REGULAR", "PREMIUM", "VIP"]
CUSTOMER_TYPE_WEIGHTS = [0.65, 0.25, 0.10]
REGIONS = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)


def random_date(start, end):
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def make_messy_email(name, idx, make_invalid):
    base = name.lower().replace(" ", ".")
    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "mail.com"])
    if make_invalid:
        # missing @ or missing domain
        if random.random() < 0.5:
            return f"{base}{idx}{domain}"          # missing @
        else:
            return f"{base}{idx}@"                 # missing domain
    return f"{base}{idx}@{domain}"


def messy_product_name(name):
    """Randomly add extra spaces or scramble the case to simulate dirty data."""
    variant = random.random()
    if variant < 0.15:
        # extra spaces
        words = name.split(" ")
        name = "  ".join(words) + "  "
    elif variant < 0.30:
        # weird case (all lower or all upper)
        name = name.lower() if random.random() < 0.5 else name.upper()
    return name


# ----------------------------------------------------------------------
# 1. customers.csv
# ----------------------------------------------------------------------
def generate_customers():
    rows = []
    n_invalid_email_target = int(N_CUSTOMERS * 0.02)
    invalid_indices = set(random.sample(range(1, N_CUSTOMERS + 1), n_invalid_email_target))

    for cid in range(1, N_CUSTOMERS + 1):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        email = make_messy_email(name, cid, cid in invalid_indices)
        reg_date = random_date(START_DATE, END_DATE - timedelta(days=30))
        ctype = random.choices(CUSTOMER_TYPES, weights=CUSTOMER_TYPE_WEIGHTS)[0]
        rows.append({
            "customer_id": cid,
            "customer_name": name,
            "email": email,
            "registration_date": reg_date.strftime("%Y-%m-%d %H:%M:%S"),
            "customer_type": ctype,
        })

    with open(f"{OUTPUT_DIR}/customers.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"customers.csv -> {len(rows)} rows "
          f"({n_invalid_email_target} invalid emails)")
    return rows


# ----------------------------------------------------------------------
# 2. products.csv
# ----------------------------------------------------------------------
def generate_products():
    rows = []
    pid = 1
    for category, subcats in CATEGORY_MAP.items():
        for subcat in subcats:
            nouns = PRODUCT_NOUNS[subcat]
            n_per_subcat = N_PRODUCTS // (len(CATEGORY_MAP) * 5)  # ~ evenly spread
            for _ in range(max(1, n_per_subcat)):
                adj = random.choice(PRODUCT_ADJECTIVES)
                noun = random.choice(nouns)
                clean_name = f"{adj} {noun}"
                name = messy_product_name(clean_name)
                cost_price = round(random.uniform(50, 25000), 2)
                rows.append({
                    "product_id": pid,
                    "product_name": name,
                    "category": category,
                    "subcategory": subcat,
                    "cost_price": cost_price,
                })
                pid += 1
                if pid > N_PRODUCTS:
                    break
            if pid > N_PRODUCTS:
                break
        if pid > N_PRODUCTS:
            break

    with open(f"{OUTPUT_DIR}/products.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"products.csv -> {len(rows)} rows")
    return rows


# ----------------------------------------------------------------------
# 3. orders.csv
# ----------------------------------------------------------------------
def generate_orders(customers):
    rows = []
    n_null_customer_target = int(N_ORDERS * 0.05)
    null_indices = set(random.sample(range(1, N_ORDERS + 1), n_null_customer_target))

    n_bad_date_target = int(N_ORDERS * 0.06)
    bad_date_indices = set(random.sample(range(1, N_ORDERS + 1), n_bad_date_target))

    customer_ids = [c["customer_id"] for c in customers]

    for oid in range(1, N_ORDERS + 1):
        if oid in null_indices:
            customer_id = ""  # NULL / empty
        else:
            customer_id = random.choice(customer_ids)

        order_dt = random_date(START_DATE, END_DATE)
        if oid in bad_date_indices:
            # Wrong format: DD-MM-YYYY (drops the time component)
            order_date_str = order_dt.strftime("%d-%m-%Y")
        else:
            order_date_str = order_dt.strftime("%Y-%m-%d %H:%M:%S")

        status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
        region = random.choice(REGIONS)

        rows.append({
            "order_id": oid,
            "customer_id": customer_id,
            "order_date": order_date_str,
            "status": status,
            "region_code": region,
            "_dt": order_dt,  # kept internally to build order_items sensibly; stripped before writing
        })

    with open(f"{OUTPUT_DIR}/orders.csv", "w", newline="") as f:
        fieldnames = ["order_id", "customer_id", "order_date", "status", "region_code"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})

    print(f"orders.csv -> {len(rows)} rows "
          f"({n_null_customer_target} NULL customer_id, {n_bad_date_target} bad date format)")
    return rows


# ----------------------------------------------------------------------
# 4. order_items.csv
# ----------------------------------------------------------------------
def generate_order_items(orders, products):
    rows = []
    item_id = 1
    product_ids = [p["product_id"] for p in products]
    product_price_hint = {p["product_id"]: p["cost_price"] for p in products}

    # First pass: build every row, tagging which ones are candidates for negative qty
    for order in orders:
        n_items = max(1, int(random.gauss(AVG_ITEMS_PER_ORDER, 1)))
        chosen_products = random.sample(product_ids, min(n_items, len(product_ids)))
        for pid in chosen_products:
            quantity = random.randint(1, 5)
            # unit price roughly cost_price * markup, independent-ish of cost
            unit_price = round(product_price_hint[pid] * random.uniform(1.15, 1.8), 2)
            discount_percent = round(random.choice([0, 0, 0, 5, 10, 15, 20, 25, 30]), 2)
            rows.append({
                "item_id": item_id,
                "order_id": order["order_id"],
                "product_id": pid,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_percent": discount_percent,
            })
            item_id += 1

    # Second pass: flip 3% of rows to negative quantity (returns)
    n_negative_target = int(len(rows) * 0.03)
    negative_indices = random.sample(range(len(rows)), n_negative_target)
    for idx in negative_indices:
        rows[idx]["quantity"] = -abs(rows[idx]["quantity"])

    with open(f"{OUTPUT_DIR}/order_items.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"order_items.csv -> {len(rows)} rows ({n_negative_target} negative quantity / returns)")
    return rows


def main():
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generating e-commerce dataset with intentional data quality issues...\n")
    customers = generate_customers()
    products = generate_products()
    orders = generate_orders(customers)
    order_items = generate_order_items(orders, products)
    print("\nAll 4 CSV files generated successfully in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
