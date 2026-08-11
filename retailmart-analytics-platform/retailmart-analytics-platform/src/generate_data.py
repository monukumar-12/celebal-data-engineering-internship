"""
RetailMart - Synthetic Raw Data Generator
==========================================
Generates messy, realistic CSV files that simulate RetailMart's scattered
raw data sources: customers, products, orders, order_items, payments.

Intentional "real-world mess" baked in on purpose, so the Silver-layer
cleaning step in src/silver/clean_silver.py has real work to do:
  - duplicate customer rows
  - missing emails / phone numbers
  - inconsistent status casing ("Delivered", "delivered", "DELIVERED")
  - a few negative / null quantities and prices
  - orders with delivery dates before order dates (data entry errors)
  - a product price change history (for SCD2 demo)

Run:
    python src/generate_data.py
Output:
    data/raw/customers.csv
    data/raw/products.csv
    data/raw/orders.csv
    data/raw/order_items.csv
    data/raw/payments.csv
    data/raw/products_v2.csv   (a later snapshot of the product catalog,
                                 used to demonstrate SCD2 change capture)
"""

import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

FIRST_NAMES = ["Aarav", "Diya", "Rohan", "Isha", "Kabir", "Meera", "Arjun", "Sara",
               "Vihaan", "Anaya", "Karan", "Priya", "Dev", "Tara", "Nikhil", "Riya",
               "Aditya", "Sneha", "Rahul", "Pooja"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Iyer", "Gupta", "Nair", "Reddy", "Singh",
              "Mehta", "Das", "Kapoor", "Rao", "Chatterjee", "Joshi", "Malhotra"]
CITIES = ["Bhubaneswar", "Bengaluru", "Mumbai", "Delhi", "Pune", "Hyderabad",
          "Chennai", "Kolkata", "Jaipur", "Ahmedabad"]
CATEGORIES = ["Electronics", "Fashion", "Home & Kitchen", "Beauty", "Sports",
              "Books", "Grocery", "Toys"]
PRODUCT_ADJ = ["Pro", "Max", "Lite", "Plus", "Mini", "Ultra", "Classic", "Smart"]
PRODUCT_NOUN = {
    "Electronics": ["Earbuds", "Smartwatch", "Bluetooth Speaker", "Power Bank", "Laptop Stand"],
    "Fashion": ["T-Shirt", "Sneakers", "Denim Jacket", "Handbag", "Sunglasses"],
    "Home & Kitchen": ["Blender", "Cookware Set", "Air Fryer", "Bed Sheet Set", "Table Lamp"],
    "Beauty": ["Face Serum", "Lipstick", "Shampoo", "Perfume", "Sunscreen"],
    "Sports": ["Yoga Mat", "Dumbbell Set", "Running Shoes", "Cricket Bat", "Cycling Helmet"],
    "Books": ["Novel", "Cookbook", "Notebook Set", "Planner", "Comic Bundle"],
    "Grocery": ["Green Tea Pack", "Almonds 500g", "Olive Oil 1L", "Cereal Box", "Coffee Beans"],
    "Toys": ["Building Blocks", "RC Car", "Puzzle Set", "Action Figure", "Board Game"],
}
ORDER_STATUSES_CLEAN = ["Placed", "Shipped", "Delivered", "Cancelled", "Returned"]
PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "COD", "Wallet"]
PAYMENT_STATUSES = ["Success", "Failed", "Pending", "Refunded"]

N_CUSTOMERS = 400
N_PRODUCTS = 120
N_ORDERS = 3000

start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)


def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days),
                              seconds=random.randint(0, 86399))


# ---------------------------------------------------------------------------
# 1. CUSTOMERS  (with intentional duplicates + missing contact info)
# ---------------------------------------------------------------------------
customers = []
for cid in range(1, N_CUSTOMERS + 1):
    fname = random.choice(FIRST_NAMES)
    lname = random.choice(LAST_NAMES)
    signup = random_date(start_date, end_date)
    email = f"{fname.lower()}.{lname.lower()}{cid}@example.com"
    if random.random() < 0.05:  # 5% missing email
        email = ""
    phone = f"9{random.randint(100000000, 999999999)}"
    if random.random() < 0.08:  # 8% missing phone
        phone = ""
    city = random.choice(CITIES)
    customers.append({
        "customer_id": f"C{cid:05d}",
        "first_name": fname,
        "last_name": lname,
        "email": email,
        "phone": phone,
        "city": city,
        "signup_date": signup.strftime("%Y-%m-%d"),
    })

# inject duplicate rows (same customer appears twice - common CSV export bug)
dupes = random.sample(customers, 15)
customers.extend(dupes)
random.shuffle(customers)

with open(os.path.join(RAW_DIR, "customers.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=customers[0].keys())
    writer.writeheader()
    writer.writerows(customers)

# ---------------------------------------------------------------------------
# 2. PRODUCTS (v1 snapshot - used as the initial catalog load)
# ---------------------------------------------------------------------------
products = []
for pid in range(1, N_PRODUCTS + 1):
    cat = random.choice(CATEGORIES)
    noun = random.choice(PRODUCT_NOUN[cat])
    adj = random.choice(PRODUCT_ADJ)
    price = round(random.uniform(199, 15999), 2)
    products.append({
        "product_id": f"P{pid:05d}",
        "product_name": f"{adj} {noun}",
        "category": cat,
        "price": price,
        "active": "Y",
    })

with open(os.path.join(RAW_DIR, "products.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=products[0].keys())
    writer.writeheader()
    writer.writerows(products)

# ---------------------------------------------------------------------------
# 2b. PRODUCTS v2 snapshot (a later extract with price changes + a couple of
#     new / discontinued products) --> used to demo Delta Lake SCD2
# ---------------------------------------------------------------------------
products_v2 = []
changed_ids = random.sample(range(1, N_PRODUCTS + 1), 25)
for p in products:
    p2 = dict(p)
    pid_num = int(p["product_id"][1:])
    if pid_num in changed_ids:
        # price change event
        change_pct = random.uniform(-0.15, 0.25)
        p2["price"] = round(float(p["price"]) * (1 + change_pct), 2)
    products_v2.append(p2)

# discontinue a few products
for pid_num in random.sample(range(1, N_PRODUCTS + 1), 5):
    for p2 in products_v2:
        if p2["product_id"] == f"P{pid_num:05d}":
            p2["active"] = "N"

# add a few brand new products
for pid in range(N_PRODUCTS + 1, N_PRODUCTS + 8):
    cat = random.choice(CATEGORIES)
    noun = random.choice(PRODUCT_NOUN[cat])
    adj = random.choice(PRODUCT_ADJ)
    products_v2.append({
        "product_id": f"P{pid:05d}",
        "product_name": f"{adj} {noun}",
        "category": cat,
        "price": round(random.uniform(199, 15999), 2),
        "active": "Y",
    })

with open(os.path.join(RAW_DIR, "products_v2.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=products_v2[0].keys())
    writer.writeheader()
    writer.writerows(products_v2)

# ---------------------------------------------------------------------------
# 3. ORDERS  (+ ORDER_ITEMS) with messy statuses & bad delivery dates
# ---------------------------------------------------------------------------
orders = []
order_items = []
item_id_counter = 1
customer_ids = list({c["customer_id"] for c in customers})
product_ids = [p["product_id"] for p in products]
product_price = {p["product_id"]: float(p["price"]) for p in products}

for oid in range(1, N_ORDERS + 1):
    cust = random.choice(customer_ids)
    order_date = random_date(start_date, end_date)
    status_clean = random.choices(
        ORDER_STATUSES_CLEAN, weights=[10, 15, 55, 12, 8], k=1
    )[0]
    # inject messy casing ~20% of the time
    if random.random() < 0.2:
        status = random.choice([status_clean.upper(), status_clean.lower()])
    else:
        status = status_clean

    delivery_date = ""
    if status_clean in ("Delivered", "Returned"):
        delivery_date = (order_date + timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d")
        # inject a data-entry error: delivery before order, ~2% of the time
        if random.random() < 0.02:
            delivery_date = (order_date - timedelta(days=random.randint(1, 3))).strftime("%Y-%m-%d")

    orders.append({
        "order_id": f"O{oid:06d}",
        "customer_id": cust,
        "order_date": order_date.strftime("%Y-%m-%d"),
        "status": status,
        "delivery_date": delivery_date,
    })

    n_items = random.randint(1, 4)
    chosen_products = random.sample(product_ids, n_items)
    for prod in chosen_products:
        qty = random.randint(1, 5)
        if random.random() < 0.01:  # bad data: negative quantity
            qty = -qty
        unit_price = product_price[prod]
        order_items.append({
            "order_item_id": f"OI{item_id_counter:07d}",
            "order_id": f"O{oid:06d}",
            "product_id": prod,
            "quantity": qty,
            "unit_price": unit_price,
        })
        item_id_counter += 1

with open(os.path.join(RAW_DIR, "orders.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=orders[0].keys())
    writer.writeheader()
    writer.writerows(orders)

with open(os.path.join(RAW_DIR, "order_items.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=order_items[0].keys())
    writer.writeheader()
    writer.writerows(order_items)

# ---------------------------------------------------------------------------
# 4. PAYMENTS
# ---------------------------------------------------------------------------
payments = []
pay_id = 1
for o in orders:
    if random.random() < 0.03:
        continue  # 3% of orders have no payment record at all (data gap)
    order_total = sum(
        float(oi["unit_price"]) * max(oi["quantity"], 0)
        for oi in order_items if oi["order_id"] == o["order_id"]
    )
    method = random.choice(PAYMENT_METHODS)
    pstatus = random.choices(PAYMENT_STATUSES, weights=[80, 8, 5, 7], k=1)[0]
    payments.append({
        "payment_id": f"PM{pay_id:06d}",
        "order_id": o["order_id"],
        "amount": round(order_total, 2),
        "method": method,
        "payment_status": pstatus,
        "payment_date": o["order_date"],
    })
    pay_id += 1

with open(os.path.join(RAW_DIR, "payments.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=payments[0].keys())
    writer.writeheader()
    writer.writerows(payments)

print("Raw data generated in:", RAW_DIR)
print(f"  customers.csv     : {len(customers)} rows (incl. {len(dupes)} intentional dupes)")
print(f"  products.csv      : {len(products)} rows")
print(f"  products_v2.csv   : {len(products_v2)} rows (later snapshot, for SCD2 demo)")
print(f"  orders.csv        : {len(orders)} rows")
print(f"  order_items.csv   : {len(order_items)} rows")
print(f"  payments.csv      : {len(payments)} rows")
