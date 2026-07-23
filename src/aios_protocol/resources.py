"""Independent Resource dimension and state-transition records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .commands import ResourceDimension, ResourceEstimate
from .identifiers import AuditRecordId, CommandId, IntegrityReference, MessageId, ResourceId
from .reason_codes import ReasonCode
from .validation import require_nonempty, require_nonnegative, require_positive


@dataclass(frozen=True, slots=True)
class ResourceQuantity:
    resource_id: ResourceId
    dimension: ResourceDimension
    amount: int | float
    unit: str

    def __post_init__(self) -> None:
        require_nonnegative(self.amount, type(self).__name__, "amount")
        require_nonempty(self.unit, type(self).__name__, "unit")


@dataclass(frozen=True, slots=True)
class ReservationRequest:
    message_id: MessageId
    command_id: CommandId
    quantities: tuple[ResourceQuantity, ...]
    aggregation_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantities", tuple(self.quantities))
        object.__setattr__(self, "aggregation_keys", tuple(self.aggregation_keys))
        if not self.quantities:
            raise ValueError("reservation requires at least one Resource dimension")
        if len({q.dimension for q in self.quantities}) != len(self.quantities):
            raise ValueError("Resource dimensions must remain independently represented")


@dataclass(frozen=True, slots=True)
class ReservationAccepted:
    request_id: MessageId
    reservation_id: MessageId
    quantities: tuple[ResourceQuantity, ...]
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantities", tuple(self.quantities))


@dataclass(frozen=True, slots=True)
class ReservationRejected:
    request_id: MessageId
    reason_code: ReasonCode
    limiting_dimension: ResourceDimension


@dataclass(frozen=True, slots=True)
class ConsumptionObservation:
    reservation_id: MessageId
    quantities: tuple[ResourceQuantity, ...]
    evidence_reference: IntegrityReference
    uncertainty: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantities", tuple(self.quantities))


@dataclass(frozen=True, slots=True)
class ConsumptionVerified:
    observation_id: MessageId
    quantities: tuple[ResourceQuantity, ...]
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantities", tuple(self.quantities))


@dataclass(frozen=True, slots=True)
class ReservationRelease:
    reservation_id: MessageId
    released: tuple[ResourceQuantity, ...]
    evidence_reference: IntegrityReference

    def __post_init__(self) -> None:
        object.__setattr__(self, "released", tuple(self.released))


@dataclass(frozen=True, slots=True)
class UncertainConsumption:
    reservation_id: MessageId
    safe_held: tuple[ResourceQuantity, ...]
    evidence_references: tuple[IntegrityReference, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "safe_held", tuple(self.safe_held))
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))


@dataclass(frozen=True, slots=True)
class ReconciliationAdjustment:
    reservation_id: MessageId
    adjustment: tuple[ResourceQuantity, ...]
    evidence_references: tuple[IntegrityReference, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "adjustment", tuple(self.adjustment))
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))


@dataclass(frozen=True, slots=True)
class ResourceLimitReached:
    resource_id: ResourceId
    dimension: ResourceDimension
    limit: int | float
    observed: int | float

    def __post_init__(self) -> None:
        require_nonnegative(self.limit, type(self).__name__, "limit")
        require_nonnegative(self.observed, type(self).__name__, "observed")


@dataclass(frozen=True, slots=True)
class ResourceStopConditionTriggered:
    limit_record_id: MessageId
    affected_references: tuple[str, ...]
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        object.__setattr__(self, "affected_references", tuple(self.affected_references))
