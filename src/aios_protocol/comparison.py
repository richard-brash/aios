"""Deterministic, serialization-neutral comparison for conformance fixtures."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from .identifiers import Identifier


def _semantic(value: Any, bindings: Mapping[Identifier, Identifier], excluded: frozenset[str]) -> Any:
    if isinstance(value, Identifier):
        return bindings.get(value, value)
    if is_dataclass(value) and not isinstance(value, type):
        return (
            type(value).__qualname__,
            tuple(
                (field.name, _semantic(getattr(value, field.name), bindings, excluded))
                for field in fields(value) if field.name not in excluded
            ),
        )
    if isinstance(value, Mapping):
        return tuple(sorted(
            ((_semantic(k, bindings, excluded), _semantic(v, bindings, excluded)) for k, v in value.items()),
            key=repr,
        ))
    if isinstance(value, tuple):
        return tuple(_semantic(item, bindings, excluded) for item in value)
    if isinstance(value, list):
        return tuple(_semantic(item, bindings, excluded) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_semantic(item, bindings, excluded) for item in value)
    if isinstance(value, Enum):
        return (type(value).__qualname__, value.value)
    return value


def semantic_equal(
    expected: object,
    actual: object,
    *,
    symbolic_bindings: Mapping[Identifier, Identifier] | None = None,
    permitted_metadata_fields: frozenset[str] = frozenset(),
) -> bool:
    """Compare all semantic fields, excluding only explicitly permitted metadata."""
    bindings = symbolic_bindings or {}
    return _semantic(expected, bindings, permitted_metadata_fields) == _semantic(actual, {}, permitted_metadata_fields)


def stable_ordered_equal(
    expected: Sequence[object],
    actual: Sequence[object],
    *,
    symbolic_bindings: Mapping[Identifier, Identifier] | None = None,
) -> bool:
    """Compare sequence order without sorting normatively ordered collections."""
    if len(expected) != len(actual):
        return False
    return all(
        semantic_equal(left, right, symbolic_bindings=symbolic_bindings)
        for left, right in zip(expected, actual)
    )


def projection_equivalent(
    expected_state: object,
    actual_state: object,
    *,
    permitted_implementation_metadata: frozenset[str] = frozenset({"implementation_metadata"}),
) -> bool:
    return semantic_equal(
        expected_state,
        actual_state,
        permitted_metadata_fields=permitted_implementation_metadata,
    )
