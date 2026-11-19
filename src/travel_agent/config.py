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
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
SUPPORTED_GEMINI_MODELS = (
    "gemini-3.8-flash",
    "gemini-4-hydrogen",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-4-neon",
    "gemini-2.5-flash-lite",
)
_GEMINI_MODEL_ALIASES = {
    "gemini-flash": "gemini-3.8-flash",
    "gemini-3.8": "gemini-3.8-flash",
    "gemini-hydrogen": "gemini-4-hydrogen",
    "4-hydrogen": "gemini-4-hydrogen",
    "gemini-3.1": "gemini-3.1-flash-lite",
    "3.1-flash": "gemini-3.1-flash-lite",
    "gemini-pro": "gemini-2.5-pro",
}
DEFAULT_GEMINI_TIMEOUT = 35.0


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
    """Return configured Gemini model identifier, normalizing common shorthand aliases."""
    raw = (override if override is not None else os.environ.get("TRAVEL_AGENT_GEMINI_MODEL", DEFAULT_GEMINI_MODEL)).strip()
    if not raw:
        return DEFAULT_GEMINI_MODEL
    return _GEMINI_MODEL_ALIASES.get(raw.lower(), raw)


def get_gemini_timeout() -> float:
    """Return clamped Gemini API timeout in seconds."""
    raw = os.environ.get("TRAVEL_AGENT_GEMINI_TIMEOUT", "").strip()
    if raw:
        try:
            value = float(raw)
            return max(5.0, min(90.0, value))
        except ValueError:
            pass
    return DEFAULT_GEMINI_TIMEOUT
