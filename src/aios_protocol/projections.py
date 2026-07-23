"""Technology-neutral projection query and response contracts."""

from __future__ import annotations

from dataclasses import dataclass

from .identifiers import ActorId, IntegrityReference, OrganizationId, ProjectionId, StreamId
from .presence import Presence
from .validation import FrozenMap, require_nonempty
from .versions import RecordTypeVersion


@dataclass(frozen=True, slots=True)
class ProjectionQuery:
    organization_id: OrganizationId
    requesting_actor_id: ActorId
    projection_id: ProjectionId
    projection_version: RecordTypeVersion
    purpose: str
    classification_ceiling: str
    as_of_stream_position: int | None = None

    def __post_init__(self) -> None:
        require_nonempty(self.purpose, type(self).__name__, "purpose")
        require_nonempty(self.classification_ceiling, type(self).__name__, "classification_ceiling")
        if self.as_of_stream_position is not None and self.as_of_stream_position < 0:
            raise ValueError("projection position cannot be negative")


@dataclass(frozen=True, slots=True)
class ProjectionResponse:
    organization_id: OrganizationId
    projection_id: ProjectionId
    projection_version: RecordTypeVersion
    source_stream_id: StreamId
    through_stream_position: int
    state: Presence[object]
    integrity_reference: IntegrityReference
    implementation_metadata: FrozenMap = FrozenMap()

    def __post_init__(self) -> None:
        if self.through_stream_position < 0:
            raise ValueError("projection position cannot be negative")
