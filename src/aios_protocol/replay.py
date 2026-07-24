"""Effect-prohibited replay control and report contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .envelope import ReplayControlEnvelope, ReplayReportEnvelope, TrafficMode
from .identifiers import (
    CheckpointId, IntegrityReference, ProjectionId, StreamId,
)
from .reason_codes import ReasonCode
from .validation import FrozenMap
from .versions import PolicyVersionReference, SpecificationVersion


@dataclass(frozen=True, slots=True)
class ReplayRequest:
    envelope: ReplayControlEnvelope
    stream_id: StreamId
    first_position: int
    last_position: int
    specification_versions: tuple[SpecificationVersion, ...]
    policy_versions: tuple[PolicyVersionReference, ...]
    projection_versions: FrozenMap
    checkpoint_id: CheckpointId | None
    expected_integrity_reference: IntegrityReference

    def __post_init__(self) -> None:
        if self.first_position < 0 or self.last_position < self.first_position:
            raise ValueError("invalid replay range")
        object.__setattr__(self, "specification_versions", tuple(self.specification_versions))
        object.__setattr__(self, "policy_versions", tuple(self.policy_versions))


@dataclass(frozen=True, slots=True)
class ReplayAuthorization:
    request: ReplayRequest
    side_effect_guard_reference: IntegrityReference
    permitted_projection_ids: tuple[ProjectionId, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "permitted_projection_ids", tuple(self.permitted_projection_ids))


@dataclass(frozen=True, slots=True)
class ReplayExecutionDescriptor:
    authorization: ReplayAuthorization
    effect_prohibited: bool = True
    traffic_mode: TrafficMode = TrafficMode.REPLAY

    def __post_init__(self) -> None:
        if not self.effect_prohibited or self.traffic_mode is not TrafficMode.REPLAY:
            raise ValueError("replay execution must be effect-prohibited")


@dataclass(frozen=True, slots=True)
class SideEffectCounters:
    tool_calls: int = 0
    external_communications: int = 0
    charges: int = 0
    approval_mutations: int = 0
    resource_mutations: int = 0
    new_authoritative_events: int = 0
    live_deliveries: int = 0

    def __post_init__(self) -> None:
        if any(value != 0 for value in (
            self.tool_calls, self.external_communications, self.charges,
            self.approval_mutations, self.resource_mutations,
            self.new_authoritative_events, self.live_deliveries,
        )):
            raise ValueError("replay report counters must prove zero external side effects")


@dataclass(frozen=True, slots=True)
class ReplayReport:
    envelope: ReplayReportEnvelope
    stream_id: StreamId
    first_position: int
    last_position: int
    applied_event_count: int
    integrity_verified: bool
    reconstructed_projections: tuple[ProjectionId, ...]
    external_reference_limitations: tuple[str, ...]
    side_effect_counters: SideEffectCounters
    zero_effect_evidence_reference: IntegrityReference

    def __post_init__(self) -> None:
        object.__setattr__(self, "reconstructed_projections", tuple(self.reconstructed_projections))
        object.__setattr__(self, "external_reference_limitations", tuple(self.external_reference_limitations))
        if self.applied_event_count < 0:
            raise ValueError("applied Event count cannot be negative")


@dataclass(frozen=True, slots=True)
class ProjectionComparison:
    expected_projection_id: ProjectionId
    actual_projection_id: ProjectionId
    semantically_equivalent: bool
    permitted_metadata_differences: FrozenMap
    first_divergence_position: int | None

    def __post_init__(self) -> None:
        if self.semantically_equivalent and self.first_divergence_position is not None:
            raise ValueError("equivalent projections cannot have a divergence position")


@dataclass(frozen=True, slots=True)
class ReplayIntegrityFailure:
    request: ReplayRequest
    reason_code: ReasonCode
    failed_position: int
    safe_detail: str
