"""Approval snapshots and monotonic use records, explicitly not Authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .identifiers import (
    ActorId, ApprovalId, ApprovalUseId, AuditRecordId, CommandId, DecisionId,
)
from .validation import FrozenMap, require_aware, require_nonnegative, require_positive


class ApprovalMode(str, Enum):
    SINGLE_USE = "single_use"
    BOUNDED_REPEAT = "bounded_repeat"
    STANDING = "standing"


class RevocationState(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class ApprovalReference:
    approval_id: ApprovalId
    decision_id: DecisionId
    mode: ApprovalMode
    permitted_scope: FrozenMap
    effective_at: datetime
    expires_at: datetime
    revocation_state: RevocationState
    current_usage: int
    maximum_usage: int | None
    conditions: tuple[str, ...]
    revocation_triggers: tuple[str, ...]
    review_schedule: str | None = None

    def __post_init__(self) -> None:
        require_aware(self.effective_at, type(self).__name__, "effective_at")
        require_aware(self.expires_at, type(self).__name__, "expires_at")
        if self.expires_at <= self.effective_at:
            raise ValueError("Approval expiry must follow effective time")
        require_nonnegative(self.current_usage, type(self).__name__, "current_usage")
        object.__setattr__(self, "conditions", tuple(self.conditions))
        object.__setattr__(self, "revocation_triggers", tuple(self.revocation_triggers))
        if self.mode is ApprovalMode.SINGLE_USE and self.maximum_usage != 1:
            raise ValueError("single-use Approval maximum must be one")
        if self.mode is ApprovalMode.BOUNDED_REPEAT:
            if self.maximum_usage is None or self.maximum_usage <= 1:
                raise ValueError("bounded-repeat maximum must be greater than one")
        if self.mode is ApprovalMode.STANDING and not self.review_schedule:
            raise ValueError("standing Approval requires review schedule")
        if self.maximum_usage is not None and self.current_usage > self.maximum_usage:
            raise ValueError("current usage cannot exceed maximum")


@dataclass(frozen=True, slots=True)
class ApprovalUseValidation:
    approval: ApprovalReference
    command_id: CommandId
    evaluated_at: datetime
    authority_checked_separately: bool
    conditions: FrozenMap
    valid_for_use: bool

    def __post_init__(self) -> None:
        require_aware(self.evaluated_at, type(self).__name__, "evaluated_at")
        if not self.authority_checked_separately:
            raise ValueError("Approval validation cannot stand in for Authority")


@dataclass(frozen=True, slots=True)
class ApprovalUseRecord:
    approval_use_id: ApprovalUseId
    approval_id: ApprovalId
    command_id: CommandId
    prior_usage: int
    next_usage: int
    exact_scope: FrozenMap
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        require_nonnegative(self.prior_usage, type(self).__name__, "prior_usage")
        if self.next_usage != self.prior_usage + 1:
            raise ValueError("Approval usage record must increment monotonically by one")
