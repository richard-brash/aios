"""Immutable source Authority Grant evidence and attenuation contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol

from .identifiers import (
    ActorId, AuthorityGrantId, CapabilityId, CommandId, EventId,
    IntegrityReference, OrganizationId, ResourceId,
)
from .reason_codes import ReasonCode
from .validation import FrozenMap, require_aware, require_nonempty, require_positive, require_type
from .versions import RECORD_V1, RecordTypeVersion


ACCEPTED_DELEGATED_EXECUTION_UNIT = "accepted_delegated_capability_execution"


class SourceAuthorityGrantLifecycle(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"


class SourceAuthorityGrantGate(str, Enum):
    SHAPE = "source_grant_shape"
    ORGANIZATION = "source_grant_organization"
    IDENTITY = "source_grant_identity"
    LIFECYCLE = "source_grant_lifecycle"
    PURPOSE = "source_grant_purpose"
    DELEGATION = "source_grant_delegation"
    CAPABILITY_SCOPE = "source_grant_capability_scope"
    RESOURCE_CEILING = "source_grant_resource_ceiling"
    EVIDENCE = "source_grant_evidence"
    DEPENDENCY = "source_grant_dependency"


def _exact_capabilities(
    values: tuple[CapabilityId, ...], *, record_type: str,
    field_path: str, allow_empty: bool = False,
) -> tuple[CapabilityId, ...]:
    result = tuple(values)
    if not result and not allow_empty:
        raise ValueError(f"{field_path} must contain at least one exact capability")
    for index, capability in enumerate(result):
        require_type(capability, CapabilityId, record_type, f"{field_path}[{index}]")
    if len(set(result)) != len(result):
        raise ValueError(f"{field_path} must not contain duplicates")
    if result != tuple(sorted(result, key=str)):
        raise ValueError(f"{field_path} must use canonical lexical ordering")
    return result


@dataclass(frozen=True, slots=True)
class SourceGrantResourceCeiling:
    """One comparable immutable Grant Resource bound; no consumption state."""

    resource_id: ResourceId
    unit: str
    authorized_limit: int

    def __post_init__(self) -> None:
        require_type(self.resource_id, ResourceId, type(self).__name__, "resource_id")
        require_nonempty(self.unit, type(self).__name__, "unit")
        require_positive(self.authorized_limit, type(self).__name__, "authorized_limit")
        if type(self.authorized_limit) is not int:
            raise TypeError("authorized_limit must be int")
        if self.unit != ACCEPTED_DELEGATED_EXECUTION_UNIT:
            raise ValueError("source Grant Resource unit is unsupported")

    def contains(self, requested: "SourceGrantResourceCeiling") -> bool:
        require_type(requested, SourceGrantResourceCeiling, type(self).__name__, "requested")
        return (
            self.resource_id == requested.resource_id
            and self.unit == requested.unit
            and requested.authorized_limit <= self.authorized_limit
        )


@dataclass(frozen=True, slots=True)
class SourceAuthorityGrantClaim:
    """Exact bounded use that a later Task asks a trusted Grant boundary to prove."""

    command_id: CommandId
    organization_id: OrganizationId
    authority_grant_id: AuthorityGrantId
    grantor_actor_id: ActorId
    authorized_subject_actor_id: ActorId
    purpose: str
    requested_capabilities: tuple[CapabilityId, ...]
    requested_resource_ceiling: SourceGrantResourceCeiling
    completion_condition: str
    evaluation_time: datetime
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("command_id", CommandId),
            ("organization_id", OrganizationId),
            ("authority_grant_id", AuthorityGrantId),
            ("grantor_actor_id", ActorId),
            ("authorized_subject_actor_id", ActorId),
            ("requested_resource_ceiling", SourceGrantResourceCeiling),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_nonempty(self.purpose, type(self).__name__, "purpose")
        require_nonempty(
            self.completion_condition, type(self).__name__, "completion_condition",
        )
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        object.__setattr__(self, "requested_capabilities", _exact_capabilities(
            self.requested_capabilities, record_type=type(self).__name__,
            field_path="requested_capabilities",
        ))


@dataclass(frozen=True, slots=True)
class SourceAuthorityGrantProof:
    """Trusted immutable proof of one currently usable source Grant."""

    claim_command_id: CommandId
    organization_id: OrganizationId
    authority_grant_id: AuthorityGrantId
    grantor_actor_id: ActorId
    authorized_subject_actor_id: ActorId
    parent_authority_grant_id: AuthorityGrantId
    purpose: str
    permitted_capabilities: tuple[CapabilityId, ...]
    prohibited_capabilities: tuple[CapabilityId, ...]
    resource_ceiling: SourceGrantResourceCeiling
    completion_condition: str
    lifecycle_state: SourceAuthorityGrantLifecycle
    evaluation_time: datetime
    effective_at: datetime
    grant_entity_revision: int
    source_event_id: EventId
    source_stream_position: int
    grant_evidence_reference: IntegrityReference
    delegation_basis_reference: IntegrityReference
    delegation_permitted: bool
    evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("claim_command_id", CommandId),
            ("organization_id", OrganizationId),
            ("authority_grant_id", AuthorityGrantId),
            ("grantor_actor_id", ActorId),
            ("authorized_subject_actor_id", ActorId),
            ("parent_authority_grant_id", AuthorityGrantId),
            ("resource_ceiling", SourceGrantResourceCeiling),
            ("lifecycle_state", SourceAuthorityGrantLifecycle),
            ("source_event_id", EventId),
            ("grant_evidence_reference", IntegrityReference),
            ("delegation_basis_reference", IntegrityReference),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_nonempty(self.purpose, type(self).__name__, "purpose")
        require_nonempty(
            self.completion_condition, type(self).__name__, "completion_condition",
        )
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        require_aware(self.effective_at, type(self).__name__, "effective_at")
        require_positive(self.grant_entity_revision, type(self).__name__, "grant_entity_revision")
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if type(self.grant_entity_revision) is not int:
            raise TypeError("grant_entity_revision must be int")
        if type(self.source_stream_position) is not int:
            raise TypeError("source_stream_position must be int")
        if self.lifecycle_state is not SourceAuthorityGrantLifecycle.ACTIVE:
            raise ValueError("source Authority Grant proof must be active")
        if type(self.delegation_permitted) is not bool or not self.delegation_permitted:
            raise ValueError("source Authority Grant proof must permit delegation")
        if self.effective_at > self.evaluation_time:
            raise ValueError("source Authority Grant is not yet effective")
        permitted = _exact_capabilities(
            self.permitted_capabilities, record_type=type(self).__name__,
            field_path="permitted_capabilities",
        )
        prohibited = _exact_capabilities(
            self.prohibited_capabilities, record_type=type(self).__name__,
            field_path="prohibited_capabilities", allow_empty=True,
        )
        if set(permitted) & set(prohibited):
            raise ValueError("permitted and prohibited capabilities must be disjoint")
        object.__setattr__(self, "permitted_capabilities", permitted)
        object.__setattr__(self, "prohibited_capabilities", prohibited)
        evidence = tuple(self.evidence_references)
        if not evidence:
            raise ValueError("source Authority Grant proof requires evidence references")
        for index, reference in enumerate(evidence):
            require_type(
                reference, IntegrityReference, type(self).__name__,
                f"evidence_references[{index}]",
            )
        if len(set(evidence)) != len(evidence):
            raise ValueError("source Authority Grant evidence must not contain duplicates")
        object.__setattr__(self, "evidence_references", evidence)

    def validate_claim(self, claim: SourceAuthorityGrantClaim) -> None:
        """Fail closed unless the requested use is exactly bound and attenuated."""

        require_type(claim, SourceAuthorityGrantClaim, type(self).__name__, "claim")
        if self.schema_version != claim.schema_version:
            raise ValueError("source Authority Grant proof version is inconsistent")
        if self.claim_command_id != claim.command_id:
            raise ValueError("source Authority Grant proof does not bind the Command")
        if self.organization_id != claim.organization_id:
            raise ValueError("source Authority Grant proof crosses Organization boundary")
        if self.authority_grant_id != claim.authority_grant_id:
            raise ValueError("source Authority Grant identity is inconsistent")
        if self.grantor_actor_id != claim.grantor_actor_id:
            raise ValueError("source Authority Grant grantor is inconsistent")
        if self.authorized_subject_actor_id != claim.authorized_subject_actor_id:
            raise ValueError("source Authority Grant subject is inconsistent")
        if self.evaluation_time != claim.evaluation_time:
            raise ValueError("source Authority Grant evaluation time is inconsistent")
        # Purpose is descriptive in the constitutional model. This first slice
        # therefore permits exact normalized equality only; it does not infer a
        # semantic subset through prose or introduce a policy language.
        if self.purpose != claim.purpose:
            raise ValueError("requested purpose is not exactly within source Grant purpose")
        if self.completion_condition != claim.completion_condition:
            raise ValueError("completion condition exceeds or differs from source Grant")
        requested = set(claim.requested_capabilities)
        if not requested.issubset(self.permitted_capabilities):
            raise ValueError("requested capability is outside source Grant scope")
        if requested & set(self.prohibited_capabilities):
            raise ValueError("requested capability is prohibited by source Grant")
        if not self.resource_ceiling.contains(claim.requested_resource_ceiling):
            raise ValueError("requested Resource ceiling exceeds source Grant")


_SOURCE_GRANT_DENIAL_CODES = frozenset({
    ReasonCode.INPUT_MALFORMED,
    ReasonCode.VER_UNSUPPORTED,
    ReasonCode.ORG_BOUNDARY_VIOLATION,
    ReasonCode.AUTH_MISSING,
    ReasonCode.AUTH_EXPIRED,
    ReasonCode.AUTH_REVOKED,
    ReasonCode.AUTH_INSUFFICIENT,
    ReasonCode.AUTH_DELEGATION_INVALID,
    ReasonCode.RESOURCE_EXCEEDED,
    ReasonCode.RESOURCE_UNVERIFIED,
    ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
    ReasonCode.INTEGRITY_VERIFICATION_FAILED,
})


@dataclass(frozen=True, slots=True)
class SourceAuthorityGrantDenied:
    claim_command_id: CommandId
    reason_code: ReasonCode
    failed_gate: SourceAuthorityGrantGate
    safe_detail: str
    diagnostic_facts: FrozenMap = field(default_factory=FrozenMap)
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.claim_command_id, CommandId, type(self).__name__, "claim_command_id")
        require_type(self.reason_code, ReasonCode, type(self).__name__, "reason_code")
        require_type(self.failed_gate, SourceAuthorityGrantGate, type(self).__name__, "failed_gate")
        require_nonempty(self.safe_detail, type(self).__name__, "safe_detail")
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        if self.reason_code not in _SOURCE_GRANT_DENIAL_CODES:
            raise ValueError("reason code is invalid for source Authority Grant denial")
        object.__setattr__(self, "diagnostic_facts", FrozenMap(self.diagnostic_facts))


SourceAuthorityGrantResolution = SourceAuthorityGrantProof | SourceAuthorityGrantDenied


class SourceAuthorityGrantResolver(Protocol):
    """Trusted read-only boundary; callers supply no persistence or runtime."""

    def resolve(
        self, claim: SourceAuthorityGrantClaim,
    ) -> SourceAuthorityGrantResolution: ...
