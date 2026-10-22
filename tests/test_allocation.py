import pytest
from backend.schemas import ReliefRequest, UrgencyLevel, InventoryItem
from services.inventory_service import InventoryService
from services.allocation_service import AllocationEngine

def test_allocation_engine_inventory_conservation():
    # Setup inventory with 100 units
    inv = {
        "water_unit": InventoryItem(
            resource_type="water_unit",
            total_initial_quantity=100,
            available_quantity=100,
            unit="units"
        )
    }
    inv_service = InventoryService(inv)

    # Requests demanding 150 units total
    req1 = ReliefRequest(
        request_id="req-1",
        location_id="loc-river",
        resource_type="water_unit",
        quantity_requested=80,
        urgency=UrgencyLevel.CRITICAL,
        vulnerability_score=4.5
    )
    req2 = ReliefRequest(
        request_id="req-2",
        location_id="loc-north",
        resource_type="water_unit",
        quantity_requested=70,
        urgency=UrgencyLevel.HIGH,
        vulnerability_score=3.0
    )

    allocations, valid_requests, total_alloc, shortages = AllocationEngine.allocate_resources(
        requests=[req1, req2],
        inventory_service=inv_service
    )

    # Assert inventory conservation
    total_allocated_water = total_alloc.get("water_unit", 0)
    assert total_allocated_water <= 100
    assert total_allocated_water == 100
    assert shortages.get("water_unit", 0) == 50

    # Verify priority: req1 should get 80, req2 gets 20 (partial fulfillment)
    assert allocations[0].request_id == "req-1"
    assert allocations[0].allocated_quantity == 80
    assert allocations[0].unfulfilled_quantity == 0

    assert allocations[1].request_id == "req-2"
    assert allocations[1].allocated_quantity == 20
    assert allocations[1].unfulfilled_quantity == 50

def test_allocation_empty_inventory():
    inv = {
        "food_kit": InventoryItem(
            resource_type="food_kit",
            total_initial_quantity=0,
            available_quantity=0,
            unit="packs"
        )
    }
    inv_service = InventoryService(inv)

    req = ReliefRequest(
        request_id="req-empty",
        location_id="loc-market",
        resource_type="food_kit",
        quantity_requested=50,
        urgency=UrgencyLevel.HIGH
    )

    allocations, valid_requests, total_alloc, shortages = AllocationEngine.allocate_resources(
        requests=[req],
        inventory_service=inv_service
    )

    assert total_alloc.get("food_kit", 0) == 0
    assert shortages.get("food_kit", 0) == 50
    assert allocations[0].allocated_quantity == 0
    assert allocations[0].unfulfilled_quantity == 50

def test_allocation_determinism():
    # Identical runs must produce bit-for-bit identical allocation decisions
    for _ in range(5):
        inv = {
            "food_kit": InventoryItem(resource_type="food_kit", total_initial_quantity=100, available_quantity=100)
        }
        inv_service = InventoryService(inv)
        r1 = ReliefRequest(request_id="r1", location_id="l1", resource_type="food_kit", quantity_requested=60, urgency=UrgencyLevel.HIGH, vulnerability_score=3.0)
        r2 = ReliefRequest(request_id="r2", location_id="l2", resource_type="food_kit", quantity_requested=60, urgency=UrgencyLevel.HIGH, vulnerability_score=3.0)
        allocs, _, total_alloc, _ = AllocationEngine.allocate_resources([r1, r2], inv_service)

        # Deterministic tie-breaking on request_id
        assert allocs[0].request_id == "r1"
        assert allocs[0].allocated_quantity == 60
        assert allocs[1].request_id == "r2"
        assert allocs[1].allocated_quantity == 40
