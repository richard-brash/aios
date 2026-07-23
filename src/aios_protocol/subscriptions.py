"""Organization- and classification-bound subscription records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .envelope import LiveDeliveryEnvelope
from .identifiers import (
    ActorId, AuthorityGrantId, DeliveryId, EventId, IntegrityReference,
    MessageId, OrganizationId, SubscriptionId,
)
from .reason_codes import ReasonCode
from .validation import FrozenMap, require_nonempty
from .versions import RecordTypeVersion


@dataclass(frozen=True, slots=True)
class SubscriptionScope:
    event_types: frozenset[str]
    classification_ceiling: str
    purpose: str
    filter_type: str
    filter_version: RecordTypeVersion
    filter_parameters: FrozenMap = FrozenMap()

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_types", frozenset(self.event_types))
        if not self.event_types:
            raise ValueError("subscription requires Event-type scope")
        for name in ("classification_ceiling", "purpose", "filter_type"):
            require_nonempty(getattr(self, name), type(self).__name__, name)

    def contains(self, requested: "SubscriptionScope") -> bool:
        return (
            requested.event_types <= self.event_types
            and requested.classification_ceiling == self.classification_ceiling
            and requested.purpose == self.purpose
            and requested.filter_type == self.filter_type
            and requested.filter_version == self.filter_version
            and requested.filter_parameters == self.filter_parameters
        )


@dataclass(frozen=True, slots=True)
class SubscriptionRequest:
    message_id: MessageId
    subscription_id: SubscriptionId
    organization_id: OrganizationId
    subscriber_actor_id: ActorId
    scope: SubscriptionScope
    authority_references: tuple[AuthorityGrantId, ...]
    starting_cursor: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_references", tuple(self.authority_references))
        if self.starting_cursor < 0:
            raise ValueError("starting cursor cannot be negative")


@dataclass(frozen=True, slots=True)
class AcceptedSubscription:
    request_id: MessageId
    subscription_id: SubscriptionId
    organization_id: OrganizationId
    subscriber_actor_id: ActorId
    accepted_scope: SubscriptionScope
    starting_cursor: int

    def validate_delivery_scope(self, requested_scope: SubscriptionScope) -> None:
        if not self.accepted_scope.contains(requested_scope):
            raise ValueError("subscriber filter cannot expand accepted scope")


@dataclass(frozen=True, slots=True)
class EventDelivery:
    envelope: LiveDeliveryEnvelope
    delivery_id: DeliveryId
    subscription_id: SubscriptionId
    event_id: EventId
    event_stream_position: int
    filter_version: RecordTypeVersion
    payload_reference: IntegrityReference
    delivery_attempt: int = 1

    def __post_init__(self) -> None:
        if self.event_stream_position <= 0 or self.delivery_attempt <= 0:
            raise ValueError("delivery position and attempt must be positive")


@dataclass(frozen=True, slots=True)
class EventRedelivery:
    original_delivery_id: DeliveryId
    event_id: EventId
    delivery_attempt: int

    def __post_init__(self) -> None:
        if self.delivery_attempt <= 1:
            raise ValueError("redelivery attempt must exceed one")


class AcknowledgmentDisposition(str, Enum):
    PROCESSED = "processed"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass(frozen=True, slots=True)
class DeliveryAcknowledgment:
    delivery_id: DeliveryId
    subscriber_actor_id: ActorId
    event_id: EventId
    event_stream_position: int
    disposition: AcknowledgmentDisposition
    proposed_checkpoint: int | None = None


@dataclass(frozen=True, slots=True)
class SubscriptionRejected:
    request_id: MessageId
    reason_code: ReasonCode
    safe_cursor: int


@dataclass(frozen=True, slots=True)
class SubscriptionSuspended:
    subscription_id: SubscriptionId
    reason_code: ReasonCode
    safe_cursor: int


@dataclass(frozen=True, slots=True)
class CursorCheckpoint:
    subscription_id: SubscriptionId
    subscriber_actor_id: ActorId
    event_stream_position: int
    integrity_reference: IntegrityReference

    def __post_init__(self) -> None:
        if self.event_stream_position < 0:
            raise ValueError("checkpoint cannot be negative")
