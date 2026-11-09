from typing import Any

from travel_agent.mock_systems.approval import create_approval_request
from travel_agent.tools._result import failure, success


def run(arguments: dict[str, Any], *, user_context: dict[str, Any], run_id: str) -> dict[str, Any]:
    record, reused = create_approval_request(
        arguments["trip_id"], arguments["action_type"], arguments["action_summary"],
        actor_id=user_context["user_id"], actor_role=user_context["role"], run_id=run_id,
    )
    if record.get("status") != "pending":
        return failure("not_allowed", "This approval request has already been resolved.")
    result = success(record, "mock_approval_request_system", read_only=False)
    result["meta"]["reused"] = reused
    return result
