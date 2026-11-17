import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from travel_agent import config
from travel_agent.config import DEFAULT_SESSION_TTL_SECONDS, MEMORY_DIR
from travel_agent.mock_systems import _storage

DATA_DIR = MEMORY_DIR
_DEFAULT_PREFERENCE_DIR = DATA_DIR / "preferences"
_DEFAULT_SESSION_DIR = DATA_DIR / "sessions"
PREFERENCE_DIR = _DEFAULT_PREFERENCE_DIR
SESSION_DIR = _DEFAULT_SESSION_DIR
_USER_ID = re.compile(r"^U-[A-Z]{3}-\d{3}$")
_SESSION_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_PREFERENCE_VALUES = {
    "response_language": {"en", "vi"},
    "preferred_output_format": {"concise", "detailed"},
}
_SESSION_VALUES = {
    "pending_intent": {"trip_details", "itinerary_read"},
    "session_language": {"vi", "en"},
    "last_workflow": {"pretrip", "intrip", "posttrip", "policy_qa"},
    "pending_slot": {"trip_id", "report_id"},
}
_SESSION_KEYS = {"active_trip_id", "active_report_id", *_SESSION_VALUES}


class ScopeError(ValueError):
    """Application context is missing or malformed."""


class ConsentError(ValueError):
    """Persistent preference write was not explicitly authorized by the application."""


# Xác thực ngữ cảnh phiên làm việc và kiểm tra quyền truy cập bộ nhớ
def _scope(user_context: dict[str, Any], *, require_write_consent: bool = False) -> tuple[str, str]:
    # Ngữ cảnh người dùng bắt buộc phải là dictionary
    if not isinstance(user_context, dict):
        raise ScopeError("unauthorized_scope")
    user_id, session_id = user_context.get("user_id"), user_context.get("session_id")
    # Kiểm tra user_id và session_id đúng định dạng và role thuộc nhóm hợp lệ
    if (
        not isinstance(user_id, str) or not _USER_ID.fullmatch(user_id)
        or not isinstance(session_id, str) or not _SESSION_ID.fullmatch(session_id)
        or not isinstance(user_context.get("role"), str)
        or user_context.get("role") not in {"Employee", "Reviewer", "Approver"}
    ):
        raise ScopeError("unauthorized_scope")
    # Ghi nhớ dài hạn bắt buộc có sự đồng thuận tường minh từ ứng dụng
    if require_write_consent and user_context.get("memory_write_authorized") is not True:
        raise ConsentError("not_allowed")
    return user_id, session_id


# Đọc dữ liệu JSON an toàn từ đường dẫn tệp
def _read(path: Path) -> dict[str, Any]:
    # Trả về rỗng nếu tệp dữ liệu chưa tồn tại
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as source:
        value = json.load(source)
    # Dữ liệu đọc lên bắt buộc phải là cấu trúc dictionary
    if not isinstance(value, dict):
        raise ValueError("Memory record is invalid")
    return value


# Ghi dữ liệu nguyên tử (atomic write) qua tệp tạm để tránh hỏng dữ liệu
def _write(path: Path, value: dict[str, Any]) -> None:
    # Đảm bảo thư mục cha tồn tại trước khi ghi tệp
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        # Ghi vào tệp tạm trước khi thay thế tệp đích
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
            json.dump(value, temporary, ensure_ascii=False, indent=2, allow_nan=False)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        # Dọn dẹp tệp tạm thời nếu còn tồn tại
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


# Xác định thư mục lưu trữ tùy chọn người dùng theo môi trường thực thi
def _resolve_pref_dir() -> Path:
    # Ưu tiên thư mục tùy chỉnh nếu đã được thiết lập khác mặc định
    if PREFERENCE_DIR != _DEFAULT_PREFERENCE_DIR:
        return PREFERENCE_DIR
    # Sử dụng thư mục mock data nếu đang chạy trong môi trường kiểm thử
    if _storage._DATA_DIR != config.DATA_DIR:
        return _storage._DATA_DIR / "memory" / "preferences"
    return PREFERENCE_DIR


# Xác định thư mục lưu trữ phiên làm việc theo môi trường thực thi
def _resolve_session_dir() -> Path:
    # Ưu tiên thư mục tùy chỉnh nếu đã được thiết lập khác mặc định
    if SESSION_DIR != _DEFAULT_SESSION_DIR:
        return SESSION_DIR
    # Sử dụng thư mục mock data nếu đang chạy trong môi trường kiểm thử
    if _storage._DATA_DIR != config.DATA_DIR:
        return _storage._DATA_DIR / "memory" / "sessions"
    return SESSION_DIR


# Memory Store (Mục 9.2): Truy xuất danh sách tùy chọn dài hạn của người dùng
def get_preferences(user_context: dict[str, Any]) -> dict[str, str]:
    user_id, _ = _scope(user_context)
    values = _read(_resolve_pref_dir() / f"{user_id}.json")
    # Lọc chỉ giữ các khóa và giá trị tùy chọn đã được chuẩn hóa
    return {
        key: value for key, value in values.items()
        if isinstance(key, str) and key in _PREFERENCE_VALUES
        and isinstance(value, str) and value in _PREFERENCE_VALUES[key]
    }


# Lấy giá trị của một tùy chọn cụ thể từ bộ nhớ dài hạn
def get_preference(user_context: dict[str, Any], key: str) -> str | None:
    # Kiểm tra khóa tùy chọn phải nằm trong danh mục hỗ trợ
    if not isinstance(key, str) or key not in _PREFERENCE_VALUES:
        raise ValueError("invalid_argument")
    return get_preferences(user_context).get(key)


# Memory Store (Mục 9.2): Lưu tùy chọn người dùng lâu dài khi có sự đồng ý tường minh
def set_preference(user_context: dict[str, Any], key: str, value: str) -> dict[str, str]:
    user_id, _ = _scope(user_context, require_write_consent=True)
    # Kiểm tra tính hợp lệ của khóa và giá trị tùy chọn
    if not isinstance(key, str) or key not in _PREFERENCE_VALUES or not isinstance(value, str) or value not in _PREFERENCE_VALUES[key]:
        raise ValueError("invalid_argument")
    values = get_preferences(user_context)
    values[key] = value
    # Ghi nhận thay đổi vào tệp hồ sơ cá nhân
    _write(_resolve_pref_dir() / f"{user_id}.json", values)
    return {"key": key, "value": value}


# Memory Store (Mục 9.2): Xóa tùy chọn đã lưu của người dùng
def delete_preference(user_context: dict[str, Any], key: str) -> bool:
    user_id, _ = _scope(user_context, require_write_consent=True)
    # Kiểm tra khóa tùy chọn cần xóa phải hợp lệ
    if not isinstance(key, str) or key not in _PREFERENCE_VALUES:
        raise ValueError("invalid_argument")
    values = get_preferences(user_context)
    existed = key in values
    values.pop(key, None)
    path = _resolve_pref_dir() / f"{user_id}.json"
    # Cập nhật tệp nếu còn tùy chọn khác, ngược lại xóa tệp rỗng
    if values:
        _write(path, values)
    else:
        path.unlink(missing_ok=True)
    return existed


# Tạo đường dẫn tệp trạng thái phiên theo user_id và session_id
def _session_path(user_id: str, session_id: str) -> Path:
    return _resolve_session_dir() / user_id / f"{session_id}.json"


# Memory Store (Mục 9.2): Truy xuất trạng thái phiên hội thoại ngắn hạn theo TTL
def get_session_state(user_context: dict[str, Any]) -> dict[str, str]:
    user_id, session_id = _scope(user_context)
    path = _session_path(user_id, session_id)
    values = _read(path)
    expires_at = values.get("_expires_at")
    # Tự động hủy phiên và trả về rỗng nếu đã vượt quá thời hạn TTL
    if isinstance(expires_at, (int, float)) and expires_at < time.time():
        path.unlink(missing_ok=True)
        return {}
    # Lọc chỉ trả về các khóa trạng thái được phép trong phiên
    return {
        key: value for key, value in values.items()
        if key in _SESSION_KEYS and isinstance(value, str)
    }


# Memory Store (Mục 9.2): Lưu giá trị ngữ cảnh gần vào phiên ngắn hạn kèm hạn dùng TTL
def set_session_value(
    user_context: dict[str, Any],
    key: str,
    value: str,
    *,
    ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
) -> None:
    user_id, session_id = _scope(user_context)
    # Tham số key và value bắt buộc phải là chuỗi ký tự
    if not isinstance(key, str) or not isinstance(value, str):
        raise ValueError("invalid_argument")
    # Kiểm tra định dạng mã TRIP-ID
    if key == "active_trip_id":
        if not re.fullmatch(r"TRIP-\d{4}-\d{3}", value):
            raise ValueError("invalid_argument")
    # Kiểm tra định dạng mã EXP-ID
    elif key == "active_report_id":
        if not re.fullmatch(r"EXP-\d{4}-\d{3}", value):
            raise ValueError("invalid_argument")
    # Kiểm tra giá trị thuộc danh mục quy ước phiên
    elif key in _SESSION_VALUES and value in _SESSION_VALUES[key]:
        pass
    else:
        raise ValueError("invalid_argument")
    values = dict(get_session_state(user_context))
    values[key] = value
    # Thiết lập thời điểm hết hạn mới dựa trên TTL
    values["_expires_at"] = time.time() + max(1, ttl_seconds)
    _write(_session_path(user_id, session_id), values)


# Xóa một khóa cụ thể khỏi phiên làm việc hiện tại
def delete_session_value(user_context: dict[str, Any], key: str) -> None:
    user_id, session_id = _scope(user_context)
    # Khóa cần xóa phải thuộc danh mục khóa phiên cho phép
    if key not in _SESSION_KEYS:
        raise ValueError("invalid_argument")
    values = dict(get_session_state(user_context))
    # Bỏ qua nếu khóa không tồn tại trong phiên
    if key not in values:
        return
    values.pop(key, None)
    path = _session_path(user_id, session_id)
    # Cập nhật tệp với TTL mới nếu còn giá trị, xóa tệp nếu phiên rỗng
    if values:
        values["_expires_at"] = int(time.time()) + DEFAULT_SESSION_TTL_SECONDS
        _write(path, values)
    else:
        path.unlink(missing_ok=True)


# Xóa sạch toàn bộ trạng thái phiên làm việc hiện tại
def clear_session(user_context: dict[str, Any]) -> None:
    user_id, session_id = _scope(user_context)
    # Hủy tệp phiên làm việc trên ổ đĩa
    _session_path(user_id, session_id).unlink(missing_ok=True)
