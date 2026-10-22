import pytest
from backend.orchestrator import CommandOrchestrator
from data.seed_demo_data import get_demo_scenario
from backend.schemas import WorkflowState, ReliefRequest, UrgencyLevel
from services.intent_service import IntentParserService

@pytest.mark.asyncio
async def test_orchestrator_normal_simulation():
    scenario = get_demo_scenario()
    report = await CommandOrchestrator.run_simulation(scenario=scenario)

    assert report.workflow_state == WorkflowState.COMPLETED
    assert report.verification_passed is True
    assert len(report.allocations) > 0
    assert len(report.delivery_tasks) > 0
    assert len(report.execution_trace) >= 6
    assert report.duplicate_requests_flagged >= 1
    # Shortages should be detected for water and generator as designed
    assert len(report.total_shortages) > 0
    assert "water_unit" in report.total_shortages or "generator" in report.total_shortages

@pytest.mark.asyncio
async def test_orchestrator_duplicate_suppression():
    scenario = get_demo_scenario()
    report = await CommandOrchestrator.run_simulation(scenario=scenario)

    # Demo scenario contains req-107-dup which is identical to req-105
    dup_allocations = [a for a in report.allocations if a.request_id == "req-107-dup"]
    assert len(dup_allocations) == 0  # Must NOT be fulfilled
    assert report.duplicate_requests_flagged >= 1

@pytest.mark.asyncio
async def test_orchestrator_incomplete_request_warning():
    scenario = get_demo_scenario()
    report = await CommandOrchestrator.run_simulation(scenario=scenario)

    # Find situation assessment events
    sit_events = [e for e in report.execution_trace if e.agent_name == "SituationAssessmentAgent" and e.action == "FLAG_LOW_CONFIDENCE"]
    assert len(sit_events) >= 1
    assert "req-109-unverified" in str(sit_events[0].details)

@pytest.mark.asyncio
async def test_orchestrator_error_recovery_on_specialist_failure(monkeypatch):
    scenario = get_demo_scenario()

    # Artificially inject an error into LogisticsAgent
    from agents.logistics_agent import LogisticsAgent
    def mock_fail(*args, **kwargs):
        raise RuntimeError("Simulated vehicle telemetry network failure")

    monkeypatch.setattr(LogisticsAgent, "dispatch_logistics", mock_fail)

    report = await CommandOrchestrator.run_simulation(scenario=scenario)

    # Must preserve completed allocations, record error event, and not crash
    assert report.workflow_state == WorkflowState.PARTIAL
    assert report.verification_passed is False
    recovery_event = next(e for e in report.execution_trace if e.action == "WORKFLOW_EXCEPTION_RECOVERED")
    assert "Simulated vehicle telemetry network failure" in recovery_event.details["error"]

@pytest.mark.asyncio
async def test_offline_intent_parser_fallback():
    prompt = "Simulate flood operations in River Zone and North Zone. We have 450 food kits and 200 water units."
    parsed, provider = await IntentParserService.parse_prompt(prompt)

    assert "Local Deterministic NLP Parser" in provider
    assert parsed["action"] == "simulate"
    assert "River Zone" in parsed["target_zones"]
    assert "North Zone" in parsed["target_zones"]
    assert parsed["inventory_overrides"].get("food_kit") == 450
    assert parsed["inventory_overrides"].get("water_unit") == 200
