"""Centralized runtime path, budget, and LLM backend configuration for the travel agent."""
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
TOTAL_TURN_MAX_STEPS = 32
DEFAULT_SESSION_TTL_SECONDS = 1800

DEFAULT_LLM_BACKEND = "rule"
SUPPORTED_LLM_BACKENDS = frozenset({"rule", "gemini"})
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_TIMEOUT = 15.0


def get_demo_today() -> date:
    """Return reference 'today' date (overridable via TRAVEL_AGENT_DEMO_TODAY=YYYY-MM-DD)."""
    raw = os.environ.get("TRAVEL_AGENT_DEMO_TODAY", "").strip()
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError:
            pass
    return date.today()


def get_llm_backend(override: str | None = None) -> str:
    """Return active LLM backend ('rule' or 'gemini'), defaulting to 'rule'."""
    raw = (override if override is not None else os.environ.get("TRAVEL_AGENT_LLM_BACKEND", DEFAULT_LLM_BACKEND)).strip().lower()
    return raw if raw in SUPPORTED_LLM_BACKENDS else DEFAULT_LLM_BACKEND


def get_gemini_api_key() -> str | None:
    """Read GEMINI_API_KEY strictly from environment variables (never log or persist)."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    return key or None


def get_gemini_model(override: str | None = None) -> str:
    """Return configured Gemini model identifier."""
    raw = (override if override is not None else os.environ.get("TRAVEL_AGENT_GEMINI_MODEL", DEFAULT_GEMINI_MODEL)).strip()
    return raw or DEFAULT_GEMINI_MODEL


def get_gemini_timeout() -> float:
    """Return clamped Gemini API timeout in seconds."""
    raw = os.environ.get("TRAVEL_AGENT_GEMINI_TIMEOUT", "").strip()
    if raw:
        try:
            value = float(raw)
            return max(1.0, min(60.0, value))
        except ValueError:
            pass
    return DEFAULT_GEMINI_TIMEOUT
