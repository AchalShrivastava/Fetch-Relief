from typing import Dict, List, Tuple
from backend.schemas import InventoryItem, Vehicle, ExecutionEvent
from services.inventory_service import InventoryService

class ResourceInventoryAgent:
    name: str = "ResourceInventoryAgent"

    @classmethod
    def initialize_inventory_session(
        cls, 
        raw_inventory: Dict[str, InventoryItem],
        vehicles: List[Vehicle]
    ) -> Tuple[InventoryService, List[ExecutionEvent]]:
        events: List[ExecutionEvent] = []
        inv_service = InventoryService(raw_inventory)

        events.append(ExecutionEvent(
            agent_name=cls.name,
            action="SNAPSHOT_INVENTORY",
            details={
                "resource_types": list(raw_inventory.keys()),
                "total_units": sum(item.available_quantity for item in raw_inventory.values()),
                "vehicles_available": len(vehicles)
            },
            status="SUCCESS"
        ))
        return inv_service, events
