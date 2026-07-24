"""Schedule lifecycle and attributable instance materialization records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .commands import WorkRoot
from .identifiers import (
    ActorId, ApprovalId, AuditRecordId, AuthorityGrantId, CommandId,
    DecisionId, IntegrityReference, MessageId, OperationId, ScheduleId,
    ScheduleInstanceId,
)
from .validation import FrozenMap, require_aware, require_nonempty


@dataclass(frozen=True, slots=True)
class ScheduleDefinition:
    schedule_id: ScheduleId
    authorizing_actor_id: ActorId
    decision_id: DecisionId
    work_root: WorkRoot
    authority_references: tuple[AuthorityGrantId, ...]
    approval_references: tuple[ApprovalId, ...]
    trigger_definition: FrozenMap
    resource_bounds: FrozenMap
    catch_up_policy: str
    review_condition: str
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_references", tuple(self.authority_references))
        object.__setattr__(self, "approval_references", tuple(self.approval_references))
        require_nonempty(self.catch_up_policy, type(self).__name__, "catch_up_policy")
        require_nonempty(self.review_condition, type(self).__name__, "review_condition")


@dataclass(frozen=True, slots=True)
class ScheduleActivation:
    schedule_id: ScheduleId
    command_id: CommandId
    effective_at: datetime

    def __post_init__(self) -> None:
        require_aware(self.effective_at, type(self).__name__, "effective_at")


@dataclass(frozen=True, slots=True)
class ScheduleSuspension:
    schedule_id: ScheduleId
    command_id: CommandId
    reason: str
    effective_at: datetime

    def __post_init__(self) -> None:
        require_nonempty(self.reason, type(self).__name__, "reason")
        require_aware(self.effective_at, type(self).__name__, "effective_at")


@dataclass(frozen=True, slots=True)
class ScheduleCancellation(ScheduleSuspension):
    pass


@dataclass(frozen=True, slots=True)
class ScheduleDueObservation:
    message_id: MessageId
    schedule_id: ScheduleId
    due_identity: OperationId
    observed_at: datetime
    source_reference: IntegrityReference

    def __post_init__(self) -> None:
        require_aware(self.observed_at, type(self).__name__, "observed_at")


@dataclass(frozen=True, slots=True)
class ScheduleInstanceMaterialization:
    schedule_id: ScheduleId
    schedule_instance_id: ScheduleInstanceId
    command_id: CommandId
    original_operation_id: OperationId
    initiating_actor_id: ActorId
    decision_id: DecisionId
    work_root: WorkRoot
    authorization_references: tuple[AuthorityGrantId, ...]
    due_observation_id: MessageId

    def __post_init__(self) -> None:
        object.__setattr__(self, "authorization_references", tuple(self.authorization_references))


class MissedDisposition(str, Enum):
    SKIPPED = "skipped"
    PAUSED = "paused"
    ESCALATED = "escalated"
    CATCH_UP_PROPOSED = "catch_up_proposed"


@dataclass(frozen=True, slots=True)
class MissedInstanceDisposition:
    schedule_id: ScheduleId
    due_observation_id: MessageId
    disposition: MissedDisposition
    policy_reference: str
    safe_detail: str


@dataclass(frozen=True, slots=True)
class CatchUpDisposition:
    schedule_id: ScheduleId
    authorized_instance_ids: tuple[ScheduleInstanceId, ...]
    decision_id: DecisionId
    resource_bounds: FrozenMap

    def __post_init__(self) -> None:
        object.__setattr__(self, "authorized_instance_ids", tuple(self.authorized_instance_ids))
        if not self.authorized_instance_ids:
            raise ValueError("catch-up disposition requires bounded instances")
