import re
from typing import Any

from travel_agent.orchestrator import run_tool
from travel_agent.state import RunState


_TRIP_ID = re.compile(r"^TRIP-\d{4}-\d{3}$")
_TRIP_FIELDS = ("trip_id", "traveler_id", "origin", "destination", "start_date", "end_date", "purpose", "travel_status")
_COUNTRY = {"Sydney": "Australia", "Singapore": "Singapore"}


def _stop(state: RunState, outcome: str, message: str, **details: Any) -> dict[str, Any]:
    state.finish(outcome)
    return {"outcome": outcome, "message": message, **details}


def run_pretrip(state: RunState, trip_id: str | None) -> dict[str, Any]:
    """Build a read-only pre-trip checklist preview from mock records and policy evidence."""
    state.set_phase("pretrip_validation")
    if not isinstance(trip_id, str) or not trip_id:
        return _stop(state, "needs_input", "Please provide a trip ID.")
    if not _TRIP_ID.fullmatch(trip_id):
        return _stop(state, "failed_validation", "The trip ID format is invalid.")

    state.set_phase("pretrip_trip_lookup")
    trip_result = run_tool(state, "get_trip_request", {"trip_id": trip_id})
    if not trip_result["ok"]:
        error = trip_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else (
            "failed_validation" if error["code"] == "not_found" else "partial"
        )
        return _stop(state, outcome, "Could not load the trip record.", error_code=error["code"])
    trip = trip_result["data"]

    state.set_phase("pretrip_requirement_discovery")
    trip_facts = {field: trip[field] for field in _TRIP_FIELDS if field in trip}
    validation_args = {"trip_facts": trip_facts, "evidence_refs": []}
    initial_validation = run_tool(state, "validate_trip_requirements", validation_args)
    if not initial_validation["ok"]:
        error = initial_validation["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, outcome, "Could not determine the trip requirements.", error_code=error["code"], trip=trip)
    requirements = initial_validation["data"]
    if requirements["missing_fields"]:
        return _stop(
            state, "needs_input", "The trip record is missing required information.",
            trip=trip, missing_fields=requirements["missing_fields"],
        )
    if requirements["unknown_destination_requirements"]:
        return _stop(state, "needs_human", "No configured policy requirements exist for this destination.", trip=trip)

    evidence: list[dict[str, Any]] = []
    version_conflicts: list[dict[str, Any]] = []
    resolved_versions: list[dict[str, Any]] = []
    country = _COUNTRY.get(trip["destination"], trip["destination"])
    state.set_phase("pretrip_policy_retrieval")
    for category in requirements["required_policy_categories"]:
        query = f"{country} business travel {category} requirements before departure"
        search_result = run_tool(state, "search_travel_policy", {
            "query": query, "category": category, "max_results": 5,
        })
        if not search_result["ok"]:
            error = search_result["error"]
            outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
            return _stop(state, outcome, "Policy retrieval did not complete.", error_code=error["code"], trip=trip)
        version_conflicts.extend(search_result["data"]["version_conflicts"])
        resolved_versions.extend(search_result["data"]["resolved_versions"])
        for chunk in search_result["data"]["results"]:
            evidence.append({
                "chunk_id": chunk["chunk_id"], "category": chunk["category"],
                "doc_id": chunk["doc_id"], "source": chunk["source"],
                "section": chunk["section"], "page": chunk.get("page"),
                "version": chunk["version"], "citation": chunk["citation"],
            })

    state.set_phase("pretrip_validation")
    final_result = run_tool(state, "validate_trip_requirements", {
        "trip_facts": trip_facts,
        "evidence_refs": [{"chunk_id": item["chunk_id"], "category": item["category"]} for item in evidence],
    })
    if not final_result["ok"]:
        error = final_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, outcome, "Trip requirements could not be validated.", error_code=error["code"], trip=trip)
    validation = final_result["data"]
    approval_status = validation["trip_approval_status"]
    checklist = {
        "trip_id": trip_id,
        "destination": trip["destination"],
        "approval_status": approval_status,
        "required_policy_categories": validation["required_policy_categories"],
        "evidence": evidence,
        "version_conflicts": version_conflicts,
        "resolved_versions": resolved_versions,
        "delivery_status": "not_published",
    }

    if any(item != "approval_pending" for item in validation["blocking"]):
        outcome, message = "needs_human", "The trip has a blocking travel or approval status."
    elif validation["missing_policy_categories"] or validation["invalid_evidence_refs"] or version_conflicts:
        outcome, message = "needs_human", "Required policy evidence is incomplete; a human reviewer must resolve the gap."
    elif approval_status == "pending":
        outcome, message = "awaiting_approval", "The trip is pending approval; this checklist is only a preview."
    else:
        outcome, message = "completed", "The read-only pre-trip checklist preview is ready."

    state.set_phase("pretrip_draft")
    draft_result = run_tool(state, "create_travel_checklist_draft", {
        "trip_id": trip_id, "checklist": checklist,
    })
    if not draft_result["ok"]:
        error = draft_result["error"]
        draft_outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, draft_outcome, "The checklist preview is ready, but the draft was not saved.", error_code=error["code"], checklist=checklist, validation=validation)
    return _stop(state, outcome, message, checklist=checklist, validation=validation, draft=draft_result["data"])
