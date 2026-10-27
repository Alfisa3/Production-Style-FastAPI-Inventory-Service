# FastAPI Inventory Service

A REST API for managing products and orders using Python, FastAPI, Pydantic, and SQLite.

## Features

- Create products
- View products
- Update products
- Delete products
- Search and filter products
- Pagination
- Create and view orders
- Automatically update inventory when orders are created
- Validate product prices and quantities
- Prevent orders when stock is insufficient
- Prevent duplicate order requests from deducting stock twice
- Automated testing with pytest

## Technologies Used

- Python 3.14
- FastAPI
- Pydantic
- SQLite
- pytest
- Ruff
- uv

## Installation

Install the project dependencies:

```bash
uv sync
```

## Run the Application

```bash
uv run uvicorn inventory_service.main:app --app-dir src --reload
```

## API Documentation

After starting the application, open:

http://127.0.0.1:8000/docs

## Run Tests

In PowerShell, run:

```powershell
$env:PYTHONPATH = "src"
uv run pytest -v
```

## Code Quality Check

```bash
uv run ruff check .
```