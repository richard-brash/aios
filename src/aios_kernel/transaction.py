"""Atomic kernel transaction and certainty-preserving outcomes."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from aios_protocol.dispositions import Accepted, AdmissionDisposition, Rejected
from aios_protocol.events import EventRecord
from aios_protocol.identifiers import AuditRecordId, CommandId, IntegrityReference, OrganizationId, StreamId
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from .gates import GateResult
from .idempotency import IdempotencyRegistration

@dataclass(frozen=True, slots=True)
class AuditRecord:
    audit_record_id: AuditRecordId
    organization_id: OrganizationId
    recording_command_id: CommandId
    evaluation_facts: tuple[GateResult, ...]
    outcome: str
    integrity_reference: IntegrityReference
    def __post_init__(self) -> None:
        object.__setattr__(self, "evaluation_facts", tuple(self.evaluation_facts))

@dataclass(frozen=True, slots=True)
class KernelTransaction:
    organization_id: OrganizationId
    stream_id: StreamId
    expected_prior_position: int
    events: tuple[EventRecord, ...]
    disposition: AdmissionDisposition
    audit_record: AuditRecord
    idempotency_registration: IdempotencyRegistration | None
    task_projection_input: FrozenMap | None
    resource_transitions: tuple[object, ...] = ()
    approval_use_transitions: tuple[object, ...] = ()
    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "resource_transitions", tuple(self.resource_transitions))
        object.__setattr__(self, "approval_use_transitions", tuple(self.approval_use_transitions))

class TransactionStatus(str, Enum):
    CONFIRMED="confirmed"; CONCURRENCY_CONFLICT="concurrency_conflict"; VALIDATION_FAILURE="validation_failure"
    APPEND_FAILURE="append_failure"; OUTCOME_UNCERTAIN="outcome_uncertain"
    PREVIOUSLY_ADMITTED="previously_admitted"; IDEMPOTENCY_CONFLICT="idempotency_conflict"

@dataclass(frozen=True, slots=True)
class TransactionResult:
    status: TransactionStatus
    disposition: AdmissionDisposition | None
    reason_code: ReasonCode | None
    first_position: int | None = None
    last_position: int | None = None
    authoritative_mutation_may_have_occurred: bool = False
    internal_reconciliation_metadata_recorded: bool = False
    external_domain_mutation_may_have_occurred: bool = False
    reconciliation_reference: IntegrityReference | None = None
    def __post_init__(self) -> None:
        if self.status is TransactionStatus.OUTCOME_UNCERTAIN:
            if self.disposition is not None or self.first_position is not None or self.last_position is not None:
                raise ValueError("uncertain append cannot claim disposition or positions")
        if self.status in {TransactionStatus.CONFIRMED, TransactionStatus.PREVIOUSLY_ADMITTED} and self.disposition is None:
            raise ValueError("confirmed transaction requires disposition")
