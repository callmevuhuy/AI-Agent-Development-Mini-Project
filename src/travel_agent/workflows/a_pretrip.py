import re
from typing import Any

from travel_agent.mock_systems._storage import load_dataset
from travel_agent.orchestrator import run_tool
from travel_agent.state import RunState

_TRIP_ID = re.compile(r"^TRIP-\d{4}-\d{3}$")
_TRIP_FIELDS = ("trip_id", "traveler_id", "origin", "destination", "start_date", "end_date", "purpose", "travel_status")
_COUNTRY = {"Sydney": "Australia", "Singapore": "Singapore"}


# Workflow State (Mục 9.1): Chốt trạng thái dừng và ghi nhận terminal outcome.
def _stop(state: RunState, outcome: str, message: str, **details: Any) -> dict[str, Any]:
    if details.get("error_code"):
        for observation in reversed(state.safe_tool_results):
            if observation.get("error_code") == details["error_code"]:
                details["error"] = {
                    "code": observation["error_code"],
                    "message": observation["error_message"],
                    "retryable": observation["retryable"],
                }
                message = observation["error_message"]
                break
    state.finish(outcome)
    return {"outcome": outcome, "message": message, **details}


# Workflow A (Mục 8.1): Chuẩn bị trước chuyến đi và kiểm tra tuân thủ chính sách theo chuỗi 6 bước chuẩn.
def run_pretrip(state: RunState, trip_id: str | None) -> dict[str, Any]:
    """Execute pre-trip planning and compliance workflow following the Section 8.1 contract."""
    # Bước 1 (Mục 8.1): Kiểm định định dạng trip_id
    state.set_phase("pretrip_validation")
    if not isinstance(trip_id, str) or not trip_id:
        return _stop(state, "needs_input", "Vui lòng cung cấp mã chuyến đi theo định dạng TRIP-YYYY-NNN.")
    if not _TRIP_ID.fullmatch(trip_id):
        return _stop(state, "failed_validation", "Mã chuyến đi không hợp lệ. Hãy dùng định dạng TRIP-YYYY-NNN.")

    # Bước 2 (Mục 8.1): Truy vấn dữ liệu chuyến đi từ Mock Travel Request System
    state.set_phase("pretrip_trip_lookup")
    trip_result = run_tool(state, "get_trip_request", {"trip_id": trip_id})
    if not trip_result["ok"]:
        error = trip_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else (
            "failed_validation" if error["code"] == "not_found" else "partial"
        )
        return _stop(state, outcome, "Không tải được hồ sơ chuyến đi. Hãy thử lại hoặc nhờ Travel Operations hỗ trợ.", error_code=error["code"])
    trip = trip_result["data"]

    # Kiểm tra các trường thiết yếu của chuyến đi (Mục 8.1: dừng/hỏi lại khi thiếu trường thiết yếu)
    trip_facts = {field: trip[field] for field in _TRIP_FIELDS if field in trip}
    requirements_config = load_dataset("requirements.json")
    missing_fields = [
        field for field in requirements_config["required_trip_fields"]
        if not isinstance(trip.get(field), str) or not trip[field].strip()
    ]
    if missing_fields:
        return _stop(
            state, "needs_input", "Hồ sơ chuyến đi thiếu thông tin bắt buộc. Vui lòng bổ sung các trường được liệt kê.",
            trip=trip, missing_fields=missing_fields,
            validation={
                "trip_id": trip_id,
                "missing_fields": missing_fields,
                "blocking": [],
                "required_policy_categories": [],
                "missing_policy_categories": [],
                "unknown_destination_requirements": False,
                "invalid_evidence_refs": 0,
                "trip_approval_status": None,
            },
        )

    # Bước 3 (Mục 8.1): Truy vấn trạng thái phê duyệt từ Mock Approval System
    state.set_phase("pretrip_approval_lookup")
    approval_result = run_tool(state, "get_approval_status", {"trip_id": trip_id})
    if not approval_result["ok"]:
        error = approval_result["error"]
        if error["code"] == "not_found":
            approval_status = None
        else:
            outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
            return _stop(state, outcome, "Không tải được trạng thái phê duyệt. Hãy thử lại hoặc nhờ Travel Operations hỗ trợ.", error_code=error["code"], trip=trip)
    else:
        approval_data = approval_result["data"]
        approval_status = approval_data.get("trip_approval_status") or approval_data.get("status")

    blocking = []
    if trip.get("travel_status") in requirements_config["needs_human_travel_statuses"]:
        blocking.append("travel_cancelled")
    if approval_status in requirements_config["needs_human_trip_approval_statuses"]:
        blocking.append("approval_rejected")
    elif approval_status in requirements_config["awaiting_approval_trip_statuses"]:
        blocking.append("approval_pending")

    early_blocking = [item for item in blocking if item != "approval_pending"]
    if early_blocking:
        return _stop(
            state, "needs_human", "Trạng thái chuyến đi hoặc phê duyệt đang chặn quy trình. Cần người phụ trách xem xét.",
            trip=trip,
            validation={
                "trip_id": trip_id,
                "missing_fields": [],
                "blocking": blocking,
                "required_policy_categories": [],
                "missing_policy_categories": [],
                "unknown_destination_requirements": False,
                "invalid_evidence_refs": 0,
                "trip_approval_status": approval_status,
            },
        )

    required_categories = requirements_config["destination_policy_categories"].get(trip.get("destination"))
    if required_categories is None:
        return _stop(
            state, "needs_human", "Chưa có yêu cầu chính sách cho điểm đến này trong dữ liệu demo. Cần Travel Operations kiểm tra.",
            trip=trip,
            validation={
                "trip_id": trip_id,
                "missing_fields": [],
                "blocking": ["unknown_destination_requirements"],
                "required_policy_categories": [],
                "missing_policy_categories": [],
                "unknown_destination_requirements": True,
                "invalid_evidence_refs": 0,
                "trip_approval_status": approval_status,
            },
        )

    # Bước 4 (Mục 8.1): Tìm kiếm trích đoạn chính sách theo điểm đến và danh mục bắt buộc
    evidence: list[dict[str, Any]] = []
    version_conflicts: list[dict[str, Any]] = []
    resolved_versions: list[dict[str, Any]] = []
    country = _COUNTRY.get(trip["destination"], trip["destination"])
    state.set_phase("pretrip_policy_retrieval")
    for category in required_categories:
        query = f"{country} business travel {category} requirements before departure"
        search_result = run_tool(state, "search_travel_policy", {
            "query": query, "category": category, "max_results": 5,
        })
        if not search_result["ok"]:
            error = search_result["error"]
            outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
            return _stop(state, outcome, "Tra cứu chính sách chưa hoàn tất. Hãy thử lại hoặc nhờ Travel Operations hỗ trợ.", error_code=error["code"], trip=trip)
        version_conflicts.extend(search_result["data"]["version_conflicts"])
        resolved_versions.extend(search_result["data"]["resolved_versions"])
        for chunk in search_result["data"]["results"]:
            evidence.append({
                "chunk_id": chunk["chunk_id"], "category": chunk["category"],
                "doc_id": chunk["doc_id"], "source": chunk["source"],
                "section": chunk["section"], "page": chunk.get("page"),
                "version": chunk["version"], "citation": chunk["citation"],
            })

    # Bước 5 (Mục 8.1): Kiểm định sự tuân thủ điều kiện bằng facts đã truy vấn và bằng chứng chính sách
    state.set_phase("pretrip_validation")
    final_result = run_tool(state, "validate_trip_requirements", {
        "trip_facts": trip_facts,
        "evidence_refs": [{"chunk_id": item["chunk_id"], "category": item["category"]} for item in evidence],
    })
    if not final_result["ok"]:
        error = final_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, outcome, "Chưa kiểm tra được điều kiện công tác. Hãy nhờ Travel Operations xác minh dữ liệu.", error_code=error["code"], trip=trip)
    validation = final_result["data"]
    checklist = {
        "trip_id": trip_id,
        "destination": trip["destination"],
        "approval_status": approval_status,
        "required_policy_categories": validation["required_policy_categories"],
        "evidence": evidence,
        "version_conflicts": version_conflicts,
        "resolved_versions": resolved_versions,
        "delivery_status": "not_published",
    }

    if any(item != "approval_pending" for item in validation["blocking"]):
        outcome, message = "needs_human", "Trạng thái chuyến đi hoặc phê duyệt đang chặn quy trình. Cần người phụ trách xem xét."
    elif validation["missing_policy_categories"] or validation["invalid_evidence_refs"] or version_conflicts:
        outcome, message = "needs_human", "Thiếu căn cứ chính sách bắt buộc. Cần Reviewer kiểm tra và bổ sung trước khi tiếp tục."
    elif approval_status == "pending":
        outcome, message = "awaiting_approval", "The trip is pending approval; this checklist is only a preview."
    else:
        outcome, message = "completed", "The read-only pre-trip checklist preview is ready."

    # Mục 11.2: pending chỉ trả preview, không ghi artifact khi chưa được duyệt.
    if approval_status == "pending":
        return _stop(state, outcome, message, trip=trip, checklist=checklist, validation=validation)

    # Bước 6 (Mục 8.1): Tạo bản ghi checklist nháp mang tính idempotent trong sandbox
    state.set_phase("pretrip_draft")
    draft_result = run_tool(state, "create_travel_checklist_draft", {
        "trip_id": trip_id, "checklist": checklist,
    })
    if not draft_result["ok"]:
        error = draft_result["error"]
        draft_outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, draft_outcome, "Đã chuẩn bị nội dung checklist nhưng chưa lưu được bản nháp. Hãy thử lại hoặc nhờ người quản trị kiểm tra.", error_code=error["code"], checklist=checklist, validation=validation)
    return _stop(state, outcome, message, trip=trip, checklist=checklist, validation=validation, draft=draft_result["data"])
