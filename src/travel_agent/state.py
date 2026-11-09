from dataclasses import dataclass, field
from copy import deepcopy
from typing import Any
from uuid import uuid4


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
    max_steps: int = 8
    run_id: str = field(default_factory=lambda: str(uuid4()))
    case_id: str | None = None
    step_count: int = 0
    safe_tool_results: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    outcome: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.user_context, dict):
            raise ValueError("user_context must be supplied by the application")
        self.user_context = deepcopy(self.user_context)
        if isinstance(self.max_steps, bool) or not isinstance(self.max_steps, int) or not 1 <= self.max_steps <= 8:
            raise ValueError("max_steps must be between 1 and 8")
        if not isinstance(self.workflow, str) or not isinstance(self.phase, str):
            raise ValueError("workflow and phase must be strings")
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
        if self.case_id is not None:
            started["case_id"] = self.case_id
        self.trace.append(started)

    def finish(self, outcome: str) -> None:
        if outcome not in TERMINAL_OUTCOMES:
            raise ValueError("Invalid terminal outcome")
        if self.outcome is not None:
            if self.outcome != outcome:
                raise ValueError("Run already has a terminal outcome")
            return
        self.outcome = outcome
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
        if self.case_id is not None:
            finished["case_id"] = self.case_id
        self.trace.append(finished)
        for event in self.trace:
            event["outcome"] = outcome

    def set_phase(self, phase: str) -> None:
        if not isinstance(phase, str) or not phase:
            raise ValueError("phase must be a non-empty string")
        self.phase = phase
