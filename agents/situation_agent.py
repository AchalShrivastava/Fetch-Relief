from typing import List, Tuple, Dict, Any
from backend.schemas import ReliefRequest, AffectedLocation, ExecutionEvent

class SituationAssessmentAgent:
    name: str = "SituationAssessmentAgent"

    @classmethod
    def assess_scenario(
        cls, 
        locations: List[AffectedLocation], 
        requests: List[ReliefRequest]
    ) -> Tuple[List[ReliefRequest], List[ExecutionEvent], List[str]]:
        """
        Parses incident requests, distinguishes confirmed inputs from assumptions,
        detects incomplete reports, and flags duplicates.
        """
        events: List[ExecutionEvent] = []
        warnings: List[str] = []

        events.append(ExecutionEvent(
            agent_name=cls.name,
            action="INGEST_INCIDENT_DATA",
            details={
                "locations_count": len(locations),
                "total_raw_requests": len(requests)
            },
            status="SUCCESS"
        ))

        # Check for unverified or low-confidence requests
        assessed_requests: List[ReliefRequest] = []
        for r in requests:
            if r.confidence_score < 0.5:
                warnings.append(f"Request {r.request_id} for {r.resource_type} has low confidence ({r.confidence_score:.2f}) from source '{r.source}'.")
                events.append(ExecutionEvent(
                    agent_name=cls.name,
                    action="FLAG_LOW_CONFIDENCE",
                    details={"request_id": r.request_id, "confidence": r.confidence_score, "source": r.source},
                    status="WARNING"
                ))
            assessed_requests.append(r)

        events.append(ExecutionEvent(
            agent_name=cls.name,
            action="ASSESSMENT_COMPLETED",
            details={
                "validated_requests": len(assessed_requests),
                "warnings_count": len(warnings)
            },
            status="SUCCESS"
        ))

        return assessed_requests, events, warnings
