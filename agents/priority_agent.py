from typing import List, Tuple
from backend.schemas import ReliefRequest, ExecutionEvent
from services.allocation_service import AllocationEngine

class NeedsAndPriorityAgent:
    name: str = "NeedsAndPriorityAgent"

    @classmethod
    def evaluate_priorities(
        cls, 
        requests: List[ReliefRequest]
    ) -> Tuple[List[ReliefRequest], List[ReliefRequest], List[ExecutionEvent]]:
        """
        Filters duplicates, calculates priority scores, and generates transparent explanations.
        Returns:
        - active_requests: List[ReliefRequest]
        - duplicate_requests: List[ReliefRequest]
        - events: List[ExecutionEvent]
        """
        events: List[ExecutionEvent] = []
        active_requests: List[ReliefRequest] = []
        duplicate_requests: List[ReliefRequest] = []

        seen_fingerprints = set()

        for req in requests:
            fingerprint = (req.location_id, req.resource_type, req.quantity_requested)
            if req.is_duplicate or fingerprint in seen_fingerprints:
                req.is_duplicate = True
                duplicate_requests.append(req)
                events.append(ExecutionEvent(
                    agent_name=cls.name,
                    action="QUARANTINE_DUPLICATE",
                    details={
                        "request_id": req.request_id,
                        "location_id": req.location_id,
                        "resource_type": req.resource_type,
                        "quantity": req.quantity_requested
                    },
                    status="WARNING"
                ))
            else:
                seen_fingerprints.add(fingerprint)
                active_requests.append(req)

        # Calculate priority scores for active requests
        scored = []
        for req in active_requests:
            score, explanation = AllocationEngine.calculate_priority_score(req)
            scored.append((score, req, explanation))

        scored.sort(key=lambda x: (-x[0], x[1].created_at, x[1].request_id))

        events.append(ExecutionEvent(
            agent_name=cls.name,
            action="PRIORITIZATION_COMPLETED",
            details={
                "ranked_requests_count": len(scored),
                "quarantined_duplicates_count": len(duplicate_requests),
                "top_priority_request": scored[0][1].request_id if scored else None
            },
            status="SUCCESS"
        ))

        return active_requests, duplicate_requests, events
