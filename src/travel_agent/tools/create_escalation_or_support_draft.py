from typing import Any

from travel_agent.tools._draft import create


# Tool Draft Workspace (Mục 6, 11.1): Tạo hoặc cập nhật bản nháp hỗ trợ sự cố gián đoạn hành trình.
def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return create("intrip", arguments["trip_id"], arguments["support_draft"])
