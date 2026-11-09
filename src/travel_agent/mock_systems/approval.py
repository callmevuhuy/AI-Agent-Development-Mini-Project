from typing import Any

from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from ._storage import find_record, load_dataset, write_dataset

_REQUEST_LOCK = Lock()
_AUDIT_LOCK = Lock()


def get_trip_approval_status(trip_id: str) -> dict[str, Any] | None:
    return find_record("approvals.json", "trip_id", trip_id)


def get_approval_request(trip_id: str, action_type: str) -> dict[str, Any] | None:
    return next((
        row for row in load_dataset("approval_requests.json")
        if row.get("trip_id") == trip_id and row.get("action_type") == action_type
    ), None)


def create_approval_request(trip_id: str, action_type: str, action_summary: str, *, actor_id: str, actor_role: str, run_id: str) -> tuple[dict[str, Any], bool]:
    with _REQUEST_LOCK:
        return _create_approval_request(trip_id, action_type, action_summary, actor_id=actor_id, actor_role=actor_role, run_id=run_id)


def _create_approval_request(trip_id: str, action_type: str, action_summary: str, *, actor_id: str, actor_role: str, run_id: str) -> tuple[dict[str, Any], bool]:
    rows = load_dataset("approval_requests.json")
    existing = next((row for row in rows if row.get("trip_id") == trip_id and row.get("action_type") == action_type), None)
    if existing:
        return existing, True
    row = {
        "request_id": f"APR-{uuid4().hex[:12]}", "trip_id": trip_id,
        "action_type": action_type, "action_summary": action_summary,
        "status": "pending", "created_by": actor_id, "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    rows.append(row)
    write_dataset("approval_requests.json", rows)
    record_audit_event({
        "event_id": f"EVT-{uuid4().hex[:12]}", "event_type": "approval_request_created",
        "actor_id": actor_id, "role": actor_role, "action": action_type,
        "trip_id": trip_id, "request_id": row["request_id"], "outcome": "pending",
        "reason_code": "submitted_for_review", "reason": action_summary[:240],
        "timestamp": row["created_at"], "run_id": run_id,
    })
    return row, False


def record_audit_event(event: dict) -> None:
    with _AUDIT_LOCK:
        rows = load_dataset("audit_events.json")
        rows.append(dict(event))
        write_dataset("audit_events.json", rows)


def record_external_decision(
    trip_id: str, action_type: str, decision: str, reason_code: str, reason: str,
    *, actor_id: str, run_id: str = "external-simulation",
) -> dict:
    """Mock external approval-system hook; deliberately not exposed as an agent tool."""
    if decision not in {"approved", "denied"} or not reason_code.strip() or not reason.strip():
        raise ValueError("A valid decision and non-empty reason are required")
    from .user import get_user
    actor = get_user(actor_id)
    request = get_approval_request(trip_id, action_type)
    if not actor or actor.get("role") != "Approver" or not request or request.get("status") != "pending":
        raise ValueError("Only an application-authorized mock Approver can decide a pending request")
    event = {
        "event_id": f"EVT-{uuid4().hex[:12]}", "event_type": "approval_decision",
        "actor_id": actor_id, "role": "Approver", "action": action_type,
        "trip_id": trip_id, "outcome": decision, "reason_code": reason_code,
        "reason": reason[:240], "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
    }
    approvals = load_dataset("approvals.json")
    status = "approved" if decision == "approved" else "rejected"
    approval = next((row for row in approvals if row.get("trip_id") == trip_id), None)
    if approval is None:
        approvals.append({"trip_id": trip_id, "trip_approval_status": status})
    else:
        approval["trip_approval_status"] = status
    write_dataset("approvals.json", approvals)
    requests = load_dataset("approval_requests.json")
    request = next((row for row in requests if row.get("trip_id") == trip_id and row.get("action_type") == action_type), None)
    if request:
        request["status"] = status
        write_dataset("approval_requests.json", requests)
    record_audit_event(event)
    return event
