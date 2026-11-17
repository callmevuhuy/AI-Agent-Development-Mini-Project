from dataclasses import dataclass, field
from copy import deepcopy
from typing import Any
from uuid import uuid4

from travel_agent.config import DEFAULT_MAX_STEPS, MAX_ALLOWED_STEPS


# Danh sách các trạng thái dừng hợp lệ của quy trình (Terminal Outcomes)
TERMINAL_OUTCOMES = frozenset({
    "completed",
    "needs_input",
    "needs_human",
    "awaiting_approval",
    "partial",
    "failed_validation",
    "failed_delivery",
    "failed_budget",
})


@dataclass
class RunState:
    workflow: str
    user_context: dict[str, Any] = field(repr=False)
    phase: str = "tool_execution"
    max_steps: int = DEFAULT_MAX_STEPS
    run_id: str = field(default_factory=lambda: str(uuid4()))
    case_id: str | None = None
    step_count: int = 0
    safe_tool_results: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    outcome: str | None = None

    def __post_init__(self) -> None:
        # Ngữ cảnh người dùng bắt buộc phải do ứng dụng cung cấp dạng dictionary
        if not isinstance(self.user_context, dict):
            raise ValueError("user_context must be supplied by the application")
        # Sao chép sâu user_context để ngăn chặn đột biến ngoài ý muốn
        self.user_context = deepcopy(self.user_context)
        # Giới hạn ngân sách bước (max_steps) phải là số nguyên nằm trong ngưỡng cho phép
        if isinstance(self.max_steps, bool) or not isinstance(self.max_steps, int) or not 1 <= self.max_steps <= MAX_ALLOWED_STEPS:
            raise ValueError(f"max_steps must be between 1 and {MAX_ALLOWED_STEPS}")
        # Tên workflow và tên giai đoạn ban đầu bắt buộc phải là chuỗi ký tự
        if not isinstance(self.workflow, str) or not isinstance(self.phase, str):
            raise ValueError("workflow and phase must be strings")
        # Khởi tạo bản ghi sự kiện bắt đầu lượt thực thi trong trace
        started = {
            "run_id": self.run_id,
            "phase": self.phase,
            "action": "run_started",
            "tool": None,
            "safe_args": {},
            "observation_status": "not_applicable",
            "transition": "started",
            "budget": {"step": 0, "max": self.max_steps},
            "outcome": None,
        }
        # Bổ sung case_id nếu có phục vụ đánh giá kiểm thử tự động
        if self.case_id is not None:
            started["case_id"] = self.case_id
        self.trace.append(started)

    # Workflow State (Mục 9.1): Chốt trạng thái dừng và ghi nhận terminal outcome
    def finish(self, outcome: str) -> None:
        # Kết quả chốt chặn bắt buộc phải thuộc danh mục TERMINAL_OUTCOMES
        if outcome not in TERMINAL_OUTCOMES:
            raise ValueError("Invalid terminal outcome")
        # Không cho phép thay đổi kết quả sau khi quy trình đã chốt trạng thái dừng
        if self.outcome is not None:
            if self.outcome != outcome:
                raise ValueError("Run already has a terminal outcome")
            return
        self.outcome = outcome
        # Ghi nhận sự kiện kết thúc quy trình vào vết thực thi
        finished = {
            "run_id": self.run_id,
            "phase": self.phase,
            "action": "run_finished",
            "tool": None,
            "safe_args": {},
            "observation_status": "not_applicable",
            "transition": "terminal",
            "budget": {"step": self.step_count, "max": self.max_steps},
            "outcome": outcome,
        }
        # Lưu kèm case_id vào sự kiện kết thúc nếu có
        if self.case_id is not None:
            finished["case_id"] = self.case_id
        self.trace.append(finished)
        # Đồng bộ kết quả dừng vào toàn bộ các sự kiện trong vết thực thi
        for event in self.trace:
            event["outcome"] = outcome

    # Workflow State (Mục 9.1): Cập nhật giai đoạn hiện tại của quy trình thực thi
    def set_phase(self, phase: str) -> None:
        # Giai đoạn (phase) phải là chuỗi ký tự không rỗng
        if not isinstance(phase, str) or not phase:
            raise ValueError("phase must be a non-empty string")
        self.phase = phase

    # Workflow Trace (Mục 9.1, 13.3): Ghi nhận sự kiện thực thi an toàn vào danh sách trace
    def record_event(
        self,
        action: str,
        *,
        tool: str | None = None,
        safe_args: dict[str, Any] | None = None,
        observation_status: str = "ok",
        transition: str = "intermediate",
    ) -> None:
        # Tạo cấu trúc sự kiện kiểm toán an toàn tuân thủ hợp đồng hệ thống
        event = {
            "run_id": self.run_id,
            "phase": self.phase,
            "action": action,
            "tool": tool,
            "safe_args": safe_args or {},
            "observation_status": observation_status,
            "transition": transition,
            "budget": {"step": self.step_count, "max": self.max_steps},
            "outcome": self.outcome,
        }
        # Đính kèm mã ca kiểm thử nếu có
        if self.case_id is not None:
            event["case_id"] = self.case_id
        self.trace.append(event)
