"""Institutional-memory admission and governed retrieval structures only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .identifiers import ActorId, AuditRecordId, IntegrityReference, MemoryRecordId, OrganizationId
from .presence import Presence
from .reason_codes import ReasonCode
from .validation import FrozenMap, require_aware, require_nonempty


@dataclass(frozen=True, slots=True)
class EvidenceSubmission:
    organization_id: OrganizationId
    submitting_actor_id: ActorId
    evidence_reference: IntegrityReference
    provenance: FrozenMap
    classification: str
    observed_at: datetime

    def __post_init__(self) -> None:
        require_nonempty(self.classification, type(self).__name__, "classification")
        require_aware(self.observed_at, type(self).__name__, "observed_at")


@dataclass(frozen=True, slots=True)
class ClaimProposal:
    claim_reference: IntegrityReference
    evidence_references: tuple[IntegrityReference, ...]
    confidence: float | None
    validity_condition: str
    proposed_classification: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))
        if not self.evidence_references:
            raise ValueError("Claim requires evidence")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between zero and one")
        require_nonempty(self.validity_condition, type(self).__name__, "validity_condition")


@dataclass(frozen=True, slots=True)
class MemoryAdmissionRequest:
    proposed_memory_id: MemoryRecordId
    submitting_actor_id: ActorId
    claims: tuple[ClaimProposal, ...]
    provenance: FrozenMap
    purpose: str
    classification: str
    retention: FrozenMap
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        object.__setattr__(self, "claims", tuple(self.claims))
        if not self.claims:
            raise ValueError("Memory admission requires at least one Claim")


class MemoryAdmissionStatus(str, Enum):
    ADMITTED = "admitted"
    REJECTED = "rejected"
    PAUSED = "paused"


@dataclass(frozen=True, slots=True)
class MemoryAdmissionDisposition:
    memory_record_id: MemoryRecordId
    status: MemoryAdmissionStatus
    audit_record_id: AuditRecordId
    reason_code: ReasonCode | None = None

    def __post_init__(self) -> None:
        if (self.status is MemoryAdmissionStatus.REJECTED) != (self.reason_code is not None):
            raise ValueError("only rejected admission requires a reason code")


@dataclass(frozen=True, slots=True)
class MemoryRetrievalRequest:
    organization_id: OrganizationId
    requesting_actor_id: ActorId
    purpose: str
    classification_ceiling: str
    query_reference: IntegrityReference


@dataclass(frozen=True, slots=True)
class RetrievedMemory:
    memory_record_id: MemoryRecordId
    content: Presence[object]
    provenance: FrozenMap
    classification: str
    validity: Presence[object]
    confidence: Presence[object]
    conflict_references: tuple[MemoryRecordId, ...]
    superseded_by: MemoryRecordId | None
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        object.__setattr__(self, "conflict_references", tuple(self.conflict_references))


@dataclass(frozen=True, slots=True)
class MemoryRetrievalResponse:
    request: MemoryRetrievalRequest
    purpose: str
    records: tuple[RetrievedMemory, ...]
    disclosure_audit_id: AuditRecordId

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))
        if self.purpose != self.request.purpose:
            raise ValueError("retrieval response cannot broaden purpose")


@dataclass(frozen=True, slots=True)
class MemoryDisclosureRecord:
    memory_record_id: MemoryRecordId
    recipient_actor_id: ActorId
    purpose: str
    disclosed_fields: frozenset[str]
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        object.__setattr__(self, "disclosed_fields", frozenset(self.disclosed_fields))


@dataclass(frozen=True, slots=True)
class MemorySupersession:
    prior_memory_id: MemoryRecordId
    successor_memory_id: MemoryRecordId
    evidence_reference: IntegrityReference

    def __post_init__(self) -> None:
        if self.prior_memory_id == self.successor_memory_id:
            raise ValueError("Memory Record cannot supersede itself")


@dataclass(frozen=True, slots=True)
class MemoryConflictMarking:
    memory_record_ids: tuple[MemoryRecordId, ...]
    evidence_references: tuple[IntegrityReference, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "memory_record_ids", tuple(self.memory_record_ids))
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))
        if len(set(self.memory_record_ids)) < 2:
            raise ValueError("conflict requires at least two Memory Records")


@dataclass(frozen=True, slots=True)
class MemoryRedaction:
    memory_record_id: MemoryRecordId
    tombstone_reference: IntegrityReference
    retained_audit_id: AuditRecordId


@dataclass(frozen=True, slots=True)
class MemoryDeletionRequest:
    memory_record_id: MemoryRecordId
    requesting_actor_id: ActorId
    legal_basis_reference: IntegrityReference


@dataclass(frozen=True, slots=True)
class MemoryLegalHold:
    memory_record_id: MemoryRecordId
    hold_reference: IntegrityReference
    review_condition: str


@dataclass(frozen=True, slots=True)
class MemoryTombstone:
    memory_record_id: MemoryRecordId
    provenance_reference: IntegrityReference
    audit_record_id: AuditRecordId
    classification: str
