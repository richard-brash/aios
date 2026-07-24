"""Atomic Event append proposal and certainty-preserving results."""

from __future__ import annotations

from dataclasses import dataclass

from .events import ProposedEvent
from .identifiers import AuditRecordId, MessageId, OrganizationId, StreamId
from .reason_codes import ReasonCode
from .validation import FrozenMap


@dataclass(frozen=True, slots=True)
class EventAppendBatch:
    message_id: MessageId
    organization_id: OrganizationId
    stream_id: StreamId
    expected_prior_position: int
    ordered_events: tuple[ProposedEvent, ...]
    projection_preconditions: FrozenMap = FrozenMap()
    resource_transitions: tuple[object, ...] = ()
    approval_use_transitions: tuple[object, ...] = ()
    dispatch_intents: tuple[object, ...] = ()
    audit_references: tuple[AuditRecordId, ...] = ()

    def __post_init__(self) -> None:
        if self.expected_prior_position < 0:
            raise ValueError("expected prior position cannot be negative")
        object.__setattr__(self, "ordered_events", tuple(self.ordered_events))
        object.__setattr__(self, "resource_transitions", tuple(self.resource_transitions))
        object.__setattr__(self, "approval_use_transitions", tuple(self.approval_use_transitions))
        object.__setattr__(self, "dispatch_intents", tuple(self.dispatch_intents))
        object.__setattr__(self, "audit_references", tuple(self.audit_references))
        if not self.ordered_events:
            raise ValueError("append batch requires ordered Events")


@dataclass(frozen=True, slots=True)
class AppendConfirmed:
    batch_id: MessageId
    first_position: int
    last_position: int

    def __post_init__(self) -> None:
        if self.first_position <= 0 or self.last_position < self.first_position:
            raise ValueError("invalid confirmed position range")


@dataclass(frozen=True, slots=True)
class AppendConcurrencyConflict:
    batch_id: MessageId
    expected_position: int
    current_position: int


@dataclass(frozen=True, slots=True)
class AppendValidationFailure:
    batch_id: MessageId
    reason_code: ReasonCode
    safe_detail: str


@dataclass(frozen=True, slots=True)
class AppendFailure:
    batch_id: MessageId
    reason_code: ReasonCode
    confirmed_nonappend: bool = True


@dataclass(frozen=True, slots=True)
class AppendOutcomeUncertain:
    batch_id: MessageId
    reason_code: ReasonCode
    reconciliation_required: bool = True


AppendResult = AppendConfirmed | AppendConcurrencyConflict | AppendValidationFailure | AppendFailure | AppendOutcomeUncertain
