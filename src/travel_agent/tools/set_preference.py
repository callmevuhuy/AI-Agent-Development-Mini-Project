from typing import Any

from travel_agent.memory import set_preference
from travel_agent.tools._memory import execute


def run(arguments: dict[str, Any], *, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
    return execute(set_preference, arguments, user_context, read_only=False)
