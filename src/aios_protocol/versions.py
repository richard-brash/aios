"""Explicit protocol and governance version value objects."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .validation import ValidationCode, fail, require_nonempty


_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:-([A-Za-z0-9.-]+))?$")


@dataclass(frozen=True, order=True, slots=True)
class Version:
    raw: str

    def __post_init__(self) -> None:
        require_nonempty(self.raw, type(self).__name__, "raw")
        if not _VERSION.fullmatch(self.raw):
            raise ValueError(f"invalid {type(self).__name__}")

    @property
    def major(self) -> int:
        return int(self.raw.split(".", 1)[0])


class ProtocolFamilyVersion(Version): pass
class RecordTypeVersion(Version): pass
class PayloadVersion(Version): pass
class SpecificationVersion(Version): pass


@dataclass(frozen=True, slots=True)
class PolicyVersionReference:
    policy_id: str
    version: Version

    def __post_init__(self) -> None:
        require_nonempty(self.policy_id, type(self).__name__, "policy_id")


@dataclass(frozen=True, slots=True)
class SupportedVersionRegistry:
    record_versions: tuple[tuple[str, tuple[RecordTypeVersion, ...]], ...]

    def __post_init__(self) -> None:
        normalized = tuple(
            sorted((name, tuple(versions)) for name, versions in tuple(self.record_versions))
        )
        object.__setattr__(self, "record_versions", normalized)

    def validate(self, record_type: str, version: RecordTypeVersion) -> None:
        supported = dict(self.record_versions).get(record_type)
        if supported is None or version not in supported:
            fail(
                ValidationCode.UNSUPPORTED_VERSION,
                record_type,
                "schema_version",
                "unsupported record version",
                "VER.UNSUPPORTED",
            )


PROTOCOL_V1 = ProtocolFamilyVersion("1.0")
RECORD_V1 = RecordTypeVersion("1.0")
PAYLOAD_V1 = PayloadVersion("1.0")
SPEC_0_0_2 = SpecificationVersion("0.0.2")
