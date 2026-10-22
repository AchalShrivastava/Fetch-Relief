from typing import List, Dict, Tuple
import uuid
from backend.schemas import ReliefRequest, Allocation, UrgencyLevel, InventoryItem
from services.inventory_service import InventoryService

class AllocationEngine:
    @staticmethod
    def calculate_priority_score(request: ReliefRequest) -> Tuple[float, str]:
        """
        Calculates a deterministic priority score between 0.0 and 100.0:
        - Urgency base weight: CRITICAL (40), HIGH (30), MEDIUM (20), LOW (10)
        - Vulnerability multiplier: up to 30 points (score from 1.0 to 5.0)
        - Confidence rating: up to 20 points (0.0 to 1.0)
        - Lifesaving resource boost: up to 10 points (first_aid, water, medicine)
        """
        urgency_weights = {
            UrgencyLevel.CRITICAL: 40.0,
            UrgencyLevel.HIGH: 30.0,
            UrgencyLevel.MEDIUM: 20.0,
            UrgencyLevel.LOW: 10.0
        }
        urgency_score = urgency_weights.get(request.urgency, 15.0)

        # Vulnerability component (scaled to max 30)
        vulnerability_score = min(max(request.vulnerability_score, 1.0), 5.0) * 6.0

        # Confidence component (scaled to max 20)
        confidence_component = min(max(request.confidence_score, 0.0), 1.0) * 20.0

        # Lifesaving resource critical bonus (up to 10 points)
        lifesaving_bonus = 0.0
        if request.resource_type in ["first_aid_kit", "water_unit", "medicine"]:
            lifesaving_bonus = 10.0
        elif request.resource_type in ["food_kit", "generator"]:
            lifesaving_bonus = 5.0

        total_score = urgency_score + vulnerability_score + confidence_component + lifesaving_bonus

        explanation = (
            f"Score: {total_score:.1f} | Urgency={request.urgency.value.upper()} ({urgency_score:.0f}pts), "
            f"Vulnerability={request.vulnerability_score:.1f}/5.0 ({vulnerability_score:.1f}pts), "
            f"Confidence={request.confidence_score:.2f} ({confidence_component:.1f}pts), "
            f"ResourceBonus={lifesaving_bonus:.0f}pts"
        )
        return total_score, explanation

    @classmethod
    def allocate_resources(
        cls, 
        requests: List[ReliefRequest], 
        inventory_service: InventoryService
    ) -> Tuple[List[Allocation], List[ReliefRequest], Dict[str, int], Dict[str, int]]:
        """
        Deterministic, priority-ordered greedy allocation.
        Returns:
        - allocations: List[Allocation]
        - processed_requests: List[ReliefRequest]
        - total_allocated: Dict[resource_type, total_qty]
        - total_shortages: Dict[resource_type, shortage_qty]
        """
        # 1. Filter out known duplicates or flagged invalid entries
        valid_requests: List[ReliefRequest] = []
        duplicate_or_invalid: List[ReliefRequest] = []

        seen_fingerprints = set()
        for req in requests:
            fingerprint = (req.location_id, req.resource_type, req.quantity_requested)
            if req.is_duplicate or fingerprint in seen_fingerprints:
                req.is_duplicate = True
                duplicate_or_invalid.append(req)
            else:
                seen_fingerprints.add(fingerprint)
                valid_requests.append(req)

        # 2. Score and sort valid requests deterministically
        scored_requests = []
        for req in valid_requests:
            score, explanation = cls.calculate_priority_score(req)
            scored_requests.append((score, req, explanation))

        # Deterministic sort: Priority score descending, created_at ascending, request_id ascending
        scored_requests.sort(key=lambda item: (-item[0], item[1].created_at, item[1].request_id))

        allocations: List[Allocation] = []
        total_allocated: Dict[str, int] = {}
        total_shortages: Dict[str, int] = {}

        event_batch_id = f"evt-batch-{uuid.uuid4().hex[:6]}"

        for rank, (score, req, explanation) in enumerate(scored_requests, start=1):
            allocated_qty, unfulfilled_qty, inventory_reason = inventory_service.reserve_stock(
                resource_type=req.resource_type,
                quantity=req.quantity_requested,
                request_id=req.request_id
            )

            total_allocated[req.resource_type] = total_allocated.get(req.resource_type, 0) + allocated_qty
            if unfulfilled_qty > 0:
                total_shortages[req.resource_type] = total_shortages.get(req.resource_type, 0) + unfulfilled_qty

            full_explanation = f"Rank #{rank} ({explanation}) -> {inventory_reason}"

            alloc = Allocation(
                request_id=req.request_id,
                location_id=req.location_id,
                resource_type=req.resource_type,
                requested_quantity=req.quantity_requested,
                allocated_quantity=allocated_qty,
                unfulfilled_quantity=unfulfilled_qty,
                priority_rank=rank,
                priority_score=score,
                priority_explanation=full_explanation,
                allocation_event_id=event_batch_id
            )
            allocations.append(alloc)

        return allocations, valid_requests, total_allocated, total_shortages
