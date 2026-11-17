import json
from typing import Any, Callable

from travel_agent.memory import ConsentError, ScopeError
from travel_agent.tools._result import failure, success


def execute(operation: Callable[..., Any], arguments: dict[str, Any], user_context: dict[str, Any] | None, *, read_only: bool) -> dict[str, Any]:
    if user_context is None:
        return failure("unauthorized_scope", "Thiếu ngữ cảnh người dùng để truy cập bộ nhớ. Hãy chọn lại tài khoản và phiên làm việc.")
    try:
        data = operation(user_context, **arguments)
    except ScopeError:
        return failure("unauthorized_scope", "Bạn không có quyền truy cập bộ nhớ này. Chỉ được xem tùy chọn trong phạm vi tài khoản và phiên hiện tại.")
    except ConsentError:
        return failure("not_allowed", "Chỉ được lưu hoặc xóa tùy chọn khi bạn yêu cầu rõ ràng. Hãy nêu tùy chọn cần thay đổi.")
    except (OSError, json.JSONDecodeError):
        return failure("unavailable", "Không truy cập được nơi lưu bộ nhớ. Hãy thử lại sau hoặc nhờ người quản trị kiểm tra.", retryable=True)
    except ValueError as error:
        code = str(error) if str(error) in {"invalid_argument", "unauthorized_scope"} else "invalid_argument"
        return failure(code, "Tùy chọn bộ nhớ không hợp lệ. Hãy kiểm tra tên tùy chọn và giá trị được hỗ trợ.")
    return success(data, "mock_user_memory", read_only=read_only)
