import pytest
from backend.schemas import Vehicle, Allocation, AffectedLocation
from services.logistics_service import LogisticsService

def test_logistics_vehicle_capacity_strictly_respected():
    vehicles = [
        Vehicle(vehicle_id="v1", name="Small Van", capacity_units=50, remaining_capacity=50, accessible_terrains=["accessible"])
    ]
    locations = [
        AffectedLocation(location_id="loc-1", name="North Center", zone="North", accessibility_status="accessible")
    ]
    # Allocation of 80 units
    allocations = [
        Allocation(
            request_id="r1",
            location_id="loc-1",
            resource_type="food_kit",
            requested_quantity=80,
            allocated_quantity=80,
            unfulfilled_quantity=0,
            priority_rank=1,
            priority_score=90.0,
            priority_explanation="Top Priority",
            allocation_event_id="evt-1"
        )
    ]

    tasks, updated_veh, unassigned = LogisticsService.plan_deliveries(
        allocations=allocations,
        vehicles=vehicles,
        locations=locations
    )

    # v1 only has 50 capacity, so task loads at most 50, and 30 remains unassigned
    assert len(tasks) == 1
    assert tasks[0].total_units_loaded <= 50
    assert tasks[0].total_units_loaded == 50
    assert len(unassigned) == 1
    assert unassigned[0]["unassigned_units"] == 30
    assert updated_veh[0].remaining_capacity == 0

def test_logistics_terrain_constraint():
    vehicles = [
        # Road truck cannot traverse partial_flood or boat_only
        Vehicle(vehicle_id="v-road", name="Road Truck", capacity_units=100, remaining_capacity=100, accessible_terrains=["accessible"]),
        # Amphibious boat can
        Vehicle(vehicle_id="v-boat", name="Amphibious Utility", capacity_units=50, remaining_capacity=50, accessible_terrains=["accessible", "partial_flood", "boat_only"])
    ]
    locations = [
        AffectedLocation(location_id="loc-flood", name="Flooded Island", zone="River", accessibility_status="boat_only")
    ]
    allocations = [
        Allocation(
            request_id="r-island",
            location_id="loc-flood",
            resource_type="medicine",
            requested_quantity=40,
            allocated_quantity=40,
            unfulfilled_quantity=0,
            priority_rank=1,
            priority_score=95.0,
            priority_explanation="Emergency Island",
            allocation_event_id="evt-2"
        )
    ]

    tasks, _, unassigned = LogisticsService.plan_deliveries(
        allocations=allocations,
        vehicles=vehicles,
        locations=locations
    )

    assert len(tasks) == 1
    # Only v-boat should have been assigned
    assert tasks[0].vehicle_id == "v-boat"
    assert tasks[0].total_units_loaded == 40
    assert len(unassigned) == 0
