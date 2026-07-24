"""Reconciliation requests and uncertainty-preserving dispositions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .identifiers import (
    ActorId, ApprovalUseId, AttemptId, AuditRecordId, CommandId, DispatchId,
    IntegrityReference, MessageId, OperationId, ResourceId,
)
from .validation import FrozenMap, require_aware


@dataclass(frozen=True, slots=True)
class ReconciliationRequest:
    message_id: MessageId
    command_id: CommandId
    operation_id: OperationId
    dispatch_id: DispatchId | None
    attempt_id: AttemptId | None
    causal_observations: tuple[IntegrityReference, ...]
    expected_result: FrozenMap
    resource_ids: tuple[ResourceId, ...]
    approval_use_ids: tuple[ApprovalUseId, ...]
    deadline: datetime
    accountable_actor_id: ActorId

    def __post_init__(self) -> None:
        object.__setattr__(self, "causal_observations", tuple(self.causal_observations))
        object.__setattr__(self, "resource_ids", tuple(self.resource_ids))
        object.__setattr__(self, "approval_use_ids", tuple(self.approval_use_ids))
        require_aware(self.deadline, type(self).__name__, "deadline")


class ReconciliationState(str, Enum):
    VERIFIED = "verified"
    FAILED = "failed"
    PARTIAL = "partial"
    DUPLICATED = "duplicated"
    COMPENSATED = "compensated"
    DISPUTED = "disputed"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class ReconciliationDisposition:
    request_id: MessageId
    state: ReconciliationState
    evidence_references: tuple[IntegrityReference, ...]
    projection_effects: FrozenMap
    resource_effects: FrozenMap
    approval_usage_decrement: int
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))
        if self.approval_usage_decrement != 0:
            raise ValueError("reconciliation cannot decrement Approval usage")
        if self.state is ReconciliationState.VERIFIED and not self.evidence_references:
            raise ValueError("verified reconciliation requires evidence")
