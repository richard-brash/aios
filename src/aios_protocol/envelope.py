"""Narrow logical envelopes with explicit field ownership."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .identifiers import (
    ActorId, AuditRecordId, CommandId, CorrelationId, IntegrityReference,
    MessageId, OrganizationId, StreamId,
)
from .validation import EMPTY_MAP, FrozenMap, ensure_no_keys, require_aware, require_nonempty, require_type
from .versions import PayloadVersion, RecordTypeVersion, RECORD_V1


class FieldSource(str, Enum):
    CALLER_ASSERTED = "caller_asserted"
    TRANSPORT_OBSERVED = "transport_observed"
    KERNEL_SUPPLIED = "kernel_supplied"
    EVENT_STORE_SUPPLIED = "event_store_supplied"
    ADAPTER_SUPPLIED = "adapter_supplied"
    SUBSCRIBER_SUPPLIED = "subscriber_supplied"
    REPLAY_CONTROLLER_SUPPLIED = "replay_controller_supplied"


class TrafficMode(str, Enum):
    LIVE = "live"
    REPLAY = "replay"
    PRE_ORGANIZATION = "pre_organization"
    PLATFORM_SECURITY = "platform_security"


TRUSTED_ENVELOPE_KEYS = frozenset({
    "message_id", "message_type", "schema_version", "organization_id",
    "initiating_actor_id", "recording_command_id", "correlation_id",
    "evaluation_time", "stream_id", "stream_position", "classification",
    "work_root", "authority_references", "policy_references",
    "decision_reference", "approval_references", "resource_references",
    "audit_reference", "integrity_reference", "traffic_mode",
})


@dataclass(frozen=True, slots=True)
class CallerEnvelope:
    message_id: MessageId
    message_type: str
    organization_id: OrganizationId
    initiating_actor_id: ActorId
    correlation_id: CorrelationId
    issued_at: datetime
    classification: str
    purpose: str
    payload_type: str
    payload_version: PayloadVersion
    payload: FrozenMap = field(default_factory=FrozenMap)
    schema_version: RecordTypeVersion = RECORD_V1
    traffic_mode: TrafficMode = TrafficMode.LIVE

    def __post_init__(self) -> None:
        require_type(self.message_id, MessageId, type(self).__name__, "message_id")
        require_type(self.organization_id, OrganizationId, type(self).__name__, "organization_id")
        require_type(self.initiating_actor_id, ActorId, type(self).__name__, "initiating_actor_id")
        require_type(self.correlation_id, CorrelationId, type(self).__name__, "correlation_id")
        require_aware(self.issued_at, type(self).__name__, "issued_at")
        for name in ("message_type", "classification", "purpose", "payload_type"):
            require_nonempty(getattr(self, name), type(self).__name__, name)
        if self.traffic_mode is not TrafficMode.LIVE:
            raise ValueError("caller operational envelope must be live")
        ensure_no_keys(self.payload, TRUSTED_ENVELOPE_KEYS, type(self).__name__)


@dataclass(frozen=True, slots=True)
class KernelDispositionEnvelope:
    message_id: MessageId
    message_type: str
    organization_id: OrganizationId
    initiating_actor_id: ActorId
    recording_command_id: CommandId
    correlation_id: CorrelationId
    evaluation_time: datetime
    classification: str
    audit_reference: AuditRecordId | None = None
    schema_version: RecordTypeVersion = RECORD_V1
    traffic_mode: TrafficMode = TrafficMode.LIVE

    def __post_init__(self) -> None:
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        require_type(self.recording_command_id, CommandId, type(self).__name__, "recording_command_id")
        if self.traffic_mode is not TrafficMode.LIVE:
            raise ValueError("disposition must be live")


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    message_id: MessageId
    message_type: str
    organization_id: OrganizationId
    initiating_actor_id: ActorId
    recording_command_id: CommandId
    correlation_id: CorrelationId
    evaluation_time: datetime
    stream_id: StreamId
    stream_position: int
    classification: str
    integrity_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1
    traffic_mode: TrafficMode = TrafficMode.LIVE

    def __post_init__(self) -> None:
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        if self.stream_position <= 0:
            raise ValueError("stream_position must be positive")
        if self.traffic_mode is not TrafficMode.LIVE:
            raise ValueError("authoritative Event must be live-recorded")


@dataclass(frozen=True, slots=True)
class LiveDeliveryEnvelope:
    message_id: MessageId
    message_type: str
    organization_id: OrganizationId
    classification: str
    issued_at: datetime
    schema_version: RecordTypeVersion = RECORD_V1
    traffic_mode: TrafficMode = TrafficMode.LIVE

    def __post_init__(self) -> None:
        require_aware(self.issued_at, type(self).__name__, "issued_at")
        if self.traffic_mode is not TrafficMode.LIVE:
            raise ValueError("live delivery cannot use replay mode")


@dataclass(frozen=True, slots=True)
class ReplayControlEnvelope:
    message_id: MessageId
    message_type: str
    organization_id: OrganizationId
    initiating_actor_id: ActorId
    correlation_id: CorrelationId
    issued_at: datetime
    classification: str
    schema_version: RecordTypeVersion = RECORD_V1
    traffic_mode: TrafficMode = TrafficMode.REPLAY

    def __post_init__(self) -> None:
        require_aware(self.issued_at, type(self).__name__, "issued_at")
        if self.traffic_mode is not TrafficMode.REPLAY:
            raise ValueError("replay control must use replay mode")


@dataclass(frozen=True, slots=True)
class ReplayReportEnvelope:
    message_id: MessageId
    message_type: str
    organization_id: OrganizationId
    correlation_id: CorrelationId
    classification: str
    schema_version: RecordTypeVersion = RECORD_V1
    traffic_mode: TrafficMode = TrafficMode.REPLAY

    def __post_init__(self) -> None:
        if self.traffic_mode is not TrafficMode.REPLAY:
            raise ValueError("replay report must use replay mode")


@dataclass(frozen=True, slots=True)
class AdapterObservationEnvelope:
    message_id: MessageId
    message_type: str
    organization_id: OrganizationId
    adapter_actor_id: ActorId
    correlation_id: CorrelationId
    observed_at: datetime
    classification: str
    integrity_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1
    traffic_mode: TrafficMode = TrafficMode.LIVE

    def __post_init__(self) -> None:
        require_aware(self.observed_at, type(self).__name__, "observed_at")
        if self.traffic_mode is not TrafficMode.LIVE:
            raise ValueError("adapter observation must be live")


@dataclass(frozen=True, slots=True)
class BootstrapEnvelope:
    message_id: MessageId
    message_type: str
    correlation_id: CorrelationId
    issued_at: datetime
    classification: str
    schema_version: RecordTypeVersion = RECORD_V1
    traffic_mode: TrafficMode = TrafficMode.PRE_ORGANIZATION

    def __post_init__(self) -> None:
        require_aware(self.issued_at, type(self).__name__, "issued_at")
        if self.traffic_mode is not TrafficMode.PRE_ORGANIZATION:
            raise ValueError("bootstrap envelope must be pre-organization")


FIELD_OWNERSHIP = FrozenMap({
    "issued_at": FieldSource.CALLER_ASSERTED,
    "received_at": FieldSource.TRANSPORT_OBSERVED,
    "evaluation_time": FieldSource.KERNEL_SUPPLIED,
    "stream_id": FieldSource.EVENT_STORE_SUPPLIED,
    "stream_position": FieldSource.EVENT_STORE_SUPPLIED,
    "adapter_observation": FieldSource.ADAPTER_SUPPLIED,
    "subscriber_acknowledgment": FieldSource.SUBSCRIBER_SUPPLIED,
    "replay_mode": FieldSource.REPLAY_CONTROLLER_SUPPLIED,
})
