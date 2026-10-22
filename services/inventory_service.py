from typing import Dict, Optional, Tuple, List
from backend.schemas import InventoryItem, ExecutionEvent

class InventoryService:
    def __init__(self, initial_inventory: Optional[Dict[str, InventoryItem]] = None):
        self.inventory: Dict[str, InventoryItem] = {}
        if initial_inventory:
            # Deep copy to isolate simulation run
            for k, v in initial_inventory.items():
                self.inventory[k] = v.model_copy(deep=True)
        self.transaction_log: List[dict] = []

    def get_stock(self, resource_type: str) -> int:
        item = self.inventory.get(resource_type)
        return item.available_quantity if item else 0

    def reserve_stock(self, resource_type: str, quantity: int, request_id: str) -> Tuple[int, int, str]:
        """
        Attempts to reserve requested quantity.
        Returns: (allocated_qty, unfulfilled_qty, reason)
        Guarantees:
        - Never allocates negative quantities.
        - Never allocates more than available_quantity.
        - Updates available_quantity and reserved_quantity transactionally.
        """
        if quantity <= 0:
            return 0, 0, "Requested quantity must be positive."

        item = self.inventory.get(resource_type)
        if not item:
            return 0, quantity, f"Resource type '{resource_type}' is not stocked in inventory."

        if item.available_quantity <= 0:
            return 0, quantity, f"Out of stock: 0 units of '{resource_type}' available."

        allocated = min(quantity, item.available_quantity)
        unfulfilled = quantity - allocated

        item.available_quantity -= allocated
        item.reserved_quantity += allocated

        self.transaction_log.append({
            "action": "reserve",
            "request_id": request_id,
            "resource_type": resource_type,
            "requested": quantity,
            "allocated": allocated,
            "unfulfilled": unfulfilled,
            "remaining_available": item.available_quantity
        })

        if unfulfilled > 0:
            reason = f"Partial fulfillment: Allocated {allocated}/{quantity} due to stock constraint ({item.available_quantity} remaining)."
        else:
            reason = f"Full fulfillment: Allocated {allocated}/{quantity} ({item.available_quantity} remaining)."

        return allocated, unfulfilled, reason

    def get_inventory_summary(self) -> Dict[str, dict]:
        return {
            k: {
                "initial": v.total_initial_quantity,
                "available": v.available_quantity,
                "reserved": v.reserved_quantity,
                "unit": v.unit
            }
            for k, v in self.inventory.items()
        }
