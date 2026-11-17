from typing import Any

from travel_agent.mock_systems.trip import list_trip_requests
from travel_agent.mock_systems.user import get_user
from travel_agent.tools._result import failure, success


# Tool Self-Serve (Mục 4): Liệt kê danh sách chuyến đi thuộc phạm vi ủy quyền của người dùng.
def run(arguments: dict[str, Any], *, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(user_context, dict):
        return failure("unauthorized_scope", "Thiếu thông tin vai trò từ ứng dụng. Hãy chọn lại tài khoản demo.")
    user = get_user(user_context.get("user_id", ""))
    if not user or user.get("role") not in {"Employee", "Reviewer"}:
        return failure("unauthorized_scope", "Vai trò này không được duyệt danh sách chuyến đi. Employee chỉ xem chuyến của mình; Reviewer và Admin xem theo chức năng được cấp.")
    traveler_id = user.get("traveler_id") if user["role"] == "Employee" else None
    trips = list_trip_requests(traveler_id=traveler_id)

    dest = arguments.get("destination")
    if isinstance(dest, str) and dest.strip():
        target = dest.strip().casefold()
        trips = [t for t in trips if str(t.get("destination", "")).casefold() == target]

    date_filter = arguments.get("date")
    if isinstance(date_filter, str) and date_filter:
        trips = [
            t for t in trips
            if isinstance(t.get("start_date"), str) and isinstance(t.get("end_date"), str)
            and t["start_date"] <= date_filter <= t["end_date"]
        ]
    return success(trips, "mock_travel_request_system")
