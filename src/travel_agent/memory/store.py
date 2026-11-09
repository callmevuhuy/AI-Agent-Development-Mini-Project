import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "memory"
PREFERENCE_DIR = DATA_DIR / "preferences"
SESSION_DIR = DATA_DIR / "sessions"
_USER_ID = re.compile(r"^U-[A-Z]{3}-\d{3}$")
_SESSION_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_PREFERENCE_VALUES = {
    "response_language": {"en", "vi"},
    "preferred_output_format": {"concise", "detailed"},
}
_SESSION_VALUES = {"last_workflow": {"pretrip", "intrip", "posttrip"}}
_SESSION_KEYS = {"active_trip_id", *_SESSION_VALUES}


class ScopeError(ValueError):
    """Application context is missing or malformed."""


class ConsentError(ValueError):
    """Persistent preference write was not explicitly authorized by the application."""


def _scope(user_context: dict[str, Any], *, require_write_consent: bool = False) -> tuple[str, str]:
    if not isinstance(user_context, dict):
        raise ScopeError("unauthorized_scope")
    user_id, session_id = user_context.get("user_id"), user_context.get("session_id")
    if (
        not isinstance(user_id, str) or not _USER_ID.fullmatch(user_id)
        or not isinstance(session_id, str) or not _SESSION_ID.fullmatch(session_id)
        or not isinstance(user_context.get("role"), str)
        or user_context.get("role") not in {"Employee", "Reviewer", "Approver"}
    ):
        raise ScopeError("unauthorized_scope")
    if require_write_consent and user_context.get("memory_write_authorized") is not True:
        raise ConsentError("not_allowed")
    return user_id, session_id


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as source:
        value = json.load(source)
    if not isinstance(value, dict):
        raise ValueError("Memory record is invalid")
    return value


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
            json.dump(value, temporary, ensure_ascii=False, indent=2, allow_nan=False)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def get_preferences(user_context: dict[str, Any]) -> dict[str, str]:
    user_id, _ = _scope(user_context)
    values = _read(PREFERENCE_DIR / f"{user_id}.json")
    return {
        key: value for key, value in values.items()
        if isinstance(key, str) and key in _PREFERENCE_VALUES
        and isinstance(value, str) and value in _PREFERENCE_VALUES[key]
    }


def get_preference(user_context: dict[str, Any], key: str) -> str | None:
    if not isinstance(key, str) or key not in _PREFERENCE_VALUES:
        raise ValueError("invalid_argument")
    return get_preferences(user_context).get(key)


def set_preference(user_context: dict[str, Any], key: str, value: str) -> dict[str, str]:
    user_id, _ = _scope(user_context, require_write_consent=True)
    if not isinstance(key, str) or key not in _PREFERENCE_VALUES or not isinstance(value, str) or value not in _PREFERENCE_VALUES[key]:
        raise ValueError("invalid_argument")
    values = get_preferences(user_context)
    values[key] = value
    _write(PREFERENCE_DIR / f"{user_id}.json", values)
    return {"key": key, "value": value}


def delete_preference(user_context: dict[str, Any], key: str) -> bool:
    user_id, _ = _scope(user_context, require_write_consent=True)
    if not isinstance(key, str) or key not in _PREFERENCE_VALUES:
        raise ValueError("invalid_argument")
    values = get_preferences(user_context)
    existed = key in values
    values.pop(key, None)
    path = PREFERENCE_DIR / f"{user_id}.json"
    if values:
        _write(path, values)
    else:
        path.unlink(missing_ok=True)
    return existed


def _session_path(user_id: str, session_id: str) -> Path:
    return SESSION_DIR / user_id / f"{session_id}.json"


def get_session_state(user_context: dict[str, Any]) -> dict[str, str]:
    user_id, session_id = _scope(user_context)
    values = _read(_session_path(user_id, session_id))
    return {key: value for key, value in values.items() if key in _SESSION_KEYS}


def set_session_value(user_context: dict[str, Any], key: str, value: str) -> None:
    user_id, session_id = _scope(user_context)
    if not isinstance(key, str) or not isinstance(value, str):
        raise ValueError("invalid_argument")
    if key == "active_trip_id":
        if not isinstance(value, str) or not re.fullmatch(r"TRIP-\d{4}-\d{3}", value):
            raise ValueError("invalid_argument")
    elif key in _SESSION_VALUES and value in _SESSION_VALUES[key]:
        pass
    else:
        raise ValueError("invalid_argument")
    values = get_session_state(user_context)
    values[key] = value
    _write(_session_path(user_id, session_id), values)


def clear_session(user_context: dict[str, Any]) -> None:
    user_id, session_id = _scope(user_context)
    _session_path(user_id, session_id).unlink(missing_ok=True)
