from typing import List, Dict, Tuple, Any
from backend.schemas import Vehicle, Allocation, DeliveryTask, AffectedLocation, ExecutionEvent
from services.logistics_service import LogisticsService

class LogisticsAgent:
    name: str = "LogisticsAgent"

    @classmethod
    def dispatch_logistics(
        cls,
        allocations: List[Allocation],
        vehicles: List[Vehicle],
        locations: List[AffectedLocation]
    ) -> Tuple[List[DeliveryTask], List[Vehicle], List[Dict[str, Any]], List[ExecutionEvent]]:
        events: List[ExecutionEvent] = []

        delivery_tasks, updated_vehicles, unassigned = LogisticsService.plan_deliveries(
            allocations=allocations,
            vehicles=vehicles,
            locations=locations
        )

        status = "SUCCESS" if len(unassigned) == 0 else "WARNING"

        events.append(ExecutionEvent(
            agent_name=cls.name,
            action="DISPATCH_LOGISTICS_PLAN",
            details={
                "scheduled_tasks_count": len(delivery_tasks),
                "vehicles_deployed": sum(1 for v in updated_vehicles if v.remaining_capacity < v.capacity_units),
                "unassigned_deliveries_count": len(unassigned)
            },
            status=status
        ))

        return delivery_tasks, updated_vehicles, unassigned, events
