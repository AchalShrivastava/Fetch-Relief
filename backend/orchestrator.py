import uuid
import traceback
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from backend.schemas import (
    Scenario, SimulationReport, WorkflowState, ExecutionEvent,
    ReliefRequest, InventoryItem, Vehicle, AffectedLocation
)
from services.storage_service import storage_service
from agents.situation_agent import SituationAssessmentAgent
from agents.inventory_agent import ResourceInventoryAgent
from agents.priority_agent import NeedsAndPriorityAgent
from agents.allocation_agent import AllocationAgent
from agents.logistics_agent import LogisticsAgent
from agents.verification_agent import VerificationAgent

class CommandOrchestrator:
    name: str = "CommandOrchestrator"

    @classmethod
    async def run_simulation(
        cls,
        scenario: Optional[Scenario] = None,
        scenario_id: Optional[str] = None,
        custom_requests: Optional[List[ReliefRequest]] = None,
        custom_inventory: Optional[Dict[str, InventoryItem]] = None,
        custom_vehicles: Optional[List[Vehicle]] = None
    ) -> SimulationReport:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        state = WorkflowState.RECEIVED
        execution_trace: List[ExecutionEvent] = []
        participating_agents = [
            cls.name,
            SituationAssessmentAgent.name,
            ResourceInventoryAgent.name,
            NeedsAndPriorityAgent.name,
            AllocationAgent.name,
            LogisticsAgent.name,
            VerificationAgent.name
        ]

        execution_trace.append(ExecutionEvent(
            agent_name=cls.name,
            action="WORKFLOW_INITIALIZED",
            details={"run_id": run_id, "state": state.value},
            status="SUCCESS"
        ))

        # 1. Resolve Scenario
        state = WorkflowState.VALIDATING
        if not scenario:
            scenario = storage_service.get_scenario(scenario_id)
            if not scenario:
                scenario = storage_service.reset_to_demo()

        active_scenario_id = scenario.scenario_id
        active_scenario_name = scenario.name

        # Deep copy inputs to protect original scenario
        requests = custom_requests if custom_requests is not None else [r.model_copy(deep=True) for r in scenario.requests]
        raw_inventory = custom_inventory if custom_inventory is not None else {k: v.model_copy(deep=True) for k, v in scenario.inventory.items()}
        vehicles = custom_vehicles if custom_vehicles is not None else [v.model_copy(deep=True) for v in scenario.vehicles]
        locations = [loc.model_copy(deep=True) for loc in scenario.incident.locations]

        try:
            # 2. Situation Assessment
            state = WorkflowState.ASSESSING
            assessed_requests, sit_events, warnings = SituationAssessmentAgent.assess_scenario(
                locations=locations,
                requests=requests
            )
            execution_trace.extend(sit_events)

            # 3. Inventory Session Initialization
            inv_service, inv_events = ResourceInventoryAgent.initialize_inventory_session(
                raw_inventory=raw_inventory,
                vehicles=vehicles
            )
            execution_trace.extend(inv_events)

            # 4. Needs & Priority Evaluation
            active_requests, quarantined_duplicates, prio_events = NeedsAndPriorityAgent.evaluate_priorities(
                requests=assessed_requests
            )
            execution_trace.extend(prio_events)

            # 5. Deterministic Resource Allocation
            state = WorkflowState.ALLOCATING
            allocations, total_allocated, total_shortages, alloc_events = AllocationAgent.execute_allocation(
                requests=active_requests,
                inventory_service=inv_service
            )
            execution_trace.extend(alloc_events)

            # 6. Logistics & Transport Planning
            state = WorkflowState.PLANNING
            delivery_tasks, updated_vehicles, unassigned, log_events = LogisticsAgent.dispatch_logistics(
                allocations=allocations,
                vehicles=vehicles,
                locations=locations
            )
            execution_trace.extend(log_events)

            # 7. Independent Verification and Reporting
            state = WorkflowState.VERIFYING
            report = VerificationAgent.audit_and_generate_report(
                run_id=run_id,
                scenario_id=active_scenario_id,
                scenario_name=active_scenario_name,
                initial_inventory=raw_inventory,
                requests=requests,
                allocations=allocations,
                delivery_tasks=delivery_tasks,
                unassigned_deliveries=unassigned,
                execution_trace=execution_trace,
                participating_agents=participating_agents
            )

            # Save completed run to persistent store
            storage_service.save_run(report)

            execution_trace.append(ExecutionEvent(
                agent_name=cls.name,
                action="WORKFLOW_COMPLETED",
                details={
                    "run_id": run_id,
                    "state": report.workflow_state.value,
                    "verification_passed": report.verification_passed
                },
                status="SUCCESS"
            ))

            return report

        except Exception as e:
            # Error Recovery: Preserve partial trace and return graceful failure
            err_msg = str(e)
            stack = traceback.format_exc()
            execution_trace.append(ExecutionEvent(
                agent_name=cls.name,
                action="WORKFLOW_EXCEPTION_RECOVERED",
                details={"error": err_msg, "traceback": stack, "failed_state": state.value},
                status="ERROR"
            ))

            fallback_report = SimulationReport(
                run_id=run_id,
                scenario_id=active_scenario_id,
                scenario_name=active_scenario_name,
                workflow_state=WorkflowState.PARTIAL,
                total_requests_received=len(requests),
                total_unique_requests=len(requests),
                execution_trace=execution_trace,
                participating_agents=participating_agents,
                human_readable_summary=f"### Workflow Warning: Partial Execution\nEncountered error in state `{state.value}`: {err_msg}",
                verification_passed=False
            )
            storage_service.save_run(fallback_report)
            return fallback_report
