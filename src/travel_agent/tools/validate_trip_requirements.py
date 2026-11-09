from typing import Any

from travel_agent.mock_systems.approval import get_trip_approval_status
from travel_agent.mock_systems.policy_kb import get_policy_chunks
from travel_agent.mock_systems.trip import get_trip_request
from travel_agent.mock_systems._storage import load_dataset
from travel_agent.tools._result import failure, success


def run(arguments: dict[str, Any], *, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(user_context, dict):
        return failure("unauthorized_scope", "Application role context is required.")
    supplied_facts = arguments["trip_facts"]
    trip_id = supplied_facts.get("trip_id")
    # Only accept the ID from caller; refresh all business facts from the source of truth.
    trip = get_trip_request(trip_id) if trip_id else None
    if trip is None:
        return failure("not_found", "The requested mock record was not found.")

    requirements = load_dataset("requirements.json")
    approval = get_trip_approval_status(trip_id) or {}
    missing_fields = [
        field for field in requirements["required_trip_fields"]
        if not isinstance(trip.get(field), str) or not trip[field].strip()
    ]
    blocking = []
    if trip.get("travel_status") in requirements["needs_human_travel_statuses"]:
        blocking.append("travel_cancelled")
    approval_status = approval.get("trip_approval_status")
    if approval_status in requirements["needs_human_trip_approval_statuses"]:
        blocking.append("approval_rejected")
    elif approval_status in requirements["awaiting_approval_trip_statuses"]:
        blocking.append("approval_pending")

    required_categories = requirements["destination_policy_categories"].get(trip.get("destination"))
    chunks_by_id = {
        chunk["chunk_id"]: chunk
        for chunk in get_policy_chunks(role=user_context.get("role"))
    }
    valid_refs = [
        ref for ref in arguments["evidence_refs"]
        if ref["chunk_id"] in chunks_by_id
        and ref["category"] == chunks_by_id[ref["chunk_id"]]["category"]
    ]
    present_categories = {ref["category"] for ref in valid_refs}
    missing_categories = sorted(set(required_categories or []) - present_categories)
    unknown_destination = required_categories is None
    if unknown_destination:
        blocking.append("unknown_destination_requirements")

    data = {
        "trip_id": trip_id,
        "missing_fields": missing_fields,
        "blocking": blocking,
        "required_policy_categories": required_categories or [],
        "missing_policy_categories": missing_categories,
        "unknown_destination_requirements": unknown_destination,
        "invalid_evidence_refs": len(arguments["evidence_refs"]) - len(valid_refs),
        "trip_approval_status": approval_status,
    }
    return success(data, "mock_travel_request_system+mock_approval_system+mock_policy_knowledge_base")
