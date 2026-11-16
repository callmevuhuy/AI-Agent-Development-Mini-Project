"""Centralized runtime path and budget configuration for the travel agent."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("TRAVEL_AGENT_DATA_DIR", ROOT_DIR / "data"))
DRAFT_DIR = Path(os.environ.get("TRAVEL_AGENT_DRAFT_DIR", DATA_DIR / "drafts"))
MEMORY_DIR = Path(os.environ.get("TRAVEL_AGENT_MEMORY_DIR", DATA_DIR / "memory"))
LOG_DIR = Path(os.environ.get("TRAVEL_AGENT_LOG_DIR", DATA_DIR / "logs"))

DEFAULT_MAX_STEPS = 8
MAX_ALLOWED_STEPS = 12
DEFAULT_SESSION_TTL_SECONDS = 1800


def get_demo_today() -> date:
    """Return reference 'today' date (overridable via TRAVEL_AGENT_DEMO_TODAY=YYYY-MM-DD)."""
    raw = os.environ.get("TRAVEL_AGENT_DEMO_TODAY", "").strip()
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError:
            pass
    return date.today()
