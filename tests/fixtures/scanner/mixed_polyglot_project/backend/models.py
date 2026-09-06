"""Data models for items in the polyglot project."""

from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    """Base attributes for an inventory item."""

    name: str = Field(..., description="Item name")
    price: float = Field(..., gt=0, description="Item unit price")
    in_stock: bool = Field(default=True, description="Availability flag")


class ItemCreate(ItemBase):
    """Payload used to create an inventory item."""


class Item(ItemBase):
    """Full inventory item representation."""

    id: int = Field(..., description="Unique identifier")
