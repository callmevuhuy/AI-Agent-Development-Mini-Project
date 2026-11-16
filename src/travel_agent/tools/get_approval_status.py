from typing import Any

from travel_agent.mock_systems.approval import get_trip_approval_status
from travel_agent.tools._result import record_result


# Tool Approval (Mục 6, 8.1): Đọc trạng thái phê duyệt chuyến đi từ Mock Approval System.
def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return record_result(get_trip_approval_status(arguments["trip_id"]), "mock_approval_system")
