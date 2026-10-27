
import os
import sqlite3
from pathlib import Path

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "inventory.db"

DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH))
)

def get_connection():
    print("DATABASE LOCATION:", DATABASE_PATH)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL CHECK(price > 0),
            quantity INTEGER NOT NULL CHECK(quantity >= 0)
        )
    """)


    connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            total_price REAL NOT NULL CHECK(total_price > 0),
            status TEXT NOT NULL DEFAULT 'created',
            request_key TEXT UNIQUE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)



    
    # Check whether request_key already exists
    columns = connection.execute(
        "PRAGMA table_info(orders)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    # Add request_key to an existing table if needed
    if "request_key" not in column_names:
        connection.execute(
            "ALTER TABLE orders ADD COLUMN request_key TEXT"
        )

    # Prevent duplicate request keys
    connection.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_request_key
        ON orders(request_key)
    """)


    connection.commit()
    connection.close()


if __name__ == "__main__":
       create_tables()
       print("Products table created successfully!")
       print(f"Database location: {DATABASE_PATH}")