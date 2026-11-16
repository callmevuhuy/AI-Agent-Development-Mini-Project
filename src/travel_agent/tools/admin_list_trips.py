from typing import Any

from travel_agent.mock_systems._storage import load_dataset
from travel_agent.tools._result import success


# Tool Admin (Mục 4, 12): Xem toàn bộ danh sách chuyến đi dành riêng cho vai trò Admin.
def run(_: dict[str, Any]) -> dict[str, Any]:
    return success(load_dataset("trips.json"), "mock_travel_request_system")
