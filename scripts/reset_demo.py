"""
ReliefMesh Demo Reset Utility
Restores the default synthetic scenario and warehouse inventories.
"""
from services.storage_service import storage_service

if __name__ == "__main__":
    scenario = storage_service.reset_to_demo()
    print(f"ReliefMesh Demo Reset Complete:")
    print(f"Scenario ID: {scenario.scenario_id}")
    print(f"Scenario:    {scenario.name}")
    print(f"Inventory:   {len(scenario.inventory)} resource types")
    print(f"Requests:    {len(scenario.requests)} relief requests (including 1 duplicate and 1 low-confidence)")
    print(f"Vehicles:    {len(scenario.vehicles)} vehicles")
