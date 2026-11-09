"""User-scoped preference and session storage."""

from .store import (
    ConsentError,
    ScopeError,
    clear_session,
    delete_preference,
    get_preference,
    get_preferences,
    get_session_state,
    set_preference,
    set_session_value,
)

__all__ = [
    "ConsentError", "ScopeError", "clear_session", "delete_preference", "get_preference", "get_preferences",
    "get_session_state", "set_preference", "set_session_value",
]
