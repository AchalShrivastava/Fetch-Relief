from typing import Dict, List
from backend.schemas import (
    Scenario, Incident, AffectedLocation, ReliefRequest, 
    InventoryItem, Vehicle, UrgencyLevel, ResourceType
)

def get_demo_locations() -> List[AffectedLocation]:
    return [
        AffectedLocation(
            location_id="loc-north",
            name="North Zone (Highland Clinic & Community Center)",
            zone="North Sector",
            population=3200,
            accessibility_status="accessible",
            distance_km_from_hub=8.5,
            estimated_transit_time_min=25,
            is_active=True
        ),
        AffectedLocation(
            location_id="loc-river",
            name="River Zone (Submerged Lowlands & Riverside Shelter)",
            zone="Central River Basin",
            population=4800,
            accessibility_status="partial_flood",
            distance_km_from_hub=14.0,
            estimated_transit_time_min=45,
            is_active=True
        ),
        AffectedLocation(
            location_id="loc-market",
            name="Market Zone (Commercial Plaza Evacuation Depot)",
            zone="East Sector",
            population=2100,
            accessibility_status="accessible",
            distance_km_from_hub=6.0,
            estimated_transit_time_min=18,
            is_active=True
        )
    ]

def get_demo_inventory() -> Dict[str, InventoryItem]:
    return {
        ResourceType.FOOD_KIT.value: InventoryItem(
            resource_type=ResourceType.FOOD_KIT.value,
            total_initial_quantity=500,
            available_quantity=500,
            unit="ration_packs",
            warehouse_location="Central Depot - Bay A"
        ),
        ResourceType.WATER_UNIT.value: InventoryItem(
            resource_type=ResourceType.WATER_UNIT.value,
            total_initial_quantity=300,
            available_quantity=300,
            unit="10L_jugs",
            warehouse_location="Central Depot - Bay B"
        ),
        ResourceType.FIRST_AID_KIT.value: InventoryItem(
            resource_type=ResourceType.FIRST_AID_KIT.value,
            total_initial_quantity=100,
            available_quantity=100,
            unit="trauma_kits",
            warehouse_location="Central Depot - Medical Vault"
        ),
        ResourceType.BLANKET.value: InventoryItem(
            resource_type=ResourceType.BLANKET.value,
            total_initial_quantity=150,
            available_quantity=150,
            unit="thermal_blankets",
            warehouse_location="Central Depot - Bay C"
        ),
        ResourceType.GENERATOR.value: InventoryItem(
            resource_type=ResourceType.GENERATOR.value,
            total_initial_quantity=10,
            available_quantity=10,
            unit="portable_5kw",
            warehouse_location="Central Depot - Heavy Bay"
        )
    }

def get_demo_vehicles() -> List[Vehicle]:
    return [
        Vehicle(
            vehicle_id="veh-01",
            name="Alpha Heavy Hauler",
            vehicle_type="heavy_truck",
            capacity_units=350,
            remaining_capacity=350,
            speed_kmh=45.0,
            status="IDLE",
            accessible_terrains=["accessible"]
        ),
        Vehicle(
            vehicle_id="veh-02",
            name="Bravo Rapid Cargo",
            vehicle_type="light_truck",
            capacity_units=180,
            remaining_capacity=180,
            speed_kmh=55.0,
            status="IDLE",
            accessible_terrains=["accessible", "partial_flood"]
        ),
        Vehicle(
            vehicle_id="veh-03",
            name="Charlie 4x4 High-Clearance",
            vehicle_type="4x4_van",
            capacity_units=120,
            remaining_capacity=120,
            speed_kmh=40.0,
            status="IDLE",
            accessible_terrains=["accessible", "partial_flood"]
        ),
        Vehicle(
            vehicle_id="veh-04",
            name="Delta Flood Rescue Utility",
            vehicle_type="amphibious_cargo",
            capacity_units=80,
            remaining_capacity=80,
            speed_kmh=25.0,
            status="IDLE",
            accessible_terrains=["accessible", "partial_flood", "boat_only"]
        )
    ]

def get_demo_requests() -> List[ReliefRequest]:
    return [
        # Request 1: Critical medical for River Zone (urgent hospital clinic)
        ReliefRequest(
            request_id="req-101",
            location_id="loc-river",
            resource_type=ResourceType.FIRST_AID_KIT.value,
            quantity_requested=60,
            urgency=UrgencyLevel.CRITICAL,
            vulnerability_score=4.8,
            source="Dr. Ellis (River Mobile Clinic)",
            confidence_score=0.95
        ),
        # Request 2: High priority water for River Zone (causes total water request to spike)
        ReliefRequest(
            request_id="req-102",
            location_id="loc-river",
            resource_type=ResourceType.WATER_UNIT.value,
            quantity_requested=250,
            urgency=UrgencyLevel.HIGH,
            vulnerability_score=4.5,
            source="River Zone Community Coordinator",
            confidence_score=0.90
        ),
        # Request 3: Critical emergency generators for North Zone clinic
        ReliefRequest(
            request_id="req-103",
            location_id="loc-north",
            resource_type=ResourceType.GENERATOR.value,
            quantity_requested=6,
            urgency=UrgencyLevel.CRITICAL,
            vulnerability_score=4.2,
            source="North Zone Clinic Engineer",
            confidence_score=0.92
        ),
        # Request 4: High food for North Zone shelter
        ReliefRequest(
            request_id="req-104",
            location_id="loc-north",
            resource_type=ResourceType.FOOD_KIT.value,
            quantity_requested=300,
            urgency=UrgencyLevel.HIGH,
            vulnerability_score=3.5,
            source="Shelter Supervisor North",
            confidence_score=0.88
        ),
        # Request 5: Medium food for Market Zone
        ReliefRequest(
            request_id="req-105",
            location_id="loc-market",
            resource_type=ResourceType.FOOD_KIT.value,
            quantity_requested=200,
            urgency=UrgencyLevel.MEDIUM,
            vulnerability_score=2.8,
            source="Market Zone Volunteer Lead",
            confidence_score=0.85
        ),
        # Request 6: High water for Market Zone (causes overall shortage!)
        # Total water requested: 250 (River) + 150 (Market) = 400 > 300 available.
        ReliefRequest(
            request_id="req-106",
            location_id="loc-market",
            resource_type=ResourceType.WATER_UNIT.value,
            quantity_requested=150,
            urgency=UrgencyLevel.MEDIUM,
            vulnerability_score=3.0,
            source="Market Plaza Shelter",
            confidence_score=0.80
        ),
        # Request 7: DUPLICATE request - Identical to req-105 from a different caller in Market Zone
        ReliefRequest(
            request_id="req-107-dup",
            location_id="loc-market",
            resource_type=ResourceType.FOOD_KIT.value,
            quantity_requested=200,
            urgency=UrgencyLevel.MEDIUM,
            vulnerability_score=2.8,
            source="Secondary Hotline Call (Duplicate)",
            confidence_score=0.60,
            is_duplicate=True,
            duplicate_of_id="req-105"
        ),
        # Request 8: Additional generator request that exceeds inventory
        # Total generator: 6 (req-103) + 8 (req-108) = 14 > 10 available!
        ReliefRequest(
            request_id="req-108",
            location_id="loc-river",
            resource_type=ResourceType.GENERATOR.value,
            quantity_requested=8,
            urgency=UrgencyLevel.MEDIUM,
            vulnerability_score=3.8,
            source="River Water Pump Station",
            confidence_score=0.75
        ),
        # Request 9: Incomplete / low confidence request for blankets
        ReliefRequest(
            request_id="req-109-unverified",
            location_id="loc-north",
            resource_type=ResourceType.BLANKET.value,
            quantity_requested=80,
            urgency=UrgencyLevel.LOW,
            vulnerability_score=1.5,
            source="Unverified Social Media Post",
            confidence_score=0.35
        )
    ]

def get_demo_scenario() -> Scenario:
    locations = get_demo_locations()
    incident = Incident(
        incident_id="inc-flood-2026",
        title="Simulated Flash Flood - Tri-Zone River Inundation",
        description="Fictional disaster response drill for high-water flooding across North, River, and Market sectors.",
        incident_type="flood",
        locations=locations
    )
    return Scenario(
        scenario_id="scenario-flood-tri-zone",
        name="Tri-Zone Flash Flood Coordination Exercise",
        incident=incident,
        requests=get_demo_requests(),
        inventory=get_demo_inventory(),
        vehicles=get_demo_vehicles(),
        is_demo=True
    )
