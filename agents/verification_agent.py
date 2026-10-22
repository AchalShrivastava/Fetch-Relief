from typing import List, Dict, Any
from backend.schemas import (
    SimulationReport, Allocation, DeliveryTask, ExecutionEvent,
    InventoryItem, Vehicle, ReliefRequest
)
from services.report_service import VerificationAndReportService

class VerificationAgent:
    name: str = "VerificationAgent"

    @classmethod
    def audit_and_generate_report(
        cls,
        run_id: str,
        scenario_id: str,
        scenario_name: str,
        initial_inventory: Dict[str, InventoryItem],
        requests: List[ReliefRequest],
        allocations: List[Allocation],
        delivery_tasks: List[DeliveryTask],
        unassigned_deliveries: List[Dict[str, Any]],
        execution_trace: List[ExecutionEvent],
        participating_agents: List[str]
    ) -> SimulationReport:
        # Run independent verification
        report = VerificationAndReportService.generate_report(
            run_id=run_id,
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            initial_inventory=initial_inventory,
            requests=requests,
            allocations=allocations,
            delivery_tasks=delivery_tasks,
            unassigned_deliveries=unassigned_deliveries,
            execution_trace=execution_trace,
            participating_agents=participating_agents
        )

        status = "SUCCESS" if report.verification_passed else "ERROR"

        audit_event = ExecutionEvent(
            agent_name=cls.name,
            action="INDEPENDENT_AUDIT_VERIFIED",
            details={
                "verification_passed": report.verification_passed,
                "total_findings": len(report.verification_findings),
                "critical_violations": sum(1 for f in report.verification_findings if not f.passed and f.severity == "CRITICAL")
            },
            status=status
        )
        report.execution_trace.append(audit_event)
        return report
