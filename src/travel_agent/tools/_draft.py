from typing import Any

from travel_agent.mock_systems.draft_workspace import upsert_draft
from travel_agent.mock_systems.expense import get_expense_report
from travel_agent.mock_systems.trip import get_trip_request
from travel_agent.tools._result import failure, success


def create(workflow: str, source_id: str, content: dict[str, Any]) -> dict[str, Any]:
    """Verify the backing mock record exists before writing an idempotent draft."""
    exists = get_expense_report(source_id) if workflow == "posttrip" else get_trip_request(source_id)
    if exists is None:
        return failure("not_found", "Không tìm thấy bản ghi trong dữ liệu demo. Hãy kiểm tra lại mã chuyến đi hoặc báo cáo.")
    return success(upsert_draft(workflow, source_id, content), "mock_draft_workspace", read_only=False)
