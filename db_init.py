import sqlite3


DB_NAME = "sample_store.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS customers")
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """)

    customers = [
        (1, "Aisha Khan", "Dublin"),
        (2, "James Murphy", "Cork"),
        (3, "Marzuq Islam", "Dublin"),
        (4, "Emily Walsh", "Galway"),
        (5, "Omar Ali", "Limerick"),
        (6, "Sophie Byrne", "Dublin"),
        (7, "Daniel Kelly", "Waterford"),
        (8, "Fatima Ahmed", "Cork")
    ]

    products = [
        (1, "Laptop", "Electronics", 899.99),
        (2, "Wireless Mouse", "Electronics", 24.99),
        (3, "Office Chair", "Furniture", 149.99),
        (4, "Desk Lamp", "Furniture", 39.99),
        (5, "Notebook", "Stationery", 4.99),
        (6, "Backpack", "Accessories", 49.99),
        (7, "Headphones", "Electronics", 79.99),
        (8, "Standing Desk", "Furniture", 299.99)
    ]

    orders = [
        (1, 1, 1, 1, "2024-01-10", 899.99),
        (2, 1, 2, 2, "2024-01-12", 49.98),
        (3, 2, 3, 1, "2024-02-05", 149.99),
        (4, 3, 1, 1, "2024-02-20", 899.99),
        (5, 3, 7, 1, "2024-02-21", 79.99),
        (6, 4, 5, 10, "2024-03-01", 49.90),
        (7, 5, 6, 2, "2024-03-12", 99.98),
        (8, 6, 8, 1, "2024-04-15", 299.99),
        (9, 6, 4, 3, "2024-04-16", 119.97),
        (10, 7, 2, 1, "2024-05-02", 24.99),
        (11, 8, 7, 2, "2024-05-10", 159.98),
        (12, 3, 8, 1, "2024-05-12", 299.99),
        (13, 1, 6, 1, "2024-05-14", 49.99),
        (14, 5, 5, 5, "2024-06-01", 24.95),
        (15, 2, 1, 1, "2024-06-05", 899.99)
    ]

    cursor.executemany(
        "INSERT INTO customers VALUES (?, ?, ?)",
        customers
    )

    cursor.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?)",
        products
    )

    cursor.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
        orders
    )

    conn.commit()
    conn.close()

    print("Database created successfully: sample_store.db")


if __name__ == "__main__":
    create_database()