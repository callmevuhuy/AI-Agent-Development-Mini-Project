"""Small deterministic planner for repeatable offline demos; no external LLM required."""
import re


_TRIP = re.compile(r"\bTRIP-\d{4}-\d{3}\b", re.IGNORECASE)
_REPORT = re.compile(r"\bEXP-\d{4}-\d{3}\b", re.IGNORECASE)


def plan(message: str) -> dict[str, str] | None:
    if not isinstance(message, str) or len(message) > 1000:
        return None
    text = message.casefold()
    if _REPORT.search(message) and any(word in text for word in ("expense", "report", "chi phí", "chi phi", "hoàn ứng", "hoan ung")):
        return {"workflow": "posttrip", "record_id": _REPORT.search(message).group(0).upper()}
    trip = _TRIP.search(message)
    if not trip:
        return None
    trip_id = trip.group(0).upper()
    if any(word in text for word in ("delay", "cancel", "disruption", "gián đoạn", "delay", "hoãn", "hủy", "huỷ")):
        return {"workflow": "intrip", "record_id": trip_id}
    if any(word in text for word in ("prepare", "pre-trip", "checklist", "compliance", "chuẩn bị", "cần gì", "yêu cầu")):
        return {"workflow": "pretrip", "record_id": trip_id}
    return None
