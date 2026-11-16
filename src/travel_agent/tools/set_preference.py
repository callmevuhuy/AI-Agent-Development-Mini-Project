from typing import Any

from travel_agent.memory import set_preference
from travel_agent.tools._memory import execute


# Tool Memory (Mục 9.2): Lưu tùy chọn người dùng khi có sự đồng ý tường minh.
def run(arguments: dict[str, Any], *, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
    return execute(set_preference, arguments, user_context, read_only=False)
