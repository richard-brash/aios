"""Side-effect-free structural validation primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping, TypeVar


class ValidationCode(str, Enum):
    """Nonnormative implementation codes; protocol reason codes live elsewhere."""

    EMPTY = "VALIDATION.EMPTY"
    MALFORMED = "VALIDATION.MALFORMED"
    WRONG_TYPE = "VALIDATION.WRONG_TYPE"
    PROHIBITED_FIELD = "VALIDATION.PROHIBITED_FIELD"
    CONFLICT = "VALIDATION.CONFLICT"
    UNSUPPORTED_VERSION = "VALIDATION.UNSUPPORTED_VERSION"
    UNSAFE_STATE = "VALIDATION.UNSAFE_STATE"


@dataclass(frozen=True, slots=True)
class StructuralValidationError(ValueError):
    code: ValidationCode
    record_type: str
    field_path: str
    safe_summary: str
    protocol_reason: str | None = None

    def __str__(self) -> str:
        return f"{self.code.value}: {self.record_type}.{self.field_path}: {self.safe_summary}"


T = TypeVar("T")


def fail(
    code: ValidationCode,
    record_type: str,
    field_path: str,
    summary: str,
    protocol_reason: str | None = None,
) -> None:
    raise StructuralValidationError(code, record_type, field_path, summary, protocol_reason)


def require_nonempty(value: str, record_type: str, field_path: str) -> str:
    if not isinstance(value, str):
        fail(ValidationCode.WRONG_TYPE, record_type, field_path, "must be text")
    if not value or value.strip() != value or any(ord(ch) < 32 for ch in value):
        fail(ValidationCode.MALFORMED, record_type, field_path, "must be nonempty normalized text")
    return value


def require_aware(value: datetime, record_type: str, field_path: str) -> datetime:
    if not isinstance(value, datetime):
        fail(ValidationCode.WRONG_TYPE, record_type, field_path, "must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        fail(ValidationCode.MALFORMED, record_type, field_path, "must be timezone-aware")
    return value


def require_type(value: Any, expected: type[T], record_type: str, field_path: str) -> T:
    if type(value) is not expected:
        fail(
            ValidationCode.WRONG_TYPE,
            record_type,
            field_path,
            f"must be {expected.__name__}",
        )
    return value


def require_types(values: Iterable[Any], expected: type[T], record_type: str, field_path: str) -> tuple[T, ...]:
    result = tuple(values)
    for index, value in enumerate(result):
        require_type(value, expected, record_type, f"{field_path}[{index}]")
    return result


def require_nonnegative(value: int | float, record_type: str, field_path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        fail(ValidationCode.MALFORMED, record_type, field_path, "must be a nonnegative number")


def require_positive(value: int | float, record_type: str, field_path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        fail(ValidationCode.MALFORMED, record_type, field_path, "must be a positive number")


def ensure_no_keys(payload: "FrozenMap", prohibited: Iterable[str], record_type: str) -> None:
    overlap = sorted(set(payload) & set(prohibited))
    if overlap:
        fail(
            ValidationCode.PROHIBITED_FIELD,
            record_type,
            "payload",
            f"contains trusted envelope field(s): {', '.join(overlap)}",
        )


def freeze(value: Any) -> Any:
    """Recursively freeze supported logical values without serialization."""

    if isinstance(value, FrozenMap):
        return value
    if isinstance(value, Mapping):
        return FrozenMap(value)
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze(item) for item in value)
    return value


class FrozenMap(Mapping[str, Any]):
    """Small immutable, deterministically ordered logical mapping."""

    __slots__ = ("_items", "_mapping")

    def __init__(self, values: Mapping[str, Any] | Iterable[tuple[str, Any]] = ()) -> None:
        raw = dict(values)
        for key in raw:
            require_nonempty(key, "FrozenMap", "key")
        items = tuple(sorted((key, freeze(value)) for key, value in raw.items()))
        object.__setattr__(self, "_items", items)
        object.__setattr__(self, "_mapping", MappingProxyType(dict(items)))

    def __getitem__(self, key: str) -> Any:
        return self._mapping[key]

    def __iter__(self):
        return iter(key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __hash__(self) -> int:
        return hash(self._items)

    def __repr__(self) -> str:
        return f"FrozenMap({dict(self._items)!r})"

    def items_tuple(self) -> tuple[tuple[str, Any], ...]:
        return self._items


EMPTY_MAP = FrozenMap()
