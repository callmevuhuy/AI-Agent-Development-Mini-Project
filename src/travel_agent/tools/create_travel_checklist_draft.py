from typing import Any

from travel_agent.tools._draft import create


# Tool Draft Workspace (Mục 6, 11.1): Tạo hoặc cập nhật bản nháp checklist trước chuyến đi.
def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return create("pretrip", arguments["trip_id"], arguments["checklist"])
