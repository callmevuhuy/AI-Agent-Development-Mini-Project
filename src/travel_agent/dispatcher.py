import json
from typing import Any

from jsonschema import Draft202012Validator

from travel_agent.mock_systems.approval import get_approval_request
from travel_agent.mock_systems.expense import get_expense_report
from travel_agent.mock_systems.traveler import get_traveler_profile
from travel_agent.mock_systems.trip import get_trip_request
from travel_agent.mock_systems.user import get_user
from travel_agent.registry import TOOL_REGISTRY, WORKFLOW_ALLOWLISTS
from travel_agent.tools._result import failure


_TRIP_TOOLS = {"get_trip_request", "get_itinerary", "get_approval_status"}
_EXPENSE_TOOLS = {"get_expense_report", "calculate_expense_summary"}
_TRIP_DRAFT_TOOLS = {"create_travel_checklist_draft", "create_escalation_or_support_draft"}
_EXPENSE_DRAFT_TOOLS = {"create_expense_review_draft"}
_MEMORY_TOOLS = {"get_preference", "set_preference", "delete_preference"}
_APPROVER_READS = {
    "checklist_review": {"get_trip_request", "get_approval_status"},
    "escalation": {"get_itinerary"},
    "publish_request": {"get_trip_request", "get_approval_status"},
}
_APPROVER_RAG_CATEGORIES = {
    "checklist_review": {"approval", "travel", "visa", "insurance"},
    "escalation": {"travel"},
    "publish_request": {"approval"},
}
_ADMIN_TOOLS = {"admin_list_trips", "admin_get_audit_history"}
_RAG_ROLES = {"Employee", "Reviewer", "Approver"}


def _scope_error() -> dict[str, Any]:
    return failure("unauthorized_scope", "The requested resource is outside this user's scope.")


def _authorize(
    tool_name: str, arguments: dict[str, Any], user_context: dict[str, Any]
) -> dict[str, Any] | None:
    user_id = user_context.get("user_id")
    user = get_user(user_id) if isinstance(user_id, str) else None
    if (
        not user
        or user_context.get("role") != user["role"]
        or not isinstance(user_context.get("session_id"), str)
        or not user_context["session_id"]
    ):
        return _scope_error()

    role = user["role"]
    if role == "Admin":
        return None if tool_name in _ADMIN_TOOLS else _scope_error()
    if tool_name in _ADMIN_TOOLS:
        return _scope_error()
    if tool_name == "request_approval" and role != "Employee":
        return _scope_error()
    if tool_name == "request_approval":
        trip = get_trip_request(arguments.get("trip_id", ""))
        if not trip or trip.get("traveler_id") != user.get("traveler_id"):
            return _scope_error()
    if tool_name in _MEMORY_TOOLS:
        if tool_name in {"set_preference", "delete_preference"} and user_context.get("memory_write_authorized") is not True:
            return failure("not_allowed", "Persistent preference changes require an explicit user request.")
        return None
    if tool_name == "search_travel_policy":
        if role not in _RAG_ROLES:
            return _scope_error()
        if role == "Approver":
            scope = user_context.get("approval_scope")
            category = arguments.get("category")
            if (
                not isinstance(scope, dict)
                or set(scope) != {"trip_id", "action_type"}
                or scope.get("action_type") not in _APPROVER_RAG_CATEGORIES
                or category not in _APPROVER_RAG_CATEGORIES[scope["action_type"]]
            ):
                return _scope_error()
            request = get_approval_request(scope["trip_id"], scope["action_type"])
            if not request or request.get("status") != "pending":
                return _scope_error()
        return None
    if role == "Reviewer":
        return None
    if role == "Approver":
        scope = user_context.get("approval_scope")
        if (
            tool_name not in _TRIP_TOOLS
            or not isinstance(scope, dict)
            or set(scope) != {"trip_id", "action_type"}
            or not isinstance(scope.get("action_type"), str)
            or scope.get("action_type") not in _APPROVER_READS
            or arguments.get("trip_id") != scope.get("trip_id")
            or tool_name not in _APPROVER_READS[scope["action_type"]]
        ):
            return _scope_error()
        request = get_approval_request(scope["trip_id"], scope["action_type"])
        if not request or request.get("status") != "pending":
            return _scope_error()
        return None
    if role != "Employee":
        return _scope_error()

    traveler_id = user.get("traveler_id")
    if tool_name in _TRIP_TOOLS or tool_name in _TRIP_DRAFT_TOOLS or tool_name in {"validate_trip_requirements", "request_approval"}:
        trip_id = arguments.get("trip_id") or arguments.get("trip_facts", {}).get("trip_id")
        trip = get_trip_request(trip_id) if trip_id else None
        if trip is not None and trip["traveler_id"] != traveler_id:
            return _scope_error()
    elif tool_name in _EXPENSE_TOOLS or tool_name in _EXPENSE_DRAFT_TOOLS:
        report = get_expense_report(arguments["report_id"])
        if report is not None and report["traveler_id"] != traveler_id:
            return _scope_error()
    elif tool_name == "get_traveler_profile" and arguments["traveler_id"] != traveler_id:
        return _scope_error()
    return None


def _valid_result(result: Any) -> bool:
    if not isinstance(result, dict) or not isinstance(result.get("ok"), bool):
        return False
    if result["ok"]:
        meta = result.get("meta")
        return (
            "data" in result
            and isinstance(meta, dict)
            and isinstance(meta.get("source"), str)
            and isinstance(meta.get("read_only"), bool)
        )
    error = result.get("error")
    return (
        isinstance(error, dict)
        and isinstance(error.get("code"), str)
        and isinstance(error.get("message"), str)
        and isinstance(error.get("retryable"), bool)
    )


def dispatch(
    tool_name: str,
    arguments: dict[str, Any],
    workflow: str,
    user_context: dict[str, Any],
    *,
    steps_used: int = 0,
    max_steps: int = 8,
    run_id: str = "direct-dispatch",
) -> dict[str, Any]:
    if not isinstance(tool_name, str) or not isinstance(workflow, str):
        return failure("not_allowed", "Tool is not allowed in this workflow.")
    spec = TOOL_REGISTRY.get(tool_name)
    if spec is None:
        return failure("not_allowed", "Tool is not registered.")
    if tool_name not in WORKFLOW_ALLOWLISTS.get(workflow, frozenset()):
        return failure("not_allowed", "Tool is not allowed in this workflow.")
    if not isinstance(arguments, dict) or not Draft202012Validator(spec.schema).is_valid(arguments):
        return failure("invalid_argument", "Tool arguments do not match the registered schema.")
    if not isinstance(user_context, dict):
        return _scope_error()
    try:
        denied = _authorize(tool_name, arguments, user_context)
    except (OSError, json.JSONDecodeError):
        return failure("unavailable", "Mock authorization data could not be read.", retryable=True)
    except Exception:
        return failure("unavailable", "Mock authorization failed safely.")
    if denied:
        return denied
    if (
        isinstance(steps_used, bool)
        or isinstance(max_steps, bool)
        or not isinstance(steps_used, int)
        or not isinstance(max_steps, int)
        or max_steps < 1
        or max_steps > 8
        or steps_used < 0
        or steps_used >= max_steps
    ):
        return failure("budget_exceeded", "The run has no remaining tool-call budget.")
    try:
        if tool_name in _MEMORY_TOOLS or tool_name in {"search_travel_policy", "validate_trip_requirements", "calculate_expense_summary"}:
            result = spec.handler(arguments, user_context=user_context)
        elif tool_name == "request_approval":
            result = spec.handler(arguments, user_context=user_context, run_id=run_id)
        else:
            result = spec.handler(arguments)
    except (OSError, json.JSONDecodeError):
        return failure("unavailable", "Mock data could not be read.", retryable=True)
    except Exception:
        return failure("unavailable", "The mock tool failed safely.")
    if not _valid_result(result):
        return failure("unavailable", "The mock tool returned an invalid result.")
    return result
