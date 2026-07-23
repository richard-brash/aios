"""Disjoint Tool-boundary knowledge records; no Tool execution occurs here."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .commands import WorkRoot
from .envelope import AdapterObservationEnvelope, TrafficMode
from .identifiers import (
    ActorId, ApprovalUseId, AttemptId, AuditRecordId, CommandId, DeliveryId,
    DispatchId, ExternalOperationId, IntegrityReference, OperationId,
    ResourceId, ToolId,
)
from .presence import Presence, NOT_YET_KNOWN
from .validation import FrozenMap, require_aware, require_nonempty, require_type
from .versions import RecordTypeVersion


@dataclass(frozen=True, slots=True)
class AuthorizedToolScope:
    tool_id: ToolId
    operation_type: str
    operation_version: RecordTypeVersion
    bounded_inputs: FrozenMap
    result_contract: FrozenMap

    def __post_init__(self) -> None:
        require_type(self.tool_id, ToolId, type(self).__name__, "tool_id")
        require_nonempty(self.operation_type, type(self).__name__, "operation_type")


@dataclass(frozen=True, slots=True)
class ToolDispatchIntent:
    command_id: CommandId
    operation_id: OperationId
    dispatch_id: DispatchId
    adapter_actor_id: ActorId
    scope: AuthorizedToolScope
    work_root: WorkRoot
    request_integrity_reference: IntegrityReference
    resource_reservation_ids: tuple[ResourceId, ...]
    approval_use_ids: tuple[ApprovalUseId, ...]
    audit_record_id: AuditRecordId
    traffic_mode: TrafficMode = TrafficMode.LIVE

    def __post_init__(self) -> None:
        if self.traffic_mode is not TrafficMode.LIVE:
            raise ValueError("replay-originated Tool dispatch is prohibited")
        object.__setattr__(self, "resource_reservation_ids", tuple(self.resource_reservation_ids))
        object.__setattr__(self, "approval_use_ids", tuple(self.approval_use_ids))


class ReceiptDisposition(str, Enum):
    RECEIVED = "received"
    REJECTED_FOR_EXECUTION = "rejected_for_execution"


@dataclass(frozen=True, slots=True)
class AdapterReceipt:
    envelope: AdapterObservationEnvelope
    delivery_id: DeliveryId
    dispatch_id: DispatchId
    disposition: ReceiptDisposition
    safe_detail: str

    def __post_init__(self) -> None:
        require_nonempty(self.safe_detail, type(self).__name__, "safe_detail")


@dataclass(frozen=True, slots=True)
class ToolExecutionAttempt:
    envelope: AdapterObservationEnvelope
    operation_id: OperationId
    dispatch_id: DispatchId
    attempt_id: AttemptId
    scope: AuthorizedToolScope
    request_integrity_reference: IntegrityReference
    external_operation_id: Presence[ExternalOperationId] = NOT_YET_KNOWN
    resource_measurements: FrozenMap = field(default_factory=FrozenMap)
    uncertainty: str = "unknown_until_observed"

    def __post_init__(self) -> None:
        require_nonempty(self.uncertainty, type(self).__name__, "uncertainty")


@dataclass(frozen=True, slots=True)
class ExternalResponseObservation:
    envelope: AdapterObservationEnvelope
    operation_id: OperationId
    dispatch_id: DispatchId
    attempt_id: AttemptId
    external_operation_id: Presence[ExternalOperationId]
    response_reference: IntegrityReference
    response_integrity_reference: IntegrityReference
    resource_measurements: FrozenMap = field(default_factory=FrozenMap)
    contradictory_evidence: tuple[IntegrityReference, ...] = ()
    uncertainty: str = "observed_not_verified"

    def __post_init__(self) -> None:
        object.__setattr__(self, "contradictory_evidence", tuple(self.contradictory_evidence))
        require_nonempty(self.uncertainty, type(self).__name__, "uncertainty")


@dataclass(frozen=True, slots=True)
class AdapterInterpretation:
    envelope: AdapterObservationEnvelope
    operation_id: OperationId
    dispatch_id: DispatchId
    attempt_id: AttemptId
    interpreted_result: str
    evidence_references: tuple[IntegrityReference, ...]
    confidence: float | None
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        require_nonempty(self.interpreted_result, type(self).__name__, "interpreted_result")
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class VerifiedToolOutcome:
    command_id: CommandId
    operation_id: OperationId
    dispatch_id: DispatchId
    attempt_id: AttemptId
    verified_result: str
    result_criteria_version: RecordTypeVersion
    evidence_references: tuple[IntegrityReference, ...]
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        require_nonempty(self.verified_result, type(self).__name__, "verified_result")
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))
        if not self.evidence_references:
            raise ValueError("verified outcome requires evidence")
