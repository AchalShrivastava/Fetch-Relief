import pytest
from backend.schemas import InventoryItem, Allocation, ReliefRequest, Vehicle, DeliveryTask
from services.report_service import VerificationAndReportService

def test_independent_verification_detects_inventory_overcommit():
    initial_inv = {
        "food_kit": InventoryItem(resource_type="food_kit", total_initial_quantity=50, available_quantity=50)
    }
    # Deliberate overcommitment bug injection in allocations
    bogus_allocations = [
        Allocation(
            request_id="r1",
            location_id="loc-1",
            resource_type="food_kit",
            requested_quantity=80,
            allocated_quantity=70,  # 70 > 50!
            unfulfilled_quantity=10,
            priority_rank=1,
            priority_score=90.0,
            priority_explanation="Faulty allocation",
            allocation_event_id="e1"
        )
    ]
    requests = [
        ReliefRequest(request_id="r1", location_id="loc-1", resource_type="food_kit", quantity_requested=80)
    ]
    vehicles = [Vehicle(vehicle_id="v1", name="Truck", capacity_units=200, remaining_capacity=130)]
    tasks = [DeliveryTask(vehicle_id="v1", vehicle_name="Truck", destination_location_id="loc-1", destination_name="Loc 1", total_units_loaded=70)]

    findings = VerificationAndReportService.run_independent_verification(
        initial_inventory=initial_inv,
        allocations=bogus_allocations,
        requests=requests,
        vehicles=vehicles,
        delivery_tasks=tasks
    )

    # Verification must flag the inventory violation
    inv_check = next(f for f in findings if f.check_id == "CHK-INV-CONSERVATION")
    assert not inv_check.passed
    assert "Allocated 70 exceeds inventory 50" in inv_check.details

def test_independent_verification_detects_vehicle_overload():
    initial_inv = {
        "food_kit": InventoryItem(resource_type="food_kit", total_initial_quantity=100, available_quantity=100)
    }
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
            priority_explanation="Valid alloc",
            allocation_event_id="e1"
        )
    ]
    requests = [ReliefRequest(request_id="r1", location_id="loc-1", resource_type="food_kit", quantity_requested=80)]
    # Vehicle capacity is only 50
    vehicles = [Vehicle(vehicle_id="v-small", name="Small Truck", capacity_units=50, remaining_capacity=0)]
    # Task attempted to load 80
    tasks = [DeliveryTask(vehicle_id="v-small", vehicle_name="Small Truck", destination_location_id="loc-1", destination_name="Loc 1", total_units_loaded=80)]

    findings = VerificationAndReportService.run_independent_verification(
        initial_inventory=initial_inv,
        allocations=allocations,
        requests=requests,
        vehicles=vehicles,
        delivery_tasks=tasks
    )

    cap_check = next(f for f in findings if f.check_id == "CHK-VEHICLE-CAPACITY")
    assert not cap_check.passed
    assert "overloaded" in cap_check.details.lower()
