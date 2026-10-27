
import logging

from fastapi import FastAPI, HTTPException

from inventory_service.database import create_tables, get_connection
from inventory_service.schemas import OrderCreate, ProductCreate, ProductUpdate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI()
create_tables()

products = []


@app.get("/")
def home():
    return {"message": "Welcome to the Inventory Service!"}


@app.post("/products")
def create_product(product: ProductCreate):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO products (name, category, price, quantity)
        VALUES (?, ?, ?, ?)
        """,
        (product.name, product.category, product.price, product.quantity),
    )

    connection.commit()

    logger.info("Product created successfully: ID %s", cursor.lastrowid)

    new_product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()

    connection.close()

    return dict(new_product)

@app.get("/products")
def get_products(
    search: str | None = None,
    category: str | None = None,
    page: int = 1,
    page_size: int = 10
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be at least 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100"
        )

    connection = get_connection()

    query = "SELECT * FROM products WHERE 1=1"
    parameters = []

    if search:
        query += " AND name LIKE ?"
        parameters.append(f"%{search}%")

    if category:
        query += " AND category = ?"
        parameters.append(category)

    query += " ORDER BY id LIMIT ? OFFSET ?"
    parameters.extend([page_size, (page - 1) * page_size])

    rows = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


@app.get("/products/{product_id}")
def get_product(product_id: int):
    connection = get_connection()

    product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()

    connection.close()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return dict(product)



@app.patch("/products/{product_id}")
def update_product(product_id: int, product_update: ProductUpdate):
    update_data = product_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    connection = get_connection()

    try:
        product = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        fields = ", ".join(f"{key} = ?" for key in update_data)
        values = list(update_data.values())
        values.append(product_id)

        connection.execute(
            f"UPDATE products SET {fields} WHERE id = ?",
            values
        )

        connection.commit()

        updated_product = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        return dict(updated_product)

    finally:
        connection.close()



@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    connection = get_connection()

    cursor = connection.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    if cursor.rowcount == 0:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    remaining_products = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if remaining_products == 0:
        connection.execute(
            "DELETE FROM sqlite_sequence WHERE name = 'products'"
        )

    connection.commit()
    connection.close()

    return {"message": "Product deleted successfully"}



@app.post("/orders")
def create_order(order: OrderCreate):
    connection = get_connection()

    try:
        # Start a database transaction
        connection.execute("BEGIN")

        # Check whether this request has already created an order
        existing_order = connection.execute(
            "SELECT * FROM orders WHERE request_key = ?",
            (order.request_key,)
        ).fetchone()

        if existing_order is not None:
            return dict(existing_order)

        # Find the requested product
        product = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (order.product_id,)
        ).fetchone()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        # Check available inventory
        if product["quantity"] < order.quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient inventory"
            )

        # Calculate the total order price
        total_price = product["price"] * order.quantity

        # Reduce inventory
        connection.execute(
            """
            UPDATE products
            SET quantity = quantity - ?
            WHERE id = ?
            """,
            (order.quantity, order.product_id)
        )

        # Save the order and its unique request key
        cursor = connection.execute(
            """
            INSERT INTO orders
                (product_id, quantity, total_price, request_key)
            VALUES (?, ?, ?, ?)
            """,
            (
                order.product_id,
                order.quantity,
                total_price,
                order.request_key
            )
        )

        # Save the changes together
        connection.commit()

        logger.info(
    "Order created successfully: ID %s, Product ID %s, Quantity %s",
    cursor.lastrowid,
    order.product_id,
    order.quantity,
)

        # Retrieve the new order
        new_order = connection.execute(
            "SELECT * FROM orders WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()

        return dict(new_order)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()



@app.get("/orders/{order_id}")
def get_order(order_id: int):
    connection = get_connection()

    try:
        order = connection.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        return dict(order)

    finally:
        connection.close()
