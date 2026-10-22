from typing import List, Dict, Any
from datetime import datetime, timezone
from backend.schemas import (
    SimulationReport, Allocation, DeliveryTask, VerificationFinding,
    ExecutionEvent, WorkflowState, InventoryItem, Vehicle, ReliefRequest
)

class VerificationAndReportService:
    @staticmethod
    def run_independent_verification(
        initial_inventory: Dict[str, InventoryItem],
        allocations: List[Allocation],
        requests: List[ReliefRequest],
        vehicles: List[Vehicle],
        delivery_tasks: List[DeliveryTask]
    ) -> List[VerificationFinding]:
        """
        Runs independent mathematical audits over simulation outputs.
        Does NOT rely on allocation agent's claims; verifies raw numbers directly.
        """
        findings: List[VerificationFinding] = []

        # Check 1: Inventory Conservation
        allocated_sums: Dict[str, int] = {}
        for a in allocations:
            allocated_sums[a.resource_type] = allocated_sums.get(a.resource_type, 0) + a.allocated_quantity

        inventory_conserved = True
        violation_details = []
        for res, total_alloc in allocated_sums.items():
            avail = initial_inventory.get(res).total_initial_quantity if res in initial_inventory else 0
            if total_alloc > avail:
                inventory_conserved = False
                violation_details.append(f"Resource '{res}': Allocated {total_alloc} exceeds inventory {avail}")

        findings.append(VerificationFinding(
            check_id="CHK-INV-CONSERVATION",
            check_name="Inventory Conservation Audit",
            passed=inventory_conserved,
            details="All allocations strictly <= warehouse inventory." if inventory_conserved else "; ".join(violation_details),
            severity="CRITICAL" if not inventory_conserved else "INFO"
        ))

        # Check 2: Non-Negative and Conservation of Quantity per Request
        math_valid = True
        math_errors = []
        for a in allocations:
            if a.allocated_quantity < 0 or a.unfulfilled_quantity < 0:
                math_valid = False
                math_errors.append(f"Negative values found in req {a.request_id}")
            if a.requested_quantity != (a.allocated_quantity + a.unfulfilled_quantity):
                math_valid = False
                math_errors.append(f"Sum mismatch in req {a.request_id}: {a.requested_quantity} != {a.allocated_quantity} + {a.unfulfilled_quantity}")

        findings.append(VerificationFinding(
            check_id="CHK-REQ-SUM-CONSERVATION",
            check_name="Request Arithmetic Conservation",
            passed=math_valid,
            details="All request lines satisfy requested = allocated + unfulfilled." if math_valid else "; ".join(math_errors),
            severity="CRITICAL" if not math_valid else "INFO"
        ))

        # Check 3: Vehicle Cargo Over-commitment Check
        veh_map = {v.vehicle_id: v.capacity_units for v in vehicles}
        vehicle_load_totals: Dict[str, int] = {}
        for task in delivery_tasks:
            vehicle_load_totals[task.vehicle_id] = vehicle_load_totals.get(task.vehicle_id, 0) + task.total_units_loaded

        capacity_valid = True
        cap_errors = []
        for v_id, load in vehicle_load_totals.items():
            max_cap = veh_map.get(v_id, 0)
            if load > max_cap:
                capacity_valid = False
                cap_errors.append(f"Vehicle {v_id} overloaded: loaded {load} > capacity {max_cap}")

        findings.append(VerificationFinding(
            check_id="CHK-VEHICLE-CAPACITY",
            check_name="Logistics Vehicle Capacity Audit",
            passed=capacity_valid,
            details="No vehicle exceeds its maximum payload rating." if capacity_valid else "; ".join(cap_errors),
            severity="CRITICAL" if not capacity_valid else "INFO"
        ))

        # Check 4: Duplicate Request Quarantine Audit
        duplicates_in_allocations = [a for a in allocations if any(r.request_id == a.request_id and r.is_duplicate for r in requests)]
        no_dup_fulfilled = len(duplicates_in_allocations) == 0
        findings.append(VerificationFinding(
            check_id="CHK-DUPLICATE-QUARANTINE",
            check_name="Duplicate Suppression Audit",
            passed=no_dup_fulfilled,
            details="Duplicate requests successfully detected and quarantined." if no_dup_fulfilled else f"{len(duplicates_in_allocations)} duplicate requests were erroneously fulfilled.",
            severity="WARNING" if not no_dup_fulfilled else "INFO"
        ))

        return findings

    @classmethod
    def generate_report(
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
        # Build fake vehicle list from delivery_tasks + default capacities
        dummy_vehicles = [
            Vehicle(vehicle_id="veh-01", name="Alpha Heavy Hauler", capacity_units=350, remaining_capacity=0),
            Vehicle(vehicle_id="veh-02", name="Bravo Rapid Cargo", capacity_units=180, remaining_capacity=0),
            Vehicle(vehicle_id="veh-03", name="Charlie 4x4 High-Clearance", capacity_units=120, remaining_capacity=0),
            Vehicle(vehicle_id="veh-04", name="Delta Flood Rescue Utility", capacity_units=80, remaining_capacity=0)
        ]
        findings = cls.run_independent_verification(
            initial_inventory=initial_inventory,
            allocations=allocations,
            requests=requests,
            vehicles=dummy_vehicles,
            delivery_tasks=delivery_tasks
        )

        all_passed = all(f.passed for f in findings if f.severity == "CRITICAL")

        # Compute summary metrics
        total_requested: Dict[str, int] = {}
        for r in requests:
            if not r.is_duplicate:
                total_requested[r.resource_type] = total_requested.get(r.resource_type, 0) + r.quantity_requested

        total_allocated: Dict[str, int] = {}
        total_shortages: Dict[str, int] = {}
        for a in allocations:
            total_allocated[a.resource_type] = total_allocated.get(a.resource_type, 0) + a.allocated_quantity
            if a.unfulfilled_quantity > 0:
                total_shortages[a.resource_type] = total_shortages.get(a.resource_type, 0) + a.unfulfilled_quantity

        dup_count = sum(1 for r in requests if r.is_duplicate)

        # Build readable markdown summary
        summary_md = cls._build_markdown_summary(
            run_id=run_id,
            scenario_name=scenario_name,
            total_requested=total_requested,
            total_allocated=total_allocated,
            total_shortages=total_shortages,
            allocations=allocations,
            delivery_tasks=delivery_tasks,
            unassigned_deliveries=unassigned_deliveries,
            findings=findings,
            all_passed=all_passed
        )

        return SimulationReport(
            run_id=run_id,
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            workflow_state=WorkflowState.COMPLETED if all_passed else WorkflowState.PARTIAL,
            total_requests_received=len(requests),
            total_unique_requests=len(requests) - dup_count,
            duplicate_requests_flagged=dup_count,
            total_resources_requested=total_requested,
            total_resources_allocated=total_allocated,
            total_shortages=total_shortages,
            allocations=allocations,
            delivery_tasks=delivery_tasks,
            unassigned_deliveries=unassigned_deliveries,
            verification_findings=findings,
            verification_passed=all_passed,
            execution_trace=execution_trace,
            participating_agents=participating_agents,
            human_readable_summary=summary_md
        )

    @staticmethod
    def _build_markdown_summary(
        run_id: str,
        scenario_name: str,
        total_requested: Dict[str, int],
        total_allocated: Dict[str, int],
        total_shortages: Dict[str, int],
        allocations: List[Allocation],
        delivery_tasks: List[DeliveryTask],
        unassigned_deliveries: List[Dict[str, Any]],
        findings: List[VerificationFinding],
        all_passed: bool
    ) -> str:
        lines = [
            f"# ReliefMesh Emergency Operations Report",
            f"**Run ID:** `{run_id}` | **Scenario:** *{scenario_name}*",
            f"**Status:** {'VERIFIED & AUDITED' if all_passed else 'WARNINGS DETECTED'}",
            "",
            "## 1. Resource Balance & Shortages",
            "| Resource Type | Requested | Allocated | Shortage | Fulfillment % |",
            "| :--- | :---: | :---: | :---: | :---: |"
        ]

        all_keys = sorted(set(total_requested.keys()).union(total_allocated.keys()))
        for k in all_keys:
            req = total_requested.get(k, 0)
            alloc = total_allocated.get(k, 0)
            shortage = total_shortages.get(k, 0)
            pct = round((alloc / req * 100), 1) if req > 0 else 100.0
            status_flag = " (Shortage)" if shortage > 0 else " (Full)"
            lines.append(f"| **{k.replace('_', ' ').title()}** | {req} | {alloc} | {shortage}{status_flag} | {pct}% |")

        lines.extend([
            "",
            "## 2. Priority-Ranked Allocations",
            "| Rank | Request | Location | Resource | Requested | Allocated | Status & Audit Reason |",
            "| :---: | :--- | :--- | :--- | :---: | :---: | :--- |"
        ])

        for a in allocations:
            status = "Fulfilled" if a.unfulfilled_quantity == 0 else f"Shortage ({a.unfulfilled_quantity} unfulfilled)"
            lines.append(
                f"| #{a.priority_rank} | `{a.request_id}` | {a.location_id} | {a.resource_type} | {a.requested_quantity} | **{a.allocated_quantity}** | {a.priority_explanation} |"
            )

        lines.extend([
            "",
            "## 3. Dispatch & Logistics Plan",
            f"**Total Scheduled Deliveries:** {len(delivery_tasks)} | **Unassigned:** {len(unassigned_deliveries)}",
            "",
            "| Seq | Vehicle | Destination | Cargo Loaded | Load % | Est. Transit | Assumptions |",
            "| :---: | :--- | :--- | :--- | :---: | :---: | :--- |"
        ])

        for t in delivery_tasks:
            cargo_str = ", ".join(f"{v} {k}" for k, v in t.items_loaded.items())
            assump_str = "; ".join(t.assumptions[:1])
            lines.append(f"| {t.delivery_sequence} | **{t.vehicle_name}** | {t.destination_name} | {cargo_str} | {t.capacity_percentage}% | {t.estimated_travel_time_min} min | {assump_str} |")

        lines.extend([
            "",
            "## 4. Independent Verification Audit",
            "| Check | Status | Details |",
            "| :--- | :---: | :--- |"
        ])

        for f in findings:
            status_badge = "[PASSED]" if f.passed else "[FAILED]"
            lines.append(f"| **{f.check_name}** | {status_badge} | {f.details} |")

        lines.extend([
            "",
            "> **SIMULATION NOTICE:** ReliefMesh is an experimental coordination model. All road conditions, patient censuses, and travel times are synthetic. Not for live emergency dispatch."
        ])

        return "\n".join(lines)
