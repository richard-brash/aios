"""Explicit logical presence states; none collapses to ``None``."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

from .identifiers import IntegrityReference
from .validation import freeze, require_nonempty


class PresenceKind(str, Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    NOT_YET_KNOWN = "not_yet_known"
    NOT_APPLICABLE = "not_applicable"
    INTENTIONALLY_EMPTY = "intentionally_empty"
    WITHHELD = "withheld"
    REDACTED = "redacted"
    EXTERNALLY_UNAVAILABLE = "externally_unavailable"
    CONFLICTED = "conflicted"


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Known(Generic[T]):
    value: T
    kind: PresenceKind = PresenceKind.KNOWN

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", freeze(self.value))


@dataclass(frozen=True, slots=True)
class Unknown:
    kind: PresenceKind = PresenceKind.UNKNOWN


@dataclass(frozen=True, slots=True)
class NotYetKnown:
    kind: PresenceKind = PresenceKind.NOT_YET_KNOWN


@dataclass(frozen=True, slots=True)
class NotApplicable:
    kind: PresenceKind = PresenceKind.NOT_APPLICABLE


@dataclass(frozen=True, slots=True)
class IntentionallyEmpty:
    kind: PresenceKind = PresenceKind.INTENTIONALLY_EMPTY


@dataclass(frozen=True, slots=True)
class Withheld:
    classification: str
    governed_reference: IntegrityReference
    kind: PresenceKind = PresenceKind.WITHHELD

    def __post_init__(self) -> None:
        require_nonempty(self.classification, type(self).__name__, "classification")


@dataclass(frozen=True, slots=True)
class Redacted:
    tombstone_reference: IntegrityReference
    kind: PresenceKind = PresenceKind.REDACTED


@dataclass(frozen=True, slots=True)
class ExternallyUnavailable:
    external_reference: IntegrityReference
    kind: PresenceKind = PresenceKind.EXTERNALLY_UNAVAILABLE


@dataclass(frozen=True, slots=True)
class Conflicted:
    evidence_references: tuple[IntegrityReference, ...]
    kind: PresenceKind = PresenceKind.CONFLICTED

    def __post_init__(self) -> None:
        refs = tuple(self.evidence_references)
        if len(refs) < 2:
            raise ValueError("Conflicted requires at least two evidence references")
        object.__setattr__(self, "evidence_references", refs)


Presence = Known[T] | Unknown | NotYetKnown | NotApplicable | IntentionallyEmpty | Withheld | Redacted | ExternallyUnavailable | Conflicted

UNKNOWN = Unknown()
NOT_YET_KNOWN = NotYetKnown()
NOT_APPLICABLE = NotApplicable()
INTENTIONALLY_EMPTY = IntentionallyEmpty()
