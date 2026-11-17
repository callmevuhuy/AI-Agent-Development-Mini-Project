import inspect
import json
from typing import Any

from jsonschema import Draft202012Validator

from travel_agent.config import DEFAULT_MAX_STEPS, MAX_ALLOWED_STEPS
from travel_agent.errors import scope_error, tool_role_error
from travel_agent.mock_systems.approval import get_approval_request
from travel_agent.mock_systems.expense import get_expense_report
from travel_agent.mock_systems.trip import get_trip_request
from travel_agent.mock_systems.user import get_user
from travel_agent.registry import TOOL_REGISTRY, WORKFLOW_ALLOWLISTS
from travel_agent.tools._result import failure


_TRIP_TOOLS = {"get_trip_request", "get_itinerary", "get_approval_status"}
_EXPENSE_TOOLS = {"get_expense_report", "calculate_expense_summary"}
_TRIP_DRAFT_TOOLS = {"create_travel_checklist_draft", "create_escalation_or_support_draft"}
_EXPENSE_DRAFT_TOOLS = {"create_expense_review_draft"}
_MEMORY_TOOLS = {"get_preference", "set_preference", "delete_preference"}
_APPROVER_READS = {
    "checklist_review": {"get_trip_request", "get_approval_status"},
    "escalation": {"get_itinerary"},
    "publish_request": {"get_trip_request", "get_approval_status"},
}
_APPROVER_RAG_CATEGORIES = {
    "checklist_review": {"approval", "travel", "visa", "insurance"},
    "escalation": {"travel"},
    "publish_request": {"approval"},
}
_ADMIN_TOOLS = {"admin_list_trips", "admin_get_audit_history"}
_RAG_ROLES = {"Employee", "Reviewer", "Approver"}


# Trả về lỗi khi yêu cầu vượt ngoài phạm vi ủy quyền của người dùng
def _scope_error(message: str = "Ngữ cảnh người dùng không hợp lệ. Hãy chọn lại tài khoản demo và phiên làm việc.") -> dict[str, Any]:
    return failure("unauthorized_scope", message)


# Dispatcher Authorization (Mục 12): Kiểm tra ủy quyền truy xuất dữ liệu theo đúng vai trò và phạm vi người dùng
def _authorize(tool_name: str, arguments: dict[str, Any], user_context: dict[str, Any]) -> dict[str, Any] | None:
    user_id = user_context.get("user_id")
    user = get_user(user_id) if isinstance(user_id, str) else None
    if (not user or user_context.get("role") != user["role"]
            or not isinstance(user_context.get("session_id"), str) or not user_context["session_id"]):
        return _scope_error()
    role = user["role"]
    if role == "Admin":
        return None if tool_name in _ADMIN_TOOLS else tool_role_error(role, tool_name)
    if tool_name in _ADMIN_TOOLS:
        return tool_role_error(role, tool_name)
    if tool_name == "request_approval":
        if role != "Employee":
            return tool_role_error(role, tool_name)
        trip = get_trip_request(arguments.get("trip_id", ""))
        if not trip or trip.get("traveler_id") != user.get("traveler_id"):
            return scope_error()
    if tool_name in _MEMORY_TOOLS:
        if tool_name in {"set_preference", "delete_preference"} and user_context.get("memory_write_authorized") is not True:
            return failure("not_allowed", "Chỉ được lưu hoặc xóa tùy chọn khi bạn yêu cầu rõ ràng. Hãy nêu tùy chọn cần thay đổi.")
        return None
    if role == "Approver":
        if tool_name != "search_travel_policy" and tool_name not in _TRIP_TOOLS:
            return tool_role_error(role, tool_name)
        scope = user_context.get("approval_scope")
        if (not isinstance(scope, dict) or set(scope) != {"trip_id", "action_type"}
                or not isinstance(scope.get("action_type"), str) or scope["action_type"] not in _APPROVER_READS):
            return scope_error("Chưa có phạm vi phê duyệt hợp lệ. Hãy chọn yêu cầu đang chờ trong mục Phạm vi phê duyệt.")
        request = get_approval_request(scope["trip_id"], scope["action_type"])
        if not request or request.get("status") != "pending":
            return scope_error("Phạm vi phê duyệt không còn hiệu lực hoặc không có yêu cầu đang chờ. Hãy chọn lại yêu cầu pending được cấp.")
        if tool_name == "search_travel_policy":
            if arguments.get("category") not in _APPROVER_RAG_CATEGORIES[scope["action_type"]]:
                return scope_error()
        elif arguments.get("trip_id") != scope["trip_id"]:
            return scope_error()
        elif tool_name not in _APPROVER_READS[scope["action_type"]]:
            return tool_role_error(role, tool_name)
        return None
    if tool_name == "search_travel_policy":
        return None if role in _RAG_ROLES else scope_error()
    if role == "Reviewer":
        return None
    if role != "Employee":
        return scope_error()
    traveler_id = user.get("traveler_id")
    if tool_name in _TRIP_TOOLS | _TRIP_DRAFT_TOOLS | {"validate_trip_requirements", "request_approval"}:
        trip_id = arguments.get("trip_id") or arguments.get("trip_facts", {}).get("trip_id")
        trip = get_trip_request(trip_id) if trip_id else None
        if trip is not None and trip["traveler_id"] != traveler_id:
            return scope_error()
    elif tool_name in _EXPENSE_TOOLS | _EXPENSE_DRAFT_TOOLS:
        report = get_expense_report(arguments["report_id"])
        if report is not None and report["traveler_id"] != traveler_id:
            return scope_error()
    elif tool_name == "get_traveler_profile" and arguments["traveler_id"] != traveler_id:
        return scope_error()
    return None


# Function Calling (Mục 7.3): Kiểm định cấu trúc kết quả trả về tuân thủ đúng hợp đồng {ok, data, meta} hoặc error
def _valid_result(result: Any) -> bool:
    # Kết quả bắt buộc phải là một dictionary và có trường boolean 'ok'
    if not isinstance(result, dict) or not isinstance(result.get("ok"), bool):
        return False
        
    # Trường hợp công cụ thực thi thành công: bắt buộc có 'data' và metadata hợp lệ
    if result["ok"]:
        meta = result.get("meta")
        return (
            "data" in result
            and isinstance(meta, dict)
            and isinstance(meta.get("source"), str)
            and isinstance(meta.get("read_only"), bool)
        )
        
    # Trường hợp công cụ gặp lỗi: bắt buộc có object 'error' chứa thông tin lỗi chuẩn
    error = result.get("error")
    return (
        isinstance(error, dict)
        and isinstance(error.get("code"), str)
        and isinstance(error.get("message"), str)
        and isinstance(error.get("retryable"), bool)
    )


# Dispatcher (Mục 7.1, 12): Trung tâm điều phối thực thi tool an toàn qua các lớp kiểm soát
def dispatch(
    tool_name: str,
    arguments: dict[str, Any],
    workflow: str,
    user_context: dict[str, Any],
    *,
    steps_used: int = 0,
    max_steps: int = DEFAULT_MAX_STEPS,
    run_id: str = "direct-dispatch",
) -> dict[str, Any]:
    # Tên tool và tên workflow bắt buộc phải là chuỗi ký tự
    if not isinstance(tool_name, str) or not isinstance(workflow, str):
        return failure("not_allowed", "Công cụ không được phép chạy trong workflow hiện tại. Hãy chọn tác vụ phù hợp.")
        
    # Kiểm tra tool đã được đăng ký trong hệ thống
    spec = TOOL_REGISTRY.get(tool_name)
    if spec is None:
        return failure("not_allowed", "Công cụ chưa được đăng ký trong hệ thống. Hãy sử dụng chức năng được hỗ trợ.")
        
    # Tool phải thuộc allowlist của workflow hiện tại theo nguyên tắc đặc quyền tối thiểu
    if tool_name not in WORKFLOW_ALLOWLISTS.get(workflow, frozenset()):
        return failure("not_allowed", "Công cụ không được phép chạy trong workflow hiện tại. Hãy chọn tác vụ phù hợp.")
        
    # Kiểm định tham số đầu vào bằng JSON Schema chuẩn
    if not isinstance(arguments, dict) or not Draft202012Validator(spec.schema).is_valid(arguments):
        return failure("invalid_argument", "Tham số công cụ không hợp lệ. Hãy kiểm tra định dạng ID, các trường bắt buộc và giá trị được hỗ trợ.")
        
    # Ngữ cảnh người dùng bắt buộc phải là dictionary
    if not isinstance(user_context, dict):
        return _scope_error()
        
    # Thực hiện kiểm tra ủy quyền (RBAC & Attribute-based Scope)
    try:
        denied = _authorize(tool_name, arguments, user_context)
    except (OSError, json.JSONDecodeError):
        return failure("unavailable", "Không đọc được dữ liệu phân quyền demo. Hãy thử lại sau hoặc nhờ người quản trị kiểm tra dữ liệu.", retryable=True)
    except Exception:
        return failure("unavailable", "Không thể xác minh quyền truy cập. Yêu cầu đã dừng; hãy chọn lại tài khoản hoặc nhờ người quản trị hỗ trợ.")
        
    # Dừng ngay nếu bị từ chối ủy quyền
    if denied:
        return denied
        
    # Kiểm tra ngân sách bước gọi công cụ (step budget) còn lại
    if (
        isinstance(steps_used, bool)
        or isinstance(max_steps, bool)
        or not isinstance(steps_used, int)
        or not isinstance(max_steps, int)
        or max_steps < 1
        or max_steps > MAX_ALLOWED_STEPS
        or steps_used < 0
        or steps_used >= max_steps
    ):
        return failure("budget_exceeded", "Quy trình đã hết số bước gọi công cụ cho phép. Hãy thu gọn yêu cầu hoặc nhờ Travel Operations hỗ trợ.")
        
    # Tự động phát hiện tham số handler hỗ trợ và thực thi an toàn
    try:
        params = inspect.signature(spec.handler).parameters
        kwargs: dict[str, Any] = {}
        # Bổ sung user_context nếu handler yêu cầu tham số này
        if "user_context" in params:
            kwargs["user_context"] = user_context
        # Bổ sung run_id nếu handler yêu cầu (cho vết kiểm toán và idempotency)
        if "run_id" in params:
            kwargs["run_id"] = run_id

        try:
            result = spec.handler(arguments, **kwargs)
        except TypeError as ex:
            # Fallback nếu handler là mock đơn giản chỉ nhận arguments
            if "unexpected keyword argument" in str(ex):
                result = spec.handler(arguments)
            else:
                raise
    except (OSError, json.JSONDecodeError):
        return failure("unavailable", "Không đọc được dữ liệu demo. Hãy thử lại sau hoặc nhờ người quản trị kiểm tra dữ liệu.", retryable=True)
    except Exception:
        return failure("unavailable", "Công cụ demo gặp lỗi và đã dừng. Hãy thử lại sau hoặc nhờ người quản trị kiểm tra.")
        
    # Kiểm định hợp đồng kết quả đầu ra
    if not _valid_result(result):
        return failure("unavailable", "Công cụ demo trả về kết quả không đúng cấu trúc. Hãy nhờ người quản trị kiểm tra công cụ.")
        
    return result
