"""Structurally disjoint Command admission disposition values."""

from __future__ import annotations

from dataclasses import dataclass

from .envelope import KernelDispositionEnvelope
from .identifiers import ActorId, EventId, MessageId
from .reason_codes import ReasonCode
from .validation import FrozenMap, require_nonempty


@dataclass(frozen=True, slots=True)
class Accepted:
    envelope: KernelDispositionEnvelope
    event_ids: tuple[EventId, ...]
    authorized_next_step: str
    derived_versions: FrozenMap = FrozenMap()

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_ids", tuple(self.event_ids))
        if not self.event_ids:
            raise ValueError("Accepted requires at least one Event")
        require_nonempty(self.authorized_next_step, type(self).__name__, "authorized_next_step")


@dataclass(frozen=True, slots=True)
class Rejected:
    envelope: KernelDispositionEnvelope
    reason_code: ReasonCode
    failed_gate: str
    safe_detail: str

    def __post_init__(self) -> None:
        require_nonempty(self.failed_gate, type(self).__name__, "failed_gate")
        require_nonempty(self.safe_detail, type(self).__name__, "safe_detail")


@dataclass(frozen=True, slots=True)
class PreviouslyAdmitted:
    envelope: KernelDispositionEnvelope
    original_disposition_id: MessageId
    original_event_ids: tuple[EventId, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "original_event_ids", tuple(self.original_event_ids))


@dataclass(frozen=True, slots=True)
class Paused:
    envelope: KernelDispositionEnvelope
    unresolved_conditions: tuple[str, ...]
    review_actor_id: ActorId
    review_condition: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "unresolved_conditions", tuple(self.unresolved_conditions))
        if not self.unresolved_conditions:
            raise ValueError("Paused requires unresolved conditions")
        require_nonempty(self.review_condition, type(self).__name__, "review_condition")


@dataclass(frozen=True, slots=True)
class Escalated:
    envelope: KernelDispositionEnvelope
    unresolved_conditions: tuple[str, ...]
    eligible_actor_ids: tuple[ActorId, ...]
    decision_sought: str
    safe_default: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "unresolved_conditions", tuple(self.unresolved_conditions))
        object.__setattr__(self, "eligible_actor_ids", tuple(self.eligible_actor_ids))
        if not self.unresolved_conditions or not self.eligible_actor_ids:
            raise ValueError("Escalated requires conditions and an eligible route")
        require_nonempty(self.decision_sought, type(self).__name__, "decision_sought")
        require_nonempty(self.safe_default, type(self).__name__, "safe_default")


AdmissionDisposition = Accepted | Rejected | PreviouslyAdmitted | Paused | Escalated
