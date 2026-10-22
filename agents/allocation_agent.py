from typing import List, Dict, Tuple
from backend.schemas import ReliefRequest, Allocation, ExecutionEvent
from services.inventory_service import InventoryService
from services.allocation_service import AllocationEngine

class AllocationAgent:
    name: str = "AllocationAgent"

    @classmethod
    def execute_allocation(
        cls,
        requests: List[ReliefRequest],
        inventory_service: InventoryService
    ) -> Tuple[List[Allocation], Dict[str, int], Dict[str, int], List[ExecutionEvent]]:
        events: List[ExecutionEvent] = []

        allocations, valid_requests, total_allocated, total_shortages = AllocationEngine.allocate_resources(
            requests=requests,
            inventory_service=inventory_service
        )

        events.append(ExecutionEvent(
            agent_name=cls.name,
            action="EXECUTE_DETERMINISTIC_ALLOCATION",
            details={
                "total_allocations_made": len(allocations),
                "total_allocated_units": sum(total_allocated.values()),
                "shortages_detected": total_shortages
            },
            status="SUCCESS"
        ))

        return allocations, total_allocated, total_shortages, events
