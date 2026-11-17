"""Vietnamese error copy shared by the agent and the demo API.

Codes remain stable for integrations; messages explain the cause and next step.
Never include raw exceptions or facts from records the caller cannot read.
"""

ERROR_MESSAGES = {
    "unauthorized_scope": "Dữ liệu được yêu cầu nằm ngoài phạm vi truy cập của bạn. Hãy kiểm tra lại mã dữ liệu hoặc phạm vi được cấp.",
    "invalid_argument": "Thông tin đầu vào không hợp lệ. Hãy kiểm tra mã chuyến đi (TRIP-YYYY-NNN), mã báo cáo (EXP-YYYY-NNN) và các trường bắt buộc.",
    "not_found": "Không tìm thấy bản ghi trong dữ liệu demo. Hãy kiểm tra lại mã chuyến đi hoặc báo cáo.",
    "not_allowed": "Thao tác này không được phép trong quy trình hiện tại. Hãy chọn chức năng phù hợp với vai trò của bạn.",
    "budget_exceeded": "Quy trình đã hết số bước xử lý cho phép. Hãy thu gọn yêu cầu hoặc nhờ Travel Operations hỗ trợ.",
    "timeout": "Công cụ phản hồi quá thời gian cho phép. Hãy thử lại sau.",
    "unavailable": "Không thể đọc dữ liệu hoặc thực thi công cụ lúc này. Hãy thử lại sau hoặc nhờ người quản trị kiểm tra dữ liệu demo.",
    "policy_access_required": "Vai trò hiện tại không có căn cứ chính sách cần thiết để rà soát chi phí. Hãy nhờ Reviewer hỗ trợ.",
}


ROLE_ACTIONS = {
    "pretrip": ("chuẩn bị checklist trước chuyến đi", "Employee hoặc Reviewer"),
    "intrip": ("tạo bản nháp hỗ trợ sự cố chuyến đi", "Employee hoặc Reviewer"),
    "posttrip": ("rà soát báo cáo chi phí", "Employee hoặc Reviewer"),
    "policy_qa": ("tra cứu chính sách công tác", "Reviewer hoặc Approver có phạm vi phù hợp"),
    "preference": ("quản lý tùy chọn cá nhân", "Employee, Reviewer hoặc Approver"),
    "audit": ("xem audit log", "Admin"),
    "trip_list": ("duyệt danh sách chuyến đi", "Employee, Reviewer hoặc Admin"),
    "request_approval": ("tạo yêu cầu phê duyệt", "Employee sở hữu chuyến đi"),
    "approval_decision": ("quyết định phê duyệt qua chat", "người phụ trách qua hệ thống phê duyệt mô phỏng"),
    "draft": ("xem hoặc tạo bản nháp nghiệp vụ", "Employee hoặc Reviewer"),
    "profile": ("xem hồ sơ nhân viên", "Employee sở hữu hồ sơ hoặc Reviewer"),
    "itinerary": ("đọc hành trình trong phạm vi phê duyệt hiện tại", "Employee, Reviewer hoặc người phụ trách cấp scope escalation"),
}


def role_error(role: str, action: str) -> dict:
    """Specific copy for an operation forbidden to the application-owned role."""
    label, owner = ROLE_ACTIONS.get(action, ("thực hiện thao tác này", "người phụ trách"))
    message = f"Vai trò {role} không được {label}. Hãy nhờ {owner} hỗ trợ."
    return {"ok": False, "error": {"code": "unauthorized_scope", "message": message, "retryable": False}}


def scope_error(message: str | None = None) -> dict:
    return {"ok": False, "error": {"code": "unauthorized_scope", "message": message or ERROR_MESSAGES["unauthorized_scope"], "retryable": False}}


def tool_role_error(role: str, tool_name: str) -> dict:
    action = {
        "get_trip_request": "pretrip", "get_itinerary": "itinerary", "get_approval_status": "pretrip",
        "validate_trip_requirements": "pretrip", "get_expense_report": "posttrip",
        "calculate_expense_summary": "posttrip", "search_travel_policy": "policy_qa",
        "get_traveler_profile": "profile", "request_approval": "request_approval",
        "admin_get_audit_history": "audit", "admin_list_trips": "trip_list",
        "list_my_trips": "trip_list", "list_my_expenses": "posttrip",
        "create_travel_checklist_draft": "pretrip", "create_escalation_or_support_draft": "intrip",
        "create_expense_review_draft": "posttrip", "get_preference": "preference",
        "set_preference": "preference", "delete_preference": "preference",
    }.get(tool_name, "draft")
    return role_error(role, action)

def error_text(error: dict) -> str:
    """Render a safe tool error with its diagnostic code for support."""
    code = error.get("code", "unavailable")
    message = error.get("message") or ERROR_MESSAGES.get(code, ERROR_MESSAGES["unavailable"])
    return f"{message}\nMã lỗi: `{code}`."
