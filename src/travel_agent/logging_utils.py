"""UTF-8 BOM CSV conversation and staff handoff logger."""
from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from travel_agent import config
from travel_agent.mock_systems import _storage

_DEFAULT_LOG_DIR = config.LOG_DIR
LOG_DIR = _DEFAULT_LOG_DIR
_LOG_LOCK = Lock()

_CARD_LIKE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_SECRET_LIKE = re.compile(r"\b(?:sk-[A-Za-z0-9]{10,}|Bearer\s+[A-Za-z0-9._-]{10,})\b", re.IGNORECASE)

CHAT_COLUMNS = [
    "timestamp_utc",
    "session_id",
    "user_id",
    "role",
    "route",
    "intent",
    "workflow",
    "record_id",
    "outcome",
    "handoff_required",
    "handoff_id",
    "handoff_reason",
    "user_message",
    "bot_response",
    "citations",
    "run_id",
    "step_count",
]

HANDOFF_COLUMNS = [
    "handoff_id",
    "created_at_utc",
    "status",
    "session_id",
    "user_id",
    "role",
    "intent",
    "trip_id",
    "report_id",
    "outcome",
    "handoff_reason",
    "verified_facts_summary",
    "citations",
    "user_message",
    "run_id",
]


def _resolve_log_dir() -> Path:
    if LOG_DIR != _DEFAULT_LOG_DIR:
        return LOG_DIR
    if _storage._DATA_DIR != config.DATA_DIR:
        return _storage._DATA_DIR / "logs"
    return LOG_DIR


def _redact_sensitive(text: str) -> str:
    if not isinstance(text, str):
        return ""
    cleaned = _SECRET_LIKE.sub("[REDACTED_SECRET]", text)
    return _CARD_LIKE.sub("[REDACTED_NUMBER]", cleaned)


def _append_csv_row(path: Path, columns: list[str], row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8-sig" if not exists else "utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        if not exists:
            writer.writeheader()
        writer.writerow({col: row.get(col, "") for col in columns})


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def log_chat_turn(
    *,
    session_id: str,
    user_id: str,
    role: str,
    route: str,
    intent: str,
    workflow: str | None,
    record_id: str | None,
    outcome: str,
    handoff_required: bool,
    handoff_id: str | None,
    handoff_reason: str,
    user_message: str,
    bot_response: str,
    citations: list[str] | None,
    run_id: str,
    step_count: int,
    verified_facts_summary: str = "",
    trip_id: str | None = None,
    report_id: str | None = None,
) -> dict[str, Path]:
    """Append a conversation turn to chat_history.csv and, if escalated, to handoff_queue.csv."""
    now = datetime.now(timezone.utc).isoformat()
    citation_str = " | ".join(dict.fromkeys(citations or []))
    safe_user_msg = _redact_sensitive(user_message)
    safe_bot_msg = _redact_sensitive(bot_response)

    log_dir = _resolve_log_dir()
    chat_path = log_dir / "chat_history.csv"
    handoff_path = log_dir / "handoff_queue.csv"

    with _LOG_LOCK:
        _append_csv_row(chat_path, CHAT_COLUMNS, {
            "timestamp_utc": now,
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "route": route,
            "intent": intent,
            "workflow": workflow or "",
            "record_id": record_id or "",
            "outcome": outcome,
            "handoff_required": "true" if handoff_required else "false",
            "handoff_id": handoff_id or "",
            "handoff_reason": handoff_reason,
            "user_message": safe_user_msg,
            "bot_response": safe_bot_msg,
            "citations": citation_str,
            "run_id": run_id,
            "step_count": step_count,
        })
        if handoff_required and handoff_id:
            _append_csv_row(handoff_path, HANDOFF_COLUMNS, {
                "handoff_id": handoff_id,
                "created_at_utc": now,
                "status": "open",
                "session_id": session_id,
                "user_id": user_id,
                "role": role,
                "intent": intent,
                "trip_id": trip_id or "",
                "report_id": report_id or "",
                "outcome": outcome,
                "handoff_reason": handoff_reason,
                "verified_facts_summary": verified_facts_summary,
                "citations": citation_str,
                "user_message": safe_user_msg,
                "run_id": run_id,
            })
    return {"chat_history": chat_path, "handoff_queue": handoff_path}


def read_chat_history(*, limit: int | None = None) -> list[dict[str, str]]:
    with _LOG_LOCK:
        rows = _read_csv(_resolve_log_dir() / "chat_history.csv")
    return rows[-limit:] if limit and limit > 0 else rows


def read_handoff_queue(*, status: str | None = None) -> list[dict[str, str]]:
    with _LOG_LOCK:
        rows = _read_csv(_resolve_log_dir() / "handoff_queue.csv")
    if status:
        return [row for row in rows if row.get("status") == status]
    return rows


def clear_all_logs() -> None:
    """Delete chat history and handoff queue CSV files."""
    log_dir = _resolve_log_dir()
    with _LOG_LOCK:
        for name in ("chat_history.csv", "handoff_queue.csv"):
            (log_dir / name).unlink(missing_ok=True)
