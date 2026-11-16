from typing import Any

from travel_agent.tools._draft import create


# Tool Draft Workspace (Mục 6, 11.1): Tạo hoặc cập nhật bản nháp rà soát báo cáo chi phí.
def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return create("posttrip", arguments["report_id"], arguments["review_preview"])
