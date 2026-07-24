"""Immutable authoritative and proposed Event contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .commands import EntityReference, WorkRoot
from .envelope import EventEnvelope, TRUSTED_ENVELOPE_KEYS
from .identifiers import ActorId, AuditRecordId, EventId, IntegrityReference
from .presence import Presence, NOT_APPLICABLE
from .validation import FrozenMap, ensure_no_keys, require_aware, require_nonempty, require_type
from .versions import RecordTypeVersion


class EpistemicStatus(str, Enum):
    DETERMINISTIC = "deterministic"
    OBSERVED = "observed"
    ASSERTED = "asserted"
    INFERRED = "inferred"
    PREDICTED = "predicted"
    DISPUTED = "disputed"


class ToolKnowledgeStage(str, Enum):
    NONE = "none"
    AUTHORIZED = "authorized"
    DISPATCHED = "dispatched"
    ATTEMPTED = "attempted"
    OBSERVED = "observed"
    INTERPRETED = "interpreted"
    RECONCILING = "reconciling"
    VERIFIED = "verified"


def _validate_confidence(status: EpistemicStatus, confidence: Presence[float], record: str) -> None:
    from .presence import Known, NotApplicable
    if status is EpistemicStatus.DETERMINISTIC and not isinstance(confidence, NotApplicable):
        raise ValueError(f"{record}: deterministic Event confidence must be not applicable")
    required = {EpistemicStatus.INFERRED, EpistemicStatus.PREDICTED, EpistemicStatus.DISPUTED}
    if status in required and not isinstance(confidence, Known):
        raise ValueError(f"{record}: epistemic status requires known confidence")
    if isinstance(confidence, Known):
        if isinstance(confidence.value, bool) or not isinstance(confidence.value, (int, float)):
            raise TypeError("confidence must be numeric")
        if not 0 <= confidence.value <= 1:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class ProposedEvent:
    event_id: EventId
    event_type: str
    event_version: RecordTypeVersion
    initiating_actor_id: ActorId
    participant_actor_ids: tuple[ActorId, ...]
    causal_reference: str | None
    epistemic_status: EpistemicStatus
    confidence: Presence[float] = NOT_APPLICABLE
    payload: FrozenMap = field(default_factory=FrozenMap)

    def __post_init__(self) -> None:
        require_type(self.event_id, EventId, type(self).__name__, "event_id")
        require_nonempty(self.event_type, type(self).__name__, "event_type")
        object.__setattr__(self, "participant_actor_ids", tuple(self.participant_actor_ids))
        ensure_no_keys(self.payload, TRUSTED_ENVELOPE_KEYS, type(self).__name__)
        _validate_confidence(self.epistemic_status, self.confidence, type(self).__name__)


@dataclass(frozen=True, slots=True)
class EventRecord:
    envelope: EventEnvelope
    event_id: EventId
    event_type: str
    event_version: RecordTypeVersion
    participant_actor_ids: tuple[ActorId, ...]
    causal_reference: str | None
    occurred_at: datetime | None
    entity_references: tuple[EntityReference, ...]
    epistemic_status: EpistemicStatus
    confidence: Presence[float]
    work_root: WorkRoot | None
    projection_effects: FrozenMap
    resource_effects: FrozenMap
    approval_use_effects: FrozenMap
    audit_record_id: AuditRecordId
    integrity_reference: IntegrityReference
    tool_knowledge_stage: ToolKnowledgeStage = ToolKnowledgeStage.NONE
    result: str = "recorded"
    payload: FrozenMap = field(default_factory=FrozenMap)
    corrects_event_id: EventId | None = None
    supersedes_event_id: EventId | None = None
    redaction_reference: IntegrityReference | None = None
    tombstones_event_id: EventId | None = None

    def __post_init__(self) -> None:
        require_type(self.event_id, EventId, type(self).__name__, "event_id")
        require_nonempty(self.event_type, type(self).__name__, "event_type")
        require_nonempty(self.result, type(self).__name__, "result")
        object.__setattr__(self, "participant_actor_ids", tuple(self.participant_actor_ids))
        object.__setattr__(self, "entity_references", tuple(self.entity_references))
        if self.occurred_at is not None:
            require_aware(self.occurred_at, type(self).__name__, "occurred_at")
        ensure_no_keys(self.payload, TRUSTED_ENVELOPE_KEYS | {"event_id", "event_type"}, type(self).__name__)
        _validate_confidence(self.epistemic_status, self.confidence, type(self).__name__)
        for name in ("corrects_event_id", "supersedes_event_id", "tombstones_event_id"):
            reference = getattr(self, name)
            if reference == self.event_id:
                raise ValueError(f"Event cannot {name.removesuffix('_event_id')} itself")
        if self.tool_knowledge_stage is ToolKnowledgeStage.ATTEMPTED and self.result in {"verified", "succeeded", "completed"}:
            raise ValueError("Tool attempt cannot claim verified outcome")
