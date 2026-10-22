from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import uuid

class ResourceType(str, Enum):
    FOOD_KIT = "food_kit"
    WATER_UNIT = "water_unit"
    FIRST_AID_KIT = "first_aid_kit"
    BLANKET = "blanket"
    GENERATOR = "generator"
    MEDICINE = "medicine"
    SHELTER_KIT = "shelter_kit"

class UrgencyLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class WorkflowState(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    ASSESSING = "ASSESSING"
    ALLOCATING = "ALLOCATING"
    PLANNING = "PLANNING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"

class AffectedLocation(BaseModel):
    location_id: str
    name: str
    zone: str
    population: int = 1000
    accessibility_status: str = "accessible"  # "accessible", "partial_flood", "boat_only"
    distance_km_from_hub: float = 5.0
    estimated_transit_time_min: int = 20
    is_active: bool = True

class ReliefRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:8]}")
    location_id: str
    resource_type: str
    quantity_requested: int
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    vulnerability_score: float = Field(default=2.5, description="1.0 (lowest) to 5.0 (highest vulnerability)")
    source: str = "Field Observation"
    confidence_score: float = Field(default=0.9, ge=0.0, le=1.0)
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InventoryItem(BaseModel):
    resource_type: str
    total_initial_quantity: int
    available_quantity: int
    reserved_quantity: int = 0
    unit: str = "units"
    warehouse_location: str = "Central Relief Depot"

class Vehicle(BaseModel):
    vehicle_id: str
    name: str
    vehicle_type: str = "cargo_van"  # "heavy_truck", "light_truck", "4x4_van", "boat"
    capacity_units: int
    remaining_capacity: int
    speed_kmh: float = 40.0
    status: str = "IDLE"  # "IDLE", "ASSIGNED", "IN_TRANSIT"
    accessible_terrains: List[str] = ["accessible", "partial_flood"]

class Allocation(BaseModel):
    allocation_id: str = Field(default_factory=lambda: f"alloc-{uuid.uuid4().hex[:8]}")
    request_id: str
    location_id: str
    resource_type: str
    requested_quantity: int
    allocated_quantity: int
    unfulfilled_quantity: int
    priority_rank: int
    priority_score: float
    priority_explanation: str
    allocation_event_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DeliveryTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"deliv-{uuid.uuid4().hex[:8]}")
    vehicle_id: str
    vehicle_name: str
    destination_location_id: str
    destination_name: str
    items_loaded: Dict[str, int] = Field(default_factory=dict)
    total_units_loaded: int = 0
    capacity_percentage: float = 0.0
    estimated_travel_time_min: int = 0
    delivery_sequence: int = 1
    assumptions: List[str] = Field(default_factory=list)
    status: str = "SCHEDULED"

class ExecutionEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_name: str
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    status: str = "SUCCESS"  # SUCCESS, WARNING, ERROR

class VerificationFinding(BaseModel):
    check_id: str
    check_name: str
    passed: bool
    details: str
    severity: str = "INFO"  # INFO, WARNING, CRITICAL

class Incident(BaseModel):
    incident_id: str = Field(default_factory=lambda: f"inc-{uuid.uuid4().hex[:8]}")
    title: str = "Simulated Flash Flood Emergency"
    description: str = "Synthetic emergency scenario"
    incident_type: str = "flood"
    locations: List[AffectedLocation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Scenario(BaseModel):
    scenario_id: str = Field(default_factory=lambda: f"scen-{uuid.uuid4().hex[:8]}")
    name: str = "Standard Regional Flood Response"
    incident: Incident
    requests: List[ReliefRequest] = Field(default_factory=list)
    inventory: Dict[str, InventoryItem] = Field(default_factory=dict)
    vehicles: List[Vehicle] = Field(default_factory=list)
    is_demo: bool = True

class SimulationReport(BaseModel):
    run_id: str
    scenario_id: str
    scenario_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workflow_state: WorkflowState = WorkflowState.COMPLETED
    total_requests_received: int = 0
    total_unique_requests: int = 0
    duplicate_requests_flagged: int = 0
    total_resources_requested: Dict[str, int] = Field(default_factory=dict)
    total_resources_allocated: Dict[str, int] = Field(default_factory=dict)
    total_shortages: Dict[str, int] = Field(default_factory=dict)
    allocations: List[Allocation] = Field(default_factory=list)
    delivery_tasks: List[DeliveryTask] = Field(default_factory=list)
    unassigned_deliveries: List[Dict[str, Any]] = Field(default_factory=list)
    verification_findings: List[VerificationFinding] = Field(default_factory=list)
    verification_passed: bool = True
    execution_trace: List[ExecutionEvent] = Field(default_factory=list)
    participating_agents: List[str] = Field(default_factory=list)
    human_readable_summary: str = ""
    limitations_disclaimer: str = (
        "SIMULATION NOTICE: ReliefMesh is an experimental coordination simulation. "
        "Outputs are strictly synthetic, based on deterministic heuristics and assumed parameters. "
        "Not validated for live disaster dispatch."
    )

class NaturalLanguageSimulationRequest(BaseModel):
    user_prompt: str
    scenario_override_id: Optional[str] = None
    strict_verification: bool = True
