from typing import Any

from travel_agent.mock_systems.traveler import get_traveler_profile as read_traveler_profile
from travel_agent.tools._result import record_result


# Tool Traveler Profile (Mục 6): Đọc hồ sơ nhân viên và tùy chọn không nhạy cảm theo traveler_id.
def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return record_result(read_traveler_profile(arguments["traveler_id"]), "mock_traveler_profile_system")
