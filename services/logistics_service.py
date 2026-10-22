from typing import List, Dict, Tuple, Any
from backend.schemas import Vehicle, Allocation, DeliveryTask, AffectedLocation

class LogisticsService:
    @staticmethod
    def plan_deliveries(
        allocations: List[Allocation],
        vehicles: List[Vehicle],
        locations: List[AffectedLocation]
    ) -> Tuple[List[DeliveryTask], List[Vehicle], List[Dict[str, Any]]]:
        """
        Plans simulated delivery tasks matching allocated supplies to available vehicles.
        Respects:
        - Vehicle cargo capacity.
        - Destination accessibility (terrain vs vehicle type).
        - Explicit transit time estimations based on synthetic speed and distance assumptions.
        Returns:
        - tasks: List[DeliveryTask]
        - updated_vehicles: List[Vehicle]
        - unassigned: List[Dict[str, Any]]
        """
        loc_map = {loc.location_id: loc for loc in locations}
        # Deep copy vehicles to track remaining capacity during planning
        avail_vehicles = [v.model_copy(deep=True) for v in vehicles if v.status == "IDLE"]
        
        # Group allocations with allocated_quantity > 0 by destination
        dest_allocations: Dict[str, List[Allocation]] = {}
        for a in allocations:
            if a.allocated_quantity > 0:
                dest_allocations.setdefault(a.location_id, []).append(a)

        delivery_tasks: List[DeliveryTask] = []
        unassigned_items: List[Dict[str, Any]] = []

        sequence_counter = 1

        for loc_id, alloc_list in dest_allocations.items():
            loc = loc_map.get(loc_id)
            loc_name = loc.name if loc else loc_id
            accessibility = loc.accessibility_status if loc else "accessible"
            distance_km = loc.distance_km_from_hub if loc else 10.0

            # Items to be delivered to this location
            items_to_deliver: Dict[str, int] = {}
            for a in alloc_list:
                items_to_deliver[a.resource_type] = items_to_deliver.get(a.resource_type, 0) + a.allocated_quantity

            # Allocate across available vehicles
            for res_type, total_units in list(items_to_deliver.items()):
                remaining_units = total_units

                while remaining_units > 0:
                    # Find best vehicle: matches accessibility and has highest remaining capacity
                    eligible_vehicles = [
                        v for v in avail_vehicles 
                        if accessibility in v.accessible_terrains and v.remaining_capacity > 0
                    ]

                    if not eligible_vehicles:
                        unassigned_items.append({
                            "location_id": loc_id,
                            "location_name": loc_name,
                            "resource_type": res_type,
                            "unassigned_units": remaining_units,
                            "reason": f"Fleet capacity exhausted or no vehicle suited for terrain '{accessibility}'"
                        })
                        break

                    # Choose the vehicle that can take the most units
                    eligible_vehicles.sort(key=lambda v: v.remaining_capacity, reverse=True)
                    chosen_vehicle = eligible_vehicles[0]

                    loadable = min(remaining_units, chosen_vehicle.remaining_capacity)
                    chosen_vehicle.remaining_capacity -= loadable
                    remaining_units -= loadable

                    # Compute travel time: (distance / speed * 60) + 15 min loading assumption
                    travel_time = int((distance_km / chosen_vehicle.speed_kmh) * 60) + 15

                    task = DeliveryTask(
                        vehicle_id=chosen_vehicle.vehicle_id,
                        vehicle_name=chosen_vehicle.name,
                        destination_location_id=loc_id,
                        destination_name=loc_name,
                        items_loaded={res_type: loadable},
                        total_units_loaded=loadable,
                        capacity_percentage=round(((chosen_vehicle.capacity_units - chosen_vehicle.remaining_capacity) / chosen_vehicle.capacity_units) * 100, 1),
                        estimated_travel_time_min=travel_time,
                        delivery_sequence=sequence_counter,
                        assumptions=[
                            f"Assumed transit route: Hub -> {loc_name} ({distance_km:.1f} km at synthetic avg {chosen_vehicle.speed_kmh:.0f} km/h).",
                            "15-minute standard cargo loading & safety verification delay applied.",
                            "Simulation only: Road clearance and flood water depth unverified."
                        ],
                        status="SCHEDULED"
                    )
                    delivery_tasks.append(task)
                    sequence_counter += 1

                    if chosen_vehicle.remaining_capacity == 0:
                        chosen_vehicle.status = "ASSIGNED"

        return delivery_tasks, avail_vehicles, unassigned_items
