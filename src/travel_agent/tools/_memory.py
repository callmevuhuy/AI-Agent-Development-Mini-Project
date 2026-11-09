import json
from typing import Any, Callable

from travel_agent.memory import ConsentError, ScopeError
from travel_agent.tools._result import failure, success


def execute(operation: Callable[..., Any], arguments: dict[str, Any], user_context: dict[str, Any] | None, *, read_only: bool) -> dict[str, Any]:
    if user_context is None:
        return failure("unauthorized_scope", "Memory access requires application user context.")
    try:
        data = operation(user_context, **arguments)
    except ScopeError:
        return failure("unauthorized_scope", "Memory access is outside this user's scope.")
    except ConsentError:
        return failure("not_allowed", "Persistent preference changes require an explicit user request.")
    except (OSError, json.JSONDecodeError):
        return failure("unavailable", "Memory storage could not be accessed.", retryable=True)
    except ValueError as error:
        code = str(error) if str(error) in {"invalid_argument", "unauthorized_scope"} else "invalid_argument"
        return failure(code, "Memory arguments are invalid.")
    return success(data, "mock_user_memory", read_only=read_only)
