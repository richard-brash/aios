"""The only behaviorally supported operation definition: CreateTask."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from aios_protocol.commands import CommandSubmission, DutyWorkRoot, GoalWorkRoot
from aios_protocol.validation import require_nonempty

CREATE_TASK = "CreateTask"

class InitialTaskState(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"; ASSIGNED = "assigned"; ACTIVE = "active"; PAUSED = "paused"
    COMPLETED = "completed"; CANCELLED = "cancelled"; FAILED = "failed"

@dataclass(frozen=True, slots=True)
class CreateTaskCommand:
    submission: CommandSubmission
    proposed_task_id: str
    title: str
    purpose: str
    initial_state: InitialTaskState
    expected_stream_position: int

    def __post_init__(self) -> None:
        for name in ("proposed_task_id", "title", "purpose"):
            require_nonempty(getattr(self, name), type(self).__name__, name)
        if self.expected_stream_position < 0:
            raise ValueError("expected stream position cannot be negative")

    @property
    def work_root(self): return self.submission.work_root
