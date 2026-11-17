from typing import Any

from travel_agent.mock_systems.policy_kb import search_policy_chunks
from travel_agent.tools._result import failure, success


# Tool Policy KB (Mục 6, 10.1): Tìm kiếm trích đoạn chính sách du lịch có phân quyền theo role.
def run(arguments: dict[str, Any], *, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(user_context, dict) or user_context.get("role") not in {"Employee", "Reviewer", "Approver"}:
        return failure("unauthorized_scope", "Vai trò này không được tra cứu kho chính sách. Hãy dùng Employee, Reviewer hoặc Approver có phạm vi phê duyệt hợp lệ.")
    data = search_policy_chunks(
        arguments["query"], arguments["category"], arguments.get("max_results", 3), user_context["role"]
    )
    return success(data, "mock_policy_knowledge_base")
