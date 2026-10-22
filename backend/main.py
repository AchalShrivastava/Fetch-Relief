from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from typing import Dict, Any, List, Optional
from backend.config import settings
from backend.schemas import (
    Scenario, SimulationReport, InventoryItem, 
    NaturalLanguageSimulationRequest
)
from services.storage_service import storage_service
from services.intent_service import IntentParserService
from backend.orchestrator import CommandOrchestrator

app = FastAPI(
    title="ReliefMesh Emergency Coordinator API",
    description="Multi-agent emergency logistics simulation backend powered by Fetch.ai and ASI:One.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static assets
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", include_in_schema=False)
def serve_dashboard():
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html")
    return {"message": "ReliefMesh API Backend Running"}

@app.get("/style.css", include_in_schema=False)
def serve_css():
    return FileResponse("frontend/style.css")

@app.get("/app.js", include_in_schema=False)
def serve_js():
    return FileResponse("frontend/app.js")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ReliefMesh Backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "storage": settings.STORAGE_BACKEND
    }

@app.get("/agents")
def list_agents():
    return {
        "orchestrator": {
            "name": "CommandOrchestrator",
            "role": "Master intent parser and task distributor",
            "status": "ONLINE"
        },
        "specialists": [
            {"name": "SituationAssessmentAgent", "role": "Incident report assessment and confidence auditing", "status": "ACTIVE"},
            {"name": "ResourceInventoryAgent", "role": "Stock tracking, isolation, and anti-double allocation", "status": "ACTIVE"},
            {"name": "NeedsAndPriorityAgent", "role": "Multi-criteria ranking and duplicate suppression", "status": "ACTIVE"},
            {"name": "AllocationAgent", "role": "Deterministic constraint-based supply matching", "status": "ACTIVE"},
            {"name": "LogisticsAgent", "role": "Vehicle capacity matching and transit sequencing", "status": "ACTIVE"},
            {"name": "VerificationAgent", "role": "Independent mathematical verification and audit logging", "status": "ACTIVE"}
        ],
        "uagent_bridge": {
            "name": settings.AGENT_NAME,
            "port": settings.AGENT_PORT,
            "protocol": "Fetch.ai Agent Chat Protocol (ACP v0.3 / 0.4)",
            "asi_one_compatible": True
        }
    }

@app.get("/inventory")
def get_inventory() -> Dict[str, InventoryItem]:
    return storage_service.get_current_inventory()

@app.post("/inventory/reset-demo")
def reset_demo():
    scenario = storage_service.reset_to_demo()
    return {
        "status": "RESET_SUCCESS",
        "active_scenario_id": scenario.scenario_id,
        "name": scenario.name,
        "inventory_count": len(scenario.inventory),
        "requests_count": len(scenario.requests),
        "vehicles_count": len(scenario.vehicles)
    }

@app.get("/scenarios/current")
def get_current_scenario() -> Scenario:
    scen = storage_service.get_scenario()
    if not scen:
        scen = storage_service.reset_to_demo()
    return scen

@app.post("/scenarios")
def create_scenario(scenario: Scenario):
    storage_service.save_scenario(scenario)
    return {"status": "CREATED", "scenario_id": scenario.scenario_id}

@app.post("/scenarios/{scenario_id}/simulate")
async def run_scenario_simulation(scenario_id: str) -> SimulationReport:
    scen = storage_service.get_scenario(scenario_id)
    if not scen:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    report = await CommandOrchestrator.run_simulation(scenario=scen)
    return report

@app.post("/simulate-nl")
async def run_natural_language_simulation(req: NaturalLanguageSimulationRequest) -> Dict[str, Any]:
    parsed, provider = await IntentParserService.parse_prompt(req.user_prompt)

    if parsed.get("action") == "reset":
        storage_service.reset_to_demo()
        return {
            "status": "RESET_SUCCESS",
            "message": "Demo data successfully reset to baseline scenario.",
            "provider": provider
        }

    scen = storage_service.get_scenario(req.scenario_override_id)
    if not scen:
        scen = storage_service.reset_to_demo()

    # Apply inventory overrides if parsed from prompt
    custom_inv = {k: v.model_copy(deep=True) for k, v in scen.inventory.items()}
    overrides = parsed.get("inventory_overrides", {})
    for res_name, qty in overrides.items():
        if res_name in custom_inv:
            custom_inv[res_name].total_initial_quantity = qty
            custom_inv[res_name].available_quantity = qty

    report = await CommandOrchestrator.run_simulation(
        scenario=scen,
        custom_inventory=custom_inv if overrides else None
    )

    return {
        "run_id": report.run_id,
        "intent_parser": provider,
        "extracted_intent": parsed,
        "report": report
    }

@app.get("/runs/{run_id}")
def get_run(run_id: str) -> SimulationReport:
    run = storage_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return run

@app.get("/runs/{run_id}/report")
def get_run_report_markdown(run_id: str):
    run = storage_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return {
        "run_id": run_id,
        "status": run.workflow_state,
        "verification_passed": run.verification_passed,
        "markdown_report": run.human_readable_summary
    }

@app.get("/runs")
def list_runs() -> List[Dict[str, Any]]:
    runs = storage_service.list_runs()
    return [
        {
            "run_id": r.run_id,
            "scenario_name": r.scenario_name,
            "timestamp": r.timestamp,
            "workflow_state": r.workflow_state,
            "verification_passed": r.verification_passed,
            "shortages_count": len(r.total_shortages)
        }
        for r in runs
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=False)
