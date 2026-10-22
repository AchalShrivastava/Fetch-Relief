import json
import os
from typing import Dict, Optional, List
from backend.schemas import Scenario, SimulationReport, InventoryItem
from data.seed_demo_data import get_demo_scenario

class StorageService:
    def __init__(self, db_path: str = "data/local_store.json"):
        self.db_path = db_path
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            self.reset_to_demo()

    def reset_to_demo(self) -> Scenario:
        demo = get_demo_scenario()
        data = {
            "scenarios": {demo.scenario_id: demo.model_dump(mode="json")},
            "runs": {},
            "active_scenario_id": demo.scenario_id
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return demo

    def _load_data(self) -> dict:
        if not os.path.exists(self.db_path):
            self.reset_to_demo()
        with open(self.db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_data(self, data: dict):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def get_scenario(self, scenario_id: Optional[str] = None) -> Optional[Scenario]:
        data = self._load_data()
        scenarios = data.get("scenarios", {})
        if not scenario_id:
            scenario_id = data.get("active_scenario_id")
        if scenario_id in scenarios:
            return Scenario.model_validate(scenarios[scenario_id])
        return None

    def save_scenario(self, scenario: Scenario):
        data = self._load_data()
        data.setdefault("scenarios", {})[scenario.scenario_id] = scenario.model_dump(mode="json")
        data["active_scenario_id"] = scenario.scenario_id
        self._save_data(data)

    def save_run(self, report: SimulationReport):
        data = self._load_data()
        data.setdefault("runs", {})[report.run_id] = report.model_dump(mode="json")
        self._save_data(data)

    def get_run(self, run_id: str) -> Optional[SimulationReport]:
        data = self._load_data()
        run_data = data.get("runs", {}).get(run_id)
        if run_data:
            return SimulationReport.model_validate(run_data)
        return None

    def list_runs(self) -> List[SimulationReport]:
        data = self._load_data()
        return [SimulationReport.model_validate(r) for r in data.get("runs", {}).values()]

    def get_current_inventory(self, scenario_id: Optional[str] = None) -> Dict[str, InventoryItem]:
        scen = self.get_scenario(scenario_id)
        if scen:
            return scen.inventory
        return {}

storage_service = StorageService()
