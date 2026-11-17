from typing import Any

from travel_agent.dispatcher import dispatch
from travel_agent.state import RunState
from travel_agent.tools._result import failure
from travel_agent.trace import record_tool_event


MAX_TOOL_RETRIES = 2


# Orchestrator (Mục 7.1, 9.1, 12): Thực thi tool có quản lý ngân sách bước gọi, giới hạn retry và ghi nhận safe trace.
def run_tool(
    state: RunState,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    max_retries: int = MAX_TOOL_RETRIES,
) -> dict[str, Any]:
    if isinstance(max_retries, bool) or not isinstance(max_retries, int) or not 0 <= max_retries <= MAX_TOOL_RETRIES:
        raise ValueError("max_retries must be between 0 and 2")
    if state.outcome is not None:
        return failure("not_allowed", "Quy trình đã kết thúc nên không thể gọi thêm công cụ. Hãy gửi yêu cầu mới.")

    retries = 0
    while True:
        if state.step_count >= state.max_steps:
            result = failure("budget_exceeded", "Quy trình đã hết số bước gọi công cụ cho phép. Hãy thu gọn yêu cầu hoặc nhờ Travel Operations hỗ trợ.")
            record_tool_event(state, tool_name, arguments, result, "budget_exhausted", executed=False)
            state.finish("failed_budget")
            return result

        state.step_count += 1
        result = dispatch(
            tool_name,
            arguments,
            state.workflow,
            state.user_context,
            steps_used=state.step_count - 1,
            max_steps=state.max_steps,
            run_id=state.run_id,
        )
        error = result.get("error", {}) if isinstance(result, dict) else {}
        should_retry = error.get("retryable") is True and retries < max_retries
        transition = "retry_scheduled" if should_retry else ("tool_succeeded" if result.get("ok") else "tool_failed")
        record_tool_event(state, tool_name, arguments, result, transition)
        if not should_retry:
            return result
        retries += 1
