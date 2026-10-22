import pytest
from backend.schemas import InventoryItem
from services.inventory_service import InventoryService

def test_inventory_non_negative():
    inv = {
        "generator": InventoryItem(
            resource_type="generator",
            total_initial_quantity=5,
            available_quantity=5,
            unit="units"
        )
    }
    service = InventoryService(inv)

    # Reserve 3 units
    alloc, unful, reason = service.reserve_stock("generator", 3, "req-1")
    assert alloc == 3
    assert unful == 0
    assert service.get_stock("generator") == 2

    # Reserve 5 units (only 2 left)
    alloc2, unful2, reason2 = service.reserve_stock("generator", 5, "req-2")
    assert alloc2 == 2
    assert unful2 == 3
    assert service.get_stock("generator") == 0

    # Reserve 1 unit when empty
    alloc3, unful3, reason3 = service.reserve_stock("generator", 1, "req-3")
    assert alloc3 == 0
    assert unful3 == 1
    assert service.get_stock("generator") == 0

def test_inventory_isolation():
    raw_inv = {
        "food_kit": InventoryItem(resource_type="food_kit", total_initial_quantity=100, available_quantity=100)
    }
    # Initializing service creates deep copy and does not mutate raw_inv
    s1 = InventoryService(raw_inv)
    s1.reserve_stock("food_kit", 50, "req-1")

    assert s1.get_stock("food_kit") == 50
    assert raw_inv["food_kit"].available_quantity == 100
