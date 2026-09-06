"""FastAPI entrypoint for the mixed polyglot project."""

from fastapi import FastAPI, HTTPException

try:
    from .models import Item, ItemCreate
except ImportError:
    from models import Item, ItemCreate

app = FastAPI(title="Polyglot Inventory API", version="0.1.0")

_ITEMS: list[dict] = [
    {"id": 1, "name": "Mechanical Keyboard", "price": 129.99, "in_stock": True},
    {"id": 2, "name": "Wireless Mouse", "price": 49.99, "in_stock": True},
    {"id": 3, "name": "USB-C Monitor Hub", "price": 89.99, "in_stock": False},
]


@app.get("/api/items", response_model=list[Item], tags=["items"])
def list_items() -> list[Item]:
    """Retrieve all inventory items."""
    return [Item(**item) for item in _ITEMS]


@app.get("/api/items/{item_id}", response_model=Item, tags=["items"])
def get_item(item_id: int) -> Item:
    """Retrieve a single inventory item by ID."""
    for item in _ITEMS:
        if item["id"] == item_id:
            return Item(**item)
    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/api/items", response_model=Item, status_code=201, tags=["items"])
def create_item(payload: ItemCreate) -> Item:
    """Create a new inventory item."""
    new_id = len(_ITEMS) + 1
    new_item = {"id": new_id, **payload.model_dump()}
    _ITEMS.append(new_item)
    return Item(**new_item)
