
import uuid

from fastapi.testclient import TestClient

from inventory_service.main import app

client = TestClient(app)


def test_create_product():
    response = client.post(
        "/products",
        json={
            "name": "Test Headphones",
            "category": "electronics",
            "price": 3499,
            "quantity": 25,
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Test Headphones"
    assert response.json()["category"] == "electronics"
    assert response.json()["price"] == 3499
    assert response.json()["quantity"] == 25



def test_create_product_with_invalid_price():
    response = client.post(
        "/products",
        json={
            "name": "Invalid Product",
            "category": "electronics",
            "price": -100,
            "quantity": 10,
        },
    )

    assert response.status_code == 422



 
def test_product_not_found():
    response = client.get("/products/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"



def test_product_pagination():
    response = client.get("/products?page=1&page_size=2")

    assert response.status_code == 200
    assert len(response.json()) <= 2



def test_filter_products_by_category():
    response = client.get("/products?category=electronics")

    assert response.status_code == 200

    for product in response.json():
        assert product["category"] == "electronics"



def test_successful_order():
    # Get the product's inventory before placing the order
    product_before = client.get("/products/1")
    assert product_before.status_code == 200
    quantity_before = product_before.json()["quantity"]

    # Place an order for one item
    response = client.post(
        "/orders",
        json={
            "product_id": 1,
            "quantity": 1,
            "request_key": f"pytest-successful-order-{uuid.uuid4().hex}",
              },
    )

    # Check that the order was created successfully
    assert response.status_code == 200
    order = response.json()
    assert order["product_id"] == 1
    assert order["quantity"] == 1
    assert order["total_price"] > 0
    assert order["status"] == "created"

    # Verify that inventory decreased by one
    product_after = client.get("/products/1")
    quantity_after = product_after.json()["quantity"]
    assert quantity_after == quantity_before - 1


def test_insufficient_inventory():
    # Check inventory before the failed order
    product_before = client.get("/products/1")
    assert product_before.status_code == 200
    quantity_before = product_before.json()["quantity"]

    # Attempt to order more items than are available
    response = client.post(
        "/orders",
        json={
            "product_id": 1,
            "quantity": 100000,
            "request_key": "pytest-insufficient-stock-001",
        },
    )

    # Verify that the order was rejected
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient inventory"

    # Verify that inventory remains unchanged
    product_after = client.get("/products/1")
    quantity_after = product_after.json()["quantity"]
    assert quantity_after == quantity_before

    

def test_duplicate_order():
    order_data = {
        "product_id": 1,
        "quantity": 1,
        "request_key": "pytest-duplicate-order-001",
    }

    first_response = client.post("/orders", json=order_data)
    second_response = client.post("/orders", json=order_data)

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    # Both requests should return the same order
    assert first_response.json()["id"] == second_response.json()["id"]



def test_invalid_request_body():
    response = client.post(
        "/products",
        json={
            "name": "Test Product",
            "category": "electronics",
            "price": 100,
            # quantity is intentionally missing
        },
    )

    assert response.status_code == 422