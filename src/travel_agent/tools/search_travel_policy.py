from typing import Any

from travel_agent.mock_systems.policy_kb import search_policy_chunks
from travel_agent.tools._result import failure, success


def run(arguments: dict[str, Any], *, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(user_context, dict) or user_context.get("role") not in {"Employee", "Reviewer", "Approver"}:
        return failure("unauthorized_scope", "This user cannot search the policy corpus.")
    data = search_policy_chunks(
        arguments["query"], arguments["category"], arguments.get("max_results", 3), user_context["role"]
    )
    return success(data, "mock_policy_knowledge_base")
