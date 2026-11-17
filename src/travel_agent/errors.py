"""Vietnamese error copy shared by the agent and the demo API.

Codes remain stable for integrations; messages explain the cause and next step.
Never include raw exceptions or facts from records the caller cannot read.
"""

ERROR_MESSAGES = {
    "unauthorized_scope": "Bạn không có quyền truy cập dữ liệu hoặc thực hiện thao tác này. Hãy kiểm tra vai trò và phạm vi được cấp.",
    "invalid_argument": "Thông tin đầu vào không hợp lệ. Hãy kiểm tra mã chuyến đi (TRIP-YYYY-NNN), mã báo cáo (EXP-YYYY-NNN) và các trường bắt buộc.",
    "not_found": "Không tìm thấy bản ghi trong dữ liệu demo. Hãy kiểm tra lại mã chuyến đi hoặc báo cáo.",
    "not_allowed": "Thao tác này không được phép trong quy trình hiện tại. Hãy chọn chức năng phù hợp với vai trò của bạn.",
    "budget_exceeded": "Quy trình đã hết số bước xử lý cho phép. Hãy thu gọn yêu cầu hoặc nhờ Travel Operations hỗ trợ.",
    "timeout": "Công cụ phản hồi quá thời gian cho phép. Hãy thử lại sau.",
    "unavailable": "Không thể đọc dữ liệu hoặc thực thi công cụ lúc này. Hãy thử lại sau hoặc nhờ người quản trị kiểm tra dữ liệu demo.",
    "policy_access_required": "Vai trò hiện tại không có căn cứ chính sách cần thiết để rà soát chi phí. Hãy nhờ Reviewer hỗ trợ.",
}


def error_text(error: dict) -> str:
    """Render a safe tool error with its diagnostic code for support."""
    code = error.get("code", "unavailable")
    message = error.get("message") or ERROR_MESSAGES.get(code, ERROR_MESSAGES["unavailable"])
    return f"{message}\nMã lỗi: `{code}`."
