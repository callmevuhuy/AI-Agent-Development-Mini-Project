import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from travel_agent.tools import (
    calculate_expense_summary,
    create_escalation_or_support_draft,
    create_expense_review_draft,
    create_travel_checklist_draft,
    delete_preference,
    get_approval_status,
    get_expense_report,
    get_itinerary,
    get_preference,
    get_traveler_profile,
    get_trip_request,
    admin_get_audit_history,
    admin_list_trips,
    request_approval,
    search_travel_policy,
    set_preference,
    validate_trip_requirements,
)


@dataclass(frozen=True)
class ToolSpec:
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    schema: dict[str, Any]
    description: str


_SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
_TOOL_DEFINITIONS = {
    "get_trip_request": (get_trip_request.run, "Read a mock business travel request."),
    "get_traveler_profile": (get_traveler_profile.run, "Read a non-sensitive mock traveler profile."),
    "get_itinerary": (get_itinerary.run, "Read a mock itinerary and disruption status."),
    "get_approval_status": (get_approval_status.run, "Read the mock trip approval status."),
    "get_expense_report": (get_expense_report.run, "Read a mock expense report."),
    "calculate_expense_summary": (calculate_expense_summary.run, "Calculate expense totals, ratios, missing fields, receipts, and threshold flags deterministically."),
    "validate_trip_requirements": (validate_trip_requirements.run, "Check mock trip fields, approval state, and required policy evidence categories."),
    "search_travel_policy": (search_travel_policy.run, "Search mock policy chunks by query and category."),
    "create_travel_checklist_draft": (create_travel_checklist_draft.run, "Create or update the sandbox pre-trip checklist draft."),
    "create_escalation_or_support_draft": (create_escalation_or_support_draft.run, "Create or update an in-trip support draft; does not contact anyone."),
    "create_expense_review_draft": (create_expense_review_draft.run, "Create or update a deterministic expense review draft."),
    "get_preference": (get_preference.run, "Read one saved preference for the signed-in user."),
    "set_preference": (set_preference.run, "Save a preference when the signed-in user requests it."),
    "delete_preference": (delete_preference.run, "Delete one saved preference for the signed-in user."),
    "request_approval": (request_approval.run, "Create an idempotent pending-only mock approval request."),
    "admin_list_trips": (admin_list_trips.run, "Read all mock trips; Admin only."),
    "admin_get_audit_history": (admin_get_audit_history.run, "Read append-only mock activity history; Admin only."),
}

TOOL_REGISTRY = {
    name: ToolSpec(
        handler=handler,
        schema=json.loads((_SCHEMA_DIR / f"{name}.json").read_text(encoding="utf-8")),
        description=description,
    )
    for name, (handler, description) in _TOOL_DEFINITIONS.items()
}

# Keep each workflow's exposed function list limited to its implemented tools.
WORKFLOW_ALLOWLISTS = {
    "pretrip": frozenset({"get_trip_request", "get_approval_status", "get_traveler_profile", "search_travel_policy", "validate_trip_requirements", "create_travel_checklist_draft", "request_approval", "get_preference", "set_preference", "delete_preference"}),
    "intrip": frozenset({"get_itinerary", "search_travel_policy", "create_escalation_or_support_draft", "request_approval", "get_preference", "set_preference", "delete_preference"}),
    "posttrip": frozenset({"get_expense_report", "calculate_expense_summary", "search_travel_policy", "create_expense_review_draft", "get_preference", "set_preference", "delete_preference"}),
    "admin": frozenset({"admin_list_trips", "admin_get_audit_history"}),
}


def function_specs(workflow: str) -> list[dict[str, Any]]:
    allowed = WORKFLOW_ALLOWLISTS.get(workflow, frozenset())
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": spec.description,
                "parameters": spec.schema,
            },
        }
        for name, spec in TOOL_REGISTRY.items()
        if name in allowed
    ]
