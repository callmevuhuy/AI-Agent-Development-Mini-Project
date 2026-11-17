from typing import Any

from travel_agent.mock_systems.approval import create_approval_request
from travel_agent.tools._result import failure, success


# Tool Approval Simulation (Mục 6, 11.2): Tạo yêu cầu phê duyệt mô phỏng ở trạng thái pending mang tính idempotent.
def run(arguments: dict[str, Any], *, user_context: dict[str, Any], run_id: str) -> dict[str, Any]:
    record, reused = create_approval_request(
        arguments["trip_id"], arguments["action_type"], arguments["action_summary"],
        actor_id=user_context["user_id"], actor_role=user_context["role"], run_id=run_id,
    )
    if record.get("status") != "pending":
        return failure("not_allowed", "Yêu cầu phê duyệt này đã được xử lý nên không thể tạo lại. Hãy kiểm tra trạng thái phê duyệt hoặc nhờ Travel Operations hỗ trợ.")
    result = success(record, "mock_approval_request_system", read_only=False)
    result["meta"]["reused"] = reused
    return result
