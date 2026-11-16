from typing import Any

from travel_agent.memory import get_preference
from travel_agent.tools._memory import execute


# Tool Memory (Mục 9.2): Đọc tùy chọn đã lưu của người dùng theo user scope.
def run(arguments: dict[str, Any], *, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
    return execute(get_preference, arguments, user_context, read_only=True)
