"""Semantic CreateTask identity and Organization/Actor-scoped idempotency contracts."""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import math
from collections.abc import Mapping

from aios_protocol.identifiers import ActorId, Identifier, IntegrityReference, MessageId, OrganizationId

LogicalValue = None | bool | int | float | str | tuple[object, ...]


@dataclass(frozen=True, slots=True)
class IdempotencyScope:
    organization_id: OrganizationId
    initiating_actor_id: ActorId
    operation_family: str
    idempotency_key: str


class IdempotencyState(str, Enum):
    NEW = "new"
    EXACT = "exact"
    CONFLICT = "conflict"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class IdempotencyInspection:
    state: IdempotencyState
    original_disposition: object | None = None
    original_fingerprint: str | None = None
    reconciliation_reference: IntegrityReference | None = None
    authoritative_mutation_may_have_occurred: bool = False
    internal_reconciliation_metadata_recorded: bool = False


@dataclass(frozen=True, slots=True)
class IdempotencyRegistration:
    scope: IdempotencyScope
    fingerprint: str
    disposition_id: MessageId


def _logical(value: object) -> LogicalValue:
    """Convert a protocol value to an immutable, type-preserving logical value."""
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, Identifier):
        return ("identifier", type(value).__name__, str.__str__(value))
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("semantic identity does not permit non-finite numbers")
        return ("float", value.hex())
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("semantic identity requires timezone-aware timestamps")
        return ("datetime", value.astimezone(timezone.utc).isoformat(timespec="microseconds"))
    if isinstance(value, Enum):
        return ("enum", type(value).__name__, _logical(value.value))
    if isinstance(value, Mapping):
        pairs = tuple((_logical(key), _logical(item)) for key, item in value.items())
        return ("mapping",) + tuple(sorted(pairs, key=_encode))
    if isinstance(value, tuple):
        return ("ordered",) + tuple(_logical(item) for item in value)
    if isinstance(value, frozenset):
        return ("set",) + tuple(sorted((_logical(item) for item in value), key=_encode))
    if is_dataclass(value) and not isinstance(value, type):
        return (
            "record",
            type(value).__name__,
            tuple((item.name, _logical(getattr(value, item.name))) for item in fields(value)),
        )
    raise TypeError(f"unsupported semantic identity value type: {type(value).__name__}")


def semantic_command_identity(command: object) -> tuple[object, ...]:
    """Return the complete immutable logical identity for CreateTask equivalence.

    Every caller-supplied CreateTask field is semantic except the envelope message_id,
    which identifies a delivery rather than the requested operation. Field names are
    included so this value remains explicit and inspectable without defining a wire format.
    """
    submission = command.submission
    envelope = submission.envelope
    envelope_semantics = (
        ("message_type", envelope.message_type),
        ("organization_id", envelope.organization_id),
        ("initiating_actor_id", envelope.initiating_actor_id),
        ("correlation_id", envelope.correlation_id),
        ("issued_at", envelope.issued_at),
        ("classification", envelope.classification),
        ("purpose", envelope.purpose),
        ("payload_type", envelope.payload_type),
        ("payload_version", envelope.payload_version),
        ("payload", envelope.payload),
        ("schema_version", envelope.schema_version),
        ("traffic_mode", envelope.traffic_mode),
    )
    submission_semantics = tuple(
        (field.name, getattr(submission, field.name))
        for field in fields(submission)
        if field.name != "envelope"
    )
    requested_task = (
        ("proposed_task_id", command.proposed_task_id),
        ("title", command.title),
        ("purpose", command.purpose),
        ("initial_state", command.initial_state),
        ("expected_stream_position", command.expected_stream_position),
    )
    return (
        "CreateTaskSemanticIdentity",
        ("envelope", _logical(envelope_semantics)),
        ("submission", _logical(submission_semantics)),
        ("requested_task", _logical(requested_task)),
    )


def _encode(value: object) -> bytes:
    """Nonnormative length-prefixed internal encoding of a logical value."""
    if value is None:
        return b"n"
    if value is True:
        return b"b1"
    if value is False:
        return b"b0"
    if isinstance(value, int):
        payload = str(value).encode("ascii")
        return b"i" + str(len(payload)).encode("ascii") + b":" + payload
    if isinstance(value, float):
        payload = value.hex().encode("ascii")
        return b"f" + str(len(payload)).encode("ascii") + b":" + payload
    if isinstance(value, str):
        payload = value.encode("utf-8")
        return b"s" + str(len(payload)).encode("ascii") + b":" + payload
    if isinstance(value, tuple):
        encoded = tuple(_encode(item) for item in value)
        return b"t" + str(len(encoded)).encode("ascii") + b":" + b"".join(
            str(len(item)).encode("ascii") + b":" + item for item in encoded
        )
    raise TypeError("semantic logical value contains an unsupported type")


def semantic_logical_value(value: object) -> LogicalValue:
    """Return the shared immutable, type-preserving logical normalization."""
    return _logical(value)


def semantic_logical_fingerprint(value: object) -> str:
    """Fingerprint a logical value without declaring a normative wire encoding."""
    return hashlib.sha256(_encode(_logical(value))).hexdigest()


def semantic_command_fingerprint(command: object) -> str:
    """Fingerprint the semantic logical value; the internal encoding is not a wire contract."""
    return hashlib.sha256(_encode(semantic_command_identity(command))).hexdigest()
