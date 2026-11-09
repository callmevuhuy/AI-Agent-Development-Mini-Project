import re
from typing import Any

from travel_agent.orchestrator import run_tool
from travel_agent.rag.claim_evidence_check import check_claim
from travel_agent.state import RunState


_TRIP_ID = re.compile(r"^TRIP-\d{4}-\d{3}$")


def _stop(state: RunState, outcome: str, message: str, **details: Any) -> dict[str, Any]:
    state.finish(outcome)
    return {"outcome": outcome, "message": message, **details}


def run_intrip(state: RunState, trip_id: str | None) -> dict[str, Any]:
    """Prepare safe disruption guidance and an idempotent support draft."""
    state.set_phase("intrip_validation")
    if not isinstance(trip_id, str) or not trip_id:
        return _stop(state, "needs_input", "Please provide a trip ID.")
    if not _TRIP_ID.fullmatch(trip_id):
        return _stop(state, "failed_validation", "The trip ID format is invalid.")

    state.set_phase("intrip_itinerary_lookup")
    itinerary_result = run_tool(state, "get_itinerary", {"trip_id": trip_id})
    if not itinerary_result["ok"]:
        error = itinerary_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else (
            "failed_validation" if error["code"] == "not_found" else "partial"
        )
        return _stop(state, outcome, "Could not load the itinerary.", error_code=error["code"])
    itinerary = itinerary_result["data"]
    disruption = itinerary.get("disruption")
    flight = itinerary.get("flight", {})
    if not isinstance(flight, dict):
        return _stop(state, "partial", "The itinerary flight facts are malformed.", trip_id=trip_id)
    if not disruption:
        if flight.get("status") == "cancelled":
            return _stop(state, "needs_human", "The flight is marked cancelled, but the itinerary has no disruption details.", trip_id=trip_id)
        return _stop(state, "completed", "No disruption is recorded in the itinerary.", trip_id=trip_id)

    state.set_phase("intrip_policy_retrieval")
    policy_result = run_tool(state, "search_travel_policy", {
        "query": "flight delay cancellation retain carrier notice contact human travel support rebooking hotel authorization",
        "category": "travel",
        "max_results": 5,
    })
    if not policy_result["ok"]:
        error = policy_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, outcome, "Disruption policy retrieval did not complete.", error_code=error["code"], trip_id=trip_id)
    evidence = [
        {
            "chunk_id": chunk["chunk_id"], "doc_id": chunk["doc_id"],
            "source": chunk["source"], "section": chunk["section"],
            "page": chunk.get("page"), "version": chunk["version"],
            "citation": chunk["citation"],
        }
        for chunk in policy_result["data"]["results"]
    ]
    disruption_type = disruption.get("type") if isinstance(disruption, dict) else None
    is_cancellation = disruption_type == "flight_cancelled"
    follow_up = "Retain the carrier's disruption notice and contact the human travel support channel."
    grounding = check_claim(follow_up, policy_result["data"]["results"])
    support_draft = {
        "trip_id": trip_id,
        "disruption": disruption,
        "flight_facts": {
            key: flight[key]
            for key in ("flight_id", "origin", "destination", "status", "departure", "arrival")
            if key in flight
        },
        "policy_evidence": evidence,
        "recommended_follow_up": follow_up if grounding["grounded"] else None,
        "grounding": grounding,
        "delivery_status": "not_sent",
        "review_required": is_cancellation or not evidence or not grounding["grounded"] or not isinstance(disruption_type, str),
    }
    state.set_phase("intrip_draft")
    draft_result = run_tool(state, "create_escalation_or_support_draft", {
        "trip_id": trip_id, "support_draft": support_draft,
    })
    if not draft_result["ok"]:
        error = draft_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, outcome, "The support preview is ready, but the draft was not saved.", error_code=error["code"], support_draft=support_draft)

    if not evidence or not grounding["grounded"] or not isinstance(disruption_type, str):
        outcome, message = "needs_human", "Disruption details or policy guidance are incomplete."
    elif is_cancellation:
        outcome, message = "needs_human", "A cancelled flight may require rebooking or lodging decisions by a human."
    else:
        outcome, message = "completed", "Safe delay guidance is ready; no booking, spending, or external contact was made."
    return _stop(state, outcome, message, support_draft=support_draft, draft=draft_result["data"])
