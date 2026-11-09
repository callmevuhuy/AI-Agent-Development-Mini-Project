from typing import Any


def success(data: Any, source: str, read_only: bool = True) -> dict[str, Any]:
    return {"ok": True, "data": data, "meta": {"source": source, "read_only": read_only}}


def failure(code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message, "retryable": retryable}}


def record_result(data: Any, source: str) -> dict[str, Any]:
    if data is None:
        return failure("not_found", "The requested mock record was not found.")
    return success(data, source)
