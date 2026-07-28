"""Deterministic CreateTask capability for the ordinary kernel runtime."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from aios_protocol.commands import DutyWorkRoot, EntityReference, GoalWorkRoot
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import RecordTypeVersion
from aios_protocol.validation import require_nonempty

from .runtime import (
    DomainEventProposal, HandlerAccepted, HandlerContext, HandlerRejected,
    RuntimeCommand,
)

CREATE_TASK = "CreateTask"

class InitialTaskState(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"; ASSIGNED = "assigned"; ACTIVE = "active"; PAUSED = "paused"
    COMPLETED = "completed"; CANCELLED = "cancelled"; FAILED = "failed"

@dataclass(frozen=True, slots=True)
class CreateTaskCommand(RuntimeCommand):
    proposed_task_id: str
    title: str
    purpose: str
    initial_state: InitialTaskState
    def __post_init__(self) -> None:
        super(CreateTaskCommand, self).__post_init__()
        for name in ("proposed_task_id", "title", "purpose"):
            require_nonempty(getattr(self, name), type(self).__name__, name)
        if self.expected_stream_position < 0:
            raise ValueError("expected stream position cannot be negative")

    @property
    def work_root(self): return self.submission.work_root


CREATE_TASK_VERSION = RecordTypeVersion("1.0")


class CreateTaskHandler:
    """Pure CreateTask domain handler; admission and governance stay in the runtime."""

    operation_type = CREATE_TASK
    operation_version = CREATE_TASK_VERSION

    def validate(self, command: RuntimeCommand):
        if type(command) is not CreateTaskCommand:
            return HandlerRejected(
                ReasonCode.INPUT_MALFORMED, "CreateTask command is malformed")
        return None

    def handle(self, context: HandlerContext):
        command = context.command
        if type(command) is not CreateTaskCommand:
            return HandlerRejected(
                ReasonCode.INPUT_MALFORMED, "CreateTask command is malformed")
        if command.initial_state is not InitialTaskState.PROPOSED:
            return HandlerRejected(
                ReasonCode.LIFECYCLE_INVALID_TRANSITION,
                "initial Task state must be proposed")
        if command.submission.decision_reference is None:
            return HandlerRejected(
                ReasonCode.DECISION_MISSING, "CreateTask requires a Decision")
        if type(command.work_root) not in (GoalWorkRoot, DutyWorkRoot):
            return HandlerRejected(
                ReasonCode.WORK_ROOT_MISSING, "CreateTask requires one Work Root")
        if any(
            event.event_type == "TaskCreated" and
            event.payload.get("task_id") == command.proposed_task_id
            for event in context.prior_events
        ):
            return HandlerRejected(
                ReasonCode.LIFECYCLE_INVALID_TRANSITION,
                "Task identity already exists")

        task_reference = EntityReference("Task", command.proposed_task_id, 1)
        common = FrozenMap({
            "task_id": command.proposed_task_id,
            "decision_id": command.submission.decision_reference,
        })
        return HandlerAccepted((
            DomainEventProposal(
                "TaskCreated", CREATE_TASK_VERSION,
                FrozenMap({
                    **dict(common),
                    "title": command.title,
                    "purpose": command.purpose,
                    "lifecycle_state": InitialTaskState.PROPOSED.value,
                    "entity_version": 1,
                }),
                FrozenMap({"task_id": command.proposed_task_id}),
                (task_reference,), command.work_root,
            ),
            DomainEventProposal(
                "DecisionLinked", CREATE_TASK_VERSION, common,
                entity_references=(task_reference,), work_root=command.work_root,
            ),
            DomainEventProposal(
                "WorkRootLinked", CREATE_TASK_VERSION, common,
                entity_references=(task_reference,), work_root=command.work_root,
            ),
        ), FrozenMap({"task_id": command.proposed_task_id, "entity_version": 1}))
