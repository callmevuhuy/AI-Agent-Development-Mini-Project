"""Application boundary: resolves identity from mock users before dispatch."""
from typing import Any
from datetime import datetime, timezone
import re

from travel_agent.dispatcher import dispatch
from travel_agent.mock_systems.approval import get_approval_request
from travel_agent.mock_systems.approval import record_audit_event
from travel_agent.mock_systems.user import get_user
from travel_agent.orchestrator import run_tool
from travel_agent.planner import plan
from travel_agent.state import RunState
from travel_agent.workflows.a_pretrip import run_pretrip
from travel_agent.workflows.b_intrip import run_intrip
from travel_agent.workflows.c_posttrip import run_posttrip


_WORKFLOWS = {"pretrip": run_pretrip, "intrip": run_intrip, "posttrip": run_posttrip}
_TRIP_ID = re.compile(r"^TRIP-\d{4}-\d{3}$")
_REPORT_ID = re.compile(r"^EXP-\d{4}-\d{3}$")


def _audit_run(user: dict[str, Any], state: RunState, record_id: str | None) -> None:
    record_audit_event({
        "event_id": f"EVT-{state.run_id}", "event_type": "workflow_run",
        "actor_id": user["user_id"], "role": user["role"], "action": state.workflow,
        "trip_id": record_id if isinstance(record_id, str) and _TRIP_ID.fullmatch(record_id) else None,
        "report_id": record_id if isinstance(record_id, str) and _REPORT_ID.fullmatch(record_id) else None,
        "outcome": state.outcome, "reason_code": "workflow_terminal_outcome",
        "reason": "Workflow completed with a recorded terminal outcome.",
        "timestamp": datetime.now(timezone.utc).isoformat(), "run_id": state.run_id,
    })


def _user_context(user_id: str, session_id: str, approval_scope: dict[str, str] | None = None) -> dict[str, Any]:
    user = get_user(user_id)
    if not user:
        raise ValueError("Unknown mock user")
    context = {"user_id": user["user_id"], "role": user["role"], "session_id": session_id}
    if approval_scope:
        context["approval_scope"] = approval_scope
    return context


def run_workflow(
    workflow: str, user_id: str, record_id: str | None, *, session_id: str = "demo-session",
    approval_action_type: str | None = None, max_steps: int = 8, case_id: str | None = None,
) -> tuple[dict[str, Any], RunState]:
    if workflow not in _WORKFLOWS:
        raise ValueError("Unknown workflow")
    user = get_user(user_id)
    if not user:
        raise ValueError("Unknown mock user")
    scope = None
    if user["role"] == "Approver":
        if not approval_action_type or not get_approval_request(record_id or "", approval_action_type):
            raise ValueError("Approver needs an existing approval request scope")
        scope = {"trip_id": record_id or "", "action_type": approval_action_type}
    state = RunState(workflow, _user_context(user_id, session_id, scope), max_steps=max_steps, case_id=case_id)
    result = _WORKFLOWS[workflow](state, record_id)
    _audit_run(user, state, record_id)
    return result, state


def submit_approval_request(
    user_id: str, trip_id: str, action_type: str, action_summary: str, *,
    session_id: str = "demo-session",
) -> tuple[dict[str, Any], RunState]:
    state = RunState("pretrip" if action_type == "checklist_review" else "intrip", _user_context(user_id, session_id))
    result = run_tool(state, "request_approval", {
        "trip_id": trip_id, "action_type": action_type, "action_summary": action_summary,
    })
    outcome = "awaiting_approval" if result.get("ok") and result["data"].get("status") == "pending" else (
        "failed_validation" if not result.get("ok") else "needs_human"
    )
    state.finish(outcome)
    _audit_run(get_user(user_id), state, trip_id)
    return {"outcome": outcome, "approval_request": result}, state


def admin_query(user_id: str, tool_name: str, arguments: dict[str, Any] | None = None) -> tuple[dict[str, Any], RunState]:
    user = get_user(user_id)
    if not user:
        raise ValueError("Unknown mock user")
    state = RunState("admin", _user_context(user_id, "admin-session"))
    result = run_tool(state, tool_name, arguments or {})
    state.finish("completed" if result.get("ok") else "failed_validation")
    _audit_run(user, state, None)
    return {"outcome": state.outcome, "result": result}, state


def run_message(message: str, user_id: str, *, session_id: str = "demo-session") -> tuple[dict[str, Any], RunState | None]:
    planned = plan(message)
    if not planned:
        user = get_user(user_id)
        if not user:
            raise ValueError("Unknown mock user")
        state = RunState("pretrip", _user_context(user_id, session_id))
        state.set_phase("planning")
        state.finish("needs_input")
        _audit_run(user, state, None)
        return {"outcome": "needs_input", "message": "Please specify a supported trip or expense ID and the task."}, state
    result, state = run_workflow(planned["workflow"], user_id, planned["record_id"], session_id=session_id)
    return result, state


def cli() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Mock travel operations agent demo")
    commands = parser.add_subparsers(dest="command", required=True)
    workflow = commands.add_parser("run", help="Run one of the three employee/reviewer workflows")
    workflow.add_argument("workflow", choices=sorted(_WORKFLOWS))
    workflow.add_argument("--user", required=True)
    workflow.add_argument("--id", dest="record_id")
    workflow.add_argument("--approval-action", choices=["checklist_review", "escalation", "publish_request"])
    message = commands.add_parser("message", help="Route a supported natural-language request with the deterministic planner")
    message.add_argument("--user", required=True)
    message.add_argument("--text", required=True)
    request = commands.add_parser("request-approval", help="Create a pending-only mock approval request")
    request.add_argument("--user", required=True)
    request.add_argument("--trip", required=True)
    request.add_argument("--action", required=True, choices=["checklist_review", "escalation", "publish_request"])
    request.add_argument("--summary", required=True)
    trips = commands.add_parser("admin-trips", help="Admin read-only trip overview")
    trips.add_argument("--user", required=True)
    audit = commands.add_parser("admin-audit", help="Admin read-only audit history")
    audit.add_argument("--user", required=True)
    audit.add_argument("--trip")
    audit.add_argument("--report")
    args = parser.parse_args()
    if args.command == "run":
        result, state = run_workflow(args.workflow, args.user, args.record_id, approval_action_type=args.approval_action)
    elif args.command == "message":
        result, state = run_message(args.text, args.user)
    elif args.command == "request-approval":
        result, state = submit_approval_request(args.user, args.trip, args.action, args.summary)
    elif args.command == "admin-trips":
        result, state = admin_query(args.user, "admin_list_trips")
    else:
        result, state = admin_query(args.user, "admin_get_audit_history", {key: value for key, value in (("trip_id", args.trip), ("report_id", args.report)) if value})
    print(json.dumps({"result": result, "trace": state.trace}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    cli()
