
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    price: float = Field(gt=0)
    quantity: int = Field(ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, min_length=1)
    price: float | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=0)



class OrderCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    request_key: str = Field(min_length=1)
