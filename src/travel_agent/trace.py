import re
from typing import Any

from travel_agent.registry import TOOL_REGISTRY
from travel_agent.state import RunState


_TRIP_ID = re.compile(r"^TRIP-\d{4}-\d{3}$")
_EXPENSE_ID = re.compile(r"^EXP-\d{4}-\d{3}$")
_TRAVELER_ID = re.compile(r"^EMP-\d{3}$")
_CATEGORIES = {"travel", "expense", "visa", "insurance", "approval"}


def _safe_id(value: Any, pattern: re.Pattern[str]) -> str:
    return value if isinstance(value, str) and pattern.fullmatch(value) else "[redacted]"


def safe_arguments(tool_name: str, arguments: Any) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        return {}
    safe: dict[str, Any] = {}
    if tool_name in {"get_trip_request", "get_itinerary", "get_approval_status", "request_approval", "admin_get_audit_history"}:
        if "trip_id" in arguments or tool_name != "admin_get_audit_history":
            safe["trip_id"] = _safe_id(arguments.get("trip_id"), _TRIP_ID)
        if tool_name == "admin_get_audit_history":
            safe["report_id"] = _safe_id(arguments.get("report_id"), _EXPENSE_ID) if "report_id" in arguments else None
        if tool_name == "request_approval":
            safe["action_type"] = arguments.get("action_type") if arguments.get("action_type") in {"checklist_review", "escalation", "publish_request"} else "[invalid]"
    elif tool_name == "admin_list_trips":
        safe = {}
    elif tool_name in {"get_expense_report", "calculate_expense_summary"}:
        safe["report_id"] = _safe_id(arguments.get("report_id"), _EXPENSE_ID)
    elif tool_name == "get_traveler_profile":
        safe["traveler_id"] = _safe_id(arguments.get("traveler_id"), _TRAVELER_ID)
    elif tool_name in {"get_preference", "set_preference", "delete_preference"}:
        key = arguments.get("key")
        safe["key"] = key if isinstance(key, str) and key in {"response_language", "preferred_output_format"} else "[invalid]"
    elif tool_name == "search_travel_policy":
        category = arguments.get("category")
        safe["category"] = category if isinstance(category, str) and category in _CATEGORIES else "[invalid]"
        safe["max_results"] = arguments.get("max_results") if type(arguments.get("max_results")) is int else None
        query = arguments.get("query")
        safe["query_length"] = len(query) if isinstance(query, str) else None
    elif tool_name == "validate_trip_requirements":
        facts = arguments.get("trip_facts")
        trip_id = facts.get("trip_id") if isinstance(facts, dict) else None
        evidence = arguments.get("evidence_refs")
        safe["trip_id"] = _safe_id(trip_id, _TRIP_ID)
        safe["evidence_ref_count"] = len(evidence) if isinstance(evidence, list) else None
    return safe


def _result_summary(result: dict[str, Any]) -> dict[str, Any]:
    if result["ok"]:
        data = result.get("data")
        summary = {
            "ok": True,
            "source": result["meta"]["source"],
            "read_only": result["meta"]["read_only"],
        }
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            summary["result_count"] = len(data["results"])
            summary["no_result"] = data.get("no_result") is True
            summary["version_conflict_count"] = len(data.get("version_conflicts", [])) if isinstance(data.get("version_conflicts"), list) else 0
            summary["excluded_untrusted_count"] = len(data.get("excluded_untrusted_chunk_ids", [])) if isinstance(data.get("excluded_untrusted_chunk_ids"), list) else 0
        return summary
    error = result["error"]
    return {"ok": False, "error_code": error["code"], "retryable": error["retryable"]}


def record_tool_event(
    state: RunState,
    tool_name: str,
    arguments: Any,
    result: dict[str, Any],
    transition: str,
    *,
    executed: bool = True,
) -> None:
    tool_label = tool_name if isinstance(tool_name, str) and tool_name in TOOL_REGISTRY else "unregistered_tool"
    summary = _result_summary(result)
    if executed:
        state.safe_tool_results.append({"tool": tool_label, **summary})
    event = {
        "run_id": state.run_id,
        "phase": state.phase,
        "action": "tool_call",
        "tool": tool_label,
        "safe_args": safe_arguments(tool_label, arguments),
        "observation_status": ("ok" if result.get("ok") else "error") if executed else "not_executed",
        "transition": transition,
        "budget": {"step": state.step_count, "max": state.max_steps},
        "outcome": state.outcome,
    }
    if state.case_id is not None:
        event["case_id"] = state.case_id
    if not result.get("ok"):
        code = result.get("error", {}).get("code")
        if code in {"unauthorized_scope", "not_allowed"}:
            event["safety_event"] = "tool_or_scope_denied"
    else:
        data = result.get("data")
        if isinstance(data, dict) and data.get("excluded_untrusted_chunk_ids"):
            event["safety_event"] = "untrusted_policy_chunk_excluded"
    state.trace.append(event)
