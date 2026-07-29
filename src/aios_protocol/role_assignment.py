"""Immutable Temporary Worker Role Assignment lifecycle contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol

from .authority import SourceAuthorityGrantLifecycle
from .identifiers import (
    ActorId, AuditRecordId, AuthorityGrantId, CommandId, EventId,
    IntegrityReference, OrganizationId, RoleAssignmentId, RoleId,
)
from .reason_codes import ReasonCode
from .temporary_worker import (
    ActorEnrollmentEvidence, ActorIdentityState, ActorKind,
    TemporaryWorkerLifecycle, TemporaryWorkerTransitionProof,
)
from .validation import FrozenMap, require_aware, require_nonempty, require_nonnegative, require_positive, require_type
from .versions import RECORD_V1, RecordTypeVersion


class RoleLifecycleState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"
    ARCHIVED = "archived"


class RoleAssignmentLifecycle(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ARCHIVED = "archived"


class RoleAssignmentTransition(str, Enum):
    PROPOSE = "propose"
    ACTIVATE = "activate"
    SUSPEND = "suspend"
    RESTORE = "restore"
    EXPIRE = "expire"
    REVOKE = "revoke"
    ARCHIVE = "archive"


class RoleAssignmentGate(str, Enum):
    SHAPE = "role_assignment_shape"
    ORGANIZATION = "role_assignment_organization"
    WORKER = "role_assignment_worker"
    ROLE = "role_assignment_role"
    ENROLLMENT = "role_assignment_enrollment"
    ASSIGNER = "role_assignment_assigner"
    AUTHORITY = "role_assignment_authority"
    SCOPE = "role_assignment_scope"
    LIFECYCLE = "role_assignment_lifecycle"
    EXPIRY = "role_assignment_expiry"
    EVIDENCE = "role_assignment_evidence"
    DEPENDENCY = "role_assignment_dependency"


def _canonical_evidence(
    values: tuple[IntegrityReference, ...], *, record_type: str, field_path: str,
) -> tuple[IntegrityReference, ...]:
    result = tuple(values)
    if not result:
        raise ValueError(f"{field_path} must contain authoritative evidence")
    for index, reference in enumerate(result):
        require_type(reference, IntegrityReference, record_type, f"{field_path}[{index}]")
    if len(set(result)) != len(result):
        raise ValueError(f"{field_path} must not contain duplicates")
    if result != tuple(sorted(result, key=str)):
        raise ValueError(f"{field_path} must use canonical lexical ordering")
    return result


@dataclass(frozen=True, slots=True)
class ActiveRoleEvidence:
    """Authoritative exact Role revision used for qualification."""

    organization_id: OrganizationId
    role_id: RoleId
    lifecycle_state: RoleLifecycleState
    role_entity_revision: int
    source_event_id: EventId
    source_stream_position: int
    integrity_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("organization_id", OrganizationId),
            ("role_id", RoleId),
            ("lifecycle_state", RoleLifecycleState),
            ("source_event_id", EventId),
            ("integrity_reference", IntegrityReference),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_positive(self.role_entity_revision, type(self).__name__, "role_entity_revision")
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if type(self.role_entity_revision) is not int:
            raise TypeError("role_entity_revision must be int")
        if type(self.source_stream_position) is not int:
            raise TypeError("source_stream_position must be int")


@dataclass(frozen=True, slots=True)
class RoleAssignmentAuthorityEvidence:
    """Trusted proof that one Actor may assign the exact Worker to the exact Role."""

    claim_command_id: CommandId
    organization_id: OrganizationId
    assigner_actor_id: ActorId
    authority_grant_id: AuthorityGrantId
    subject_actor_id: ActorId
    role_id: RoleId
    assignment_permitted: bool
    lifecycle_state: SourceAuthorityGrantLifecycle
    evaluation_time: datetime
    authority_entity_revision: int
    source_event_id: EventId
    source_stream_position: int
    authority_evidence_reference: IntegrityReference
    evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("claim_command_id", CommandId),
            ("organization_id", OrganizationId),
            ("assigner_actor_id", ActorId),
            ("authority_grant_id", AuthorityGrantId),
            ("subject_actor_id", ActorId),
            ("role_id", RoleId),
            ("lifecycle_state", SourceAuthorityGrantLifecycle),
            ("source_event_id", EventId),
            ("authority_evidence_reference", IntegrityReference),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        require_positive(
            self.authority_entity_revision, type(self).__name__, "authority_entity_revision",
        )
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if type(self.authority_entity_revision) is not int:
            raise TypeError("authority_entity_revision must be int")
        if type(self.source_stream_position) is not int:
            raise TypeError("source_stream_position must be int")
        if type(self.assignment_permitted) is not bool or not self.assignment_permitted:
            raise ValueError("assigner authority must affirm the exact Role Assignment")
        if self.lifecycle_state is not SourceAuthorityGrantLifecycle.ACTIVE:
            raise ValueError("assigner Authority Grant must be active")
        object.__setattr__(self, "evidence_references", _canonical_evidence(
            self.evidence_references,
            record_type=type(self).__name__,
            field_path="evidence_references",
        ))


@dataclass(frozen=True, slots=True)
class RoleAssignmentProfile:
    """Immutable identity and scope of one Temporary Worker Role Assignment."""

    role_assignment_id: RoleAssignmentId
    organization_id: OrganizationId
    worker_actor_id: ActorId
    role_id: RoleId
    assigned_by_actor_id: ActorId
    qualifying_role_entity_revision: int
    effective_at: datetime
    duty_scope: str
    review_or_completion_condition: str
    review_or_completion_condition_reference: IntegrityReference
    profile_evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("role_assignment_id", RoleAssignmentId),
            ("organization_id", OrganizationId),
            ("worker_actor_id", ActorId),
            ("role_id", RoleId),
            ("assigned_by_actor_id", ActorId),
            ("review_or_completion_condition_reference", IntegrityReference),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_positive(
            self.qualifying_role_entity_revision,
            type(self).__name__, "qualifying_role_entity_revision",
        )
        if type(self.qualifying_role_entity_revision) is not int:
            raise TypeError("qualifying_role_entity_revision must be int")
        require_aware(self.effective_at, type(self).__name__, "effective_at")
        require_nonempty(self.duty_scope, type(self).__name__, "duty_scope")
        require_nonempty(
            self.review_or_completion_condition,
            type(self).__name__, "review_or_completion_condition",
        )
        if self.worker_actor_id == self.assigned_by_actor_id:
            raise ValueError("Temporary Worker cannot assign its own Role")
        object.__setattr__(self, "profile_evidence_references", _canonical_evidence(
            self.profile_evidence_references,
            record_type=type(self).__name__,
            field_path="profile_evidence_references",
        ))


@dataclass(frozen=True, slots=True)
class RoleAssignmentQualificationEvidence:
    """Current immutable enrollment, Role, assigner, and authority conjunction."""

    claim_command_id: CommandId
    evaluation_time: datetime
    observed_organization_stream_position: int
    current_qualification_reference: IntegrityReference
    enrollment_proof: TemporaryWorkerTransitionProof
    role_evidence: ActiveRoleEvidence
    assigner_actor: ActorEnrollmentEvidence
    assigner_authority: RoleAssignmentAuthorityEvidence
    evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("claim_command_id", CommandId),
            ("current_qualification_reference", IntegrityReference),
            ("enrollment_proof", TemporaryWorkerTransitionProof),
            ("role_evidence", ActiveRoleEvidence),
            ("assigner_actor", ActorEnrollmentEvidence),
            ("assigner_authority", RoleAssignmentAuthorityEvidence),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        require_positive(
            self.observed_organization_stream_position,
            type(self).__name__, "observed_organization_stream_position",
        )
        if type(self.observed_organization_stream_position) is not int:
            raise TypeError("observed_organization_stream_position must be int")
        enrollment = self.enrollment_proof.claim.enrollment
        if self.enrollment_proof.claim.resulting_state is not TemporaryWorkerLifecycle.ACTIVE:
            raise ValueError("Role Assignment requires active Temporary Worker enrollment")
        if self.role_evidence.lifecycle_state is not RoleLifecycleState.ACTIVE:
            raise ValueError("Role Assignment requires active Role evidence")
        if self.assigner_actor.identity_state is not ActorIdentityState.ACTIVE:
            raise ValueError("Role assigner identity must be active")
        if self.assigner_actor.actor_kind not in (ActorKind.HUMAN, ActorKind.EMPLOYEE):
            raise ValueError("Role assigner must be a Human or Employee Actor")
        organization_ids = {
            enrollment.organization_id,
            self.role_evidence.organization_id,
            self.assigner_actor.organization_id,
            self.assigner_authority.organization_id,
        }
        if len(organization_ids) != 1:
            raise ValueError("Role Assignment qualification crosses Organization boundary")
        if self.assigner_actor.actor_id != enrollment.sponsor_actor.actor_id:
            raise ValueError("first-worker Role assigner must be its Sponsor")
        if self.assigner_authority.assigner_actor_id != self.assigner_actor.actor_id:
            raise ValueError("Role assigner authority names another Actor")
        if self.assigner_authority.subject_actor_id != enrollment.actor_id:
            raise ValueError("Role assigner authority names another Worker Actor")
        if self.assigner_authority.role_id != self.role_evidence.role_id:
            raise ValueError("Role assigner authority names another Role")
        if self.assigner_authority.claim_command_id != self.claim_command_id:
            raise ValueError("Role assigner authority differs from qualification Command")
        if self.assigner_authority.evaluation_time != self.evaluation_time:
            raise ValueError("Role assigner authority differs from qualification time")
        evidence_positions = (
            self.enrollment_proof.source_stream_position,
            self.role_evidence.source_stream_position,
            self.assigner_actor.source_stream_position,
            self.assigner_authority.source_stream_position,
        )
        if any(
            position > self.observed_organization_stream_position
            for position in evidence_positions
        ):
            raise ValueError("current qualification predates its authoritative evidence")
        object.__setattr__(self, "evidence_references", _canonical_evidence(
            self.evidence_references,
            record_type=type(self).__name__,
            field_path="evidence_references",
        ))

    @property
    def organization_id(self) -> OrganizationId:
        return self.role_evidence.organization_id

    @property
    def worker_actor_id(self) -> ActorId:
        return self.enrollment_proof.claim.enrollment.actor_id


@dataclass(frozen=True, slots=True)
class RoleAssignmentExpiryEvidence:
    """Explicit immutable condition evidence; construction performs no clock read."""

    organization_id: OrganizationId
    role_assignment_id: RoleAssignmentId
    condition_reference: IntegrityReference
    condition_satisfied_at: datetime
    source_event_id: EventId
    source_stream_position: int
    integrity_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("organization_id", OrganizationId),
            ("role_assignment_id", RoleAssignmentId),
            ("condition_reference", IntegrityReference),
            ("source_event_id", EventId),
            ("integrity_reference", IntegrityReference),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_aware(
            self.condition_satisfied_at, type(self).__name__, "condition_satisfied_at",
        )
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if type(self.source_stream_position) is not int:
            raise TypeError("source_stream_position must be int")


@dataclass(frozen=True, slots=True)
class RoleAssignmentPriorTransitionEvidence:
    """Exact authoritative relationship state consumed by a later transition."""

    organization_id: OrganizationId
    role_assignment_id: RoleAssignmentId
    lifecycle_state: RoleAssignmentLifecycle
    entity_revision: int
    source_event_id: EventId
    source_stream_position: int
    integrity_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("organization_id", OrganizationId),
            ("role_assignment_id", RoleAssignmentId),
            ("lifecycle_state", RoleAssignmentLifecycle),
            ("source_event_id", EventId),
            ("integrity_reference", IntegrityReference),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_positive(self.entity_revision, type(self).__name__, "entity_revision")
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if type(self.entity_revision) is not int:
            raise TypeError("entity_revision must be int")
        if type(self.source_stream_position) is not int:
            raise TypeError("source_stream_position must be int")


_TRANSITIONS = {
    RoleAssignmentTransition.PROPOSE: (None, RoleAssignmentLifecycle.PROPOSED),
    RoleAssignmentTransition.ACTIVATE: (
        RoleAssignmentLifecycle.PROPOSED, RoleAssignmentLifecycle.ACTIVE,
    ),
    RoleAssignmentTransition.SUSPEND: (
        RoleAssignmentLifecycle.ACTIVE, RoleAssignmentLifecycle.SUSPENDED,
    ),
    RoleAssignmentTransition.RESTORE: (
        RoleAssignmentLifecycle.SUSPENDED, RoleAssignmentLifecycle.ACTIVE,
    ),
    RoleAssignmentTransition.EXPIRE: (
        (RoleAssignmentLifecycle.ACTIVE, RoleAssignmentLifecycle.SUSPENDED),
        RoleAssignmentLifecycle.EXPIRED,
    ),
    RoleAssignmentTransition.REVOKE: (
        (RoleAssignmentLifecycle.ACTIVE, RoleAssignmentLifecycle.SUSPENDED),
        RoleAssignmentLifecycle.REVOKED,
    ),
    RoleAssignmentTransition.ARCHIVE: (
        (RoleAssignmentLifecycle.SUSPENDED, RoleAssignmentLifecycle.EXPIRED,
         RoleAssignmentLifecycle.REVOKED),
        RoleAssignmentLifecycle.ARCHIVED,
    ),
}


@dataclass(frozen=True, slots=True)
class RoleAssignmentTransitionClaim:
    """One pure relationship transition over explicitly supplied evidence."""

    command_id: CommandId
    profile: RoleAssignmentProfile
    transition: RoleAssignmentTransition
    prior_state: RoleAssignmentLifecycle | None
    resulting_state: RoleAssignmentLifecycle
    expected_entity_revision: int
    prior_transition_evidence: RoleAssignmentPriorTransitionEvidence | None
    evaluation_time: datetime
    qualification_evidence: RoleAssignmentQualificationEvidence | None
    expiry_evidence: RoleAssignmentExpiryEvidence | None
    transition_evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("command_id", CommandId),
            ("profile", RoleAssignmentProfile),
            ("transition", RoleAssignmentTransition),
            ("resulting_state", RoleAssignmentLifecycle),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        if self.prior_state is not None:
            require_type(
                self.prior_state, RoleAssignmentLifecycle,
                type(self).__name__, "prior_state",
            )
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        require_nonnegative(
            self.expected_entity_revision, type(self).__name__, "expected_entity_revision",
        )
        if type(self.expected_entity_revision) is not int:
            raise TypeError("expected_entity_revision must be int")
        expected_prior, expected_result = _TRANSITIONS[self.transition]
        allowed_prior = expected_prior if isinstance(expected_prior, tuple) else (expected_prior,)
        if self.prior_state not in allowed_prior or self.resulting_state is not expected_result:
            raise ValueError("unsupported Role Assignment lifecycle transition")
        if self.transition is RoleAssignmentTransition.PROPOSE:
            if self.expected_entity_revision != 0:
                raise ValueError("RoleAssignmentProposed requires nonexistent revision zero")
            if self.prior_transition_evidence is not None:
                raise ValueError("RoleAssignmentProposed cannot claim prior relationship history")
        else:
            if self.expected_entity_revision < 1:
                raise ValueError("existing Role Assignment transition requires positive revision")
            require_type(
                self.prior_transition_evidence, RoleAssignmentPriorTransitionEvidence,
                type(self).__name__, "prior_transition_evidence",
            )
            prior = self.prior_transition_evidence
            if prior.organization_id != self.profile.organization_id:
                raise ValueError("prior Role Assignment state crosses Organization boundary")
            if prior.role_assignment_id != self.profile.role_assignment_id:
                raise ValueError("prior state names another Role Assignment")
            if prior.lifecycle_state is not self.prior_state:
                raise ValueError("prior Role Assignment lifecycle state is contradictory")
            if prior.entity_revision != self.expected_entity_revision:
                raise ValueError("prior Role Assignment entity revision is stale")
        needs_qualification = self.transition in (
            RoleAssignmentTransition.PROPOSE,
            RoleAssignmentTransition.ACTIVATE,
            RoleAssignmentTransition.RESTORE,
        )
        if needs_qualification:
            require_type(
                self.qualification_evidence, RoleAssignmentQualificationEvidence,
                type(self).__name__, "qualification_evidence",
            )
            self._validate_qualification()
        elif self.qualification_evidence is not None:
            raise ValueError("transition does not accept unrelated current qualification evidence")
        if self.transition is RoleAssignmentTransition.EXPIRE:
            require_type(
                self.expiry_evidence, RoleAssignmentExpiryEvidence,
                type(self).__name__, "expiry_evidence",
            )
            self._validate_expiry()
        elif self.expiry_evidence is not None:
            raise ValueError("non-expiry transition cannot claim expiry evidence")
        object.__setattr__(self, "transition_evidence_references", _canonical_evidence(
            self.transition_evidence_references,
            record_type=type(self).__name__,
            field_path="transition_evidence_references",
        ))

    def _validate_qualification(self) -> None:
        evidence = self.qualification_evidence
        assert evidence is not None
        if evidence.organization_id != self.profile.organization_id:
            raise ValueError("Role Assignment profile crosses Organization boundary")
        if evidence.worker_actor_id != self.profile.worker_actor_id:
            raise ValueError("Role Assignment profile names another Worker Actor")
        if evidence.role_evidence.role_id != self.profile.role_id:
            raise ValueError("Role Assignment profile names another Role")
        if evidence.role_evidence.role_entity_revision != self.profile.qualifying_role_entity_revision:
            raise ValueError("Role Assignment Role revision is stale or contradictory")
        if evidence.assigner_actor.actor_id != self.profile.assigned_by_actor_id:
            raise ValueError("Role Assignment profile names another assigner")
        if evidence.claim_command_id != self.command_id:
            raise ValueError("qualification does not bind the transition Command")
        if evidence.evaluation_time != self.evaluation_time:
            raise ValueError("qualification does not bind the evaluation point")
        if (
            self.transition in (
                RoleAssignmentTransition.ACTIVATE, RoleAssignmentTransition.RESTORE,
            )
            and self.evaluation_time < self.profile.effective_at
        ):
            raise ValueError("Role Assignment is not yet effective")

    def _validate_expiry(self) -> None:
        evidence = self.expiry_evidence
        assert evidence is not None
        if evidence.organization_id != self.profile.organization_id:
            raise ValueError("Role Assignment expiry crosses Organization boundary")
        if evidence.role_assignment_id != self.profile.role_assignment_id:
            raise ValueError("Role Assignment expiry names another relationship")
        if evidence.condition_reference != self.profile.review_or_completion_condition_reference:
            raise ValueError("Role Assignment expiry condition is inconsistent")
        if evidence.condition_satisfied_at > self.evaluation_time:
            raise ValueError("Role Assignment expiry condition is not yet satisfied")
        if (
            self.prior_transition_evidence is not None
            and evidence.source_stream_position
            <= self.prior_transition_evidence.source_stream_position
        ):
            raise ValueError("Role Assignment expiry evidence does not follow prior state")


@dataclass(frozen=True, slots=True)
class RoleAssignmentTransitionProof:
    """Replay-sufficient accepted evidence for one relationship transition."""

    claim: RoleAssignmentTransitionClaim
    resulting_entity_revision: int
    source_event_id: EventId
    source_stream_position: int
    audit_record_id: AuditRecordId
    accepted_evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("claim", RoleAssignmentTransitionClaim),
            ("source_event_id", EventId),
            ("audit_record_id", AuditRecordId),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_positive(
            self.resulting_entity_revision, type(self).__name__, "resulting_entity_revision",
        )
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if type(self.resulting_entity_revision) is not int:
            raise TypeError("resulting_entity_revision must be int")
        if type(self.source_stream_position) is not int:
            raise TypeError("source_stream_position must be int")
        if self.resulting_entity_revision != self.claim.expected_entity_revision + 1:
            raise ValueError("accepted Role Assignment revision must advance exactly once")
        if (
            self.claim.prior_transition_evidence is not None
            and self.source_stream_position
            <= self.claim.prior_transition_evidence.source_stream_position
        ):
            raise ValueError("accepted Role Assignment Event must follow prior transition")
        if (
            self.claim.prior_transition_evidence is not None
            and self.source_event_id == self.claim.prior_transition_evidence.source_event_id
        ):
            raise ValueError("accepted and prior transitions require distinct Events")
        if (
            self.claim.qualification_evidence is not None
            and self.source_stream_position
            <= self.claim.qualification_evidence.observed_organization_stream_position
        ):
            raise ValueError("accepted Role Assignment Event must follow qualification evidence")
        if self.claim.expiry_evidence is not None:
            if self.source_stream_position <= self.claim.expiry_evidence.source_stream_position:
                raise ValueError("accepted expiry Event must follow condition evidence")
            if self.source_event_id == self.claim.expiry_evidence.source_event_id:
                raise ValueError("expiry and condition evidence require distinct Events")
        object.__setattr__(self, "accepted_evidence_references", _canonical_evidence(
            self.accepted_evidence_references,
            record_type=type(self).__name__,
            field_path="accepted_evidence_references",
        ))


_ROLE_ASSIGNMENT_DENIAL_CODES = frozenset({
    ReasonCode.INPUT_MALFORMED,
    ReasonCode.VER_UNSUPPORTED,
    ReasonCode.ORG_BOUNDARY_VIOLATION,
    ReasonCode.IDENTITY_UNKNOWN,
    ReasonCode.IDENTITY_FORGED,
    ReasonCode.IDENTITY_SUSPENDED,
    ReasonCode.AUTH_MISSING,
    ReasonCode.AUTH_EXPIRED,
    ReasonCode.AUTH_REVOKED,
    ReasonCode.AUTH_INSUFFICIENT,
    ReasonCode.AUTH_DELEGATION_INVALID,
    ReasonCode.LIFECYCLE_INVALID_TRANSITION,
    ReasonCode.STATE_STALE_VERSION,
    ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
    ReasonCode.INTEGRITY_VERIFICATION_FAILED,
})


@dataclass(frozen=True, slots=True)
class RoleAssignmentDenied:
    claim_command_id: CommandId
    reason_code: ReasonCode
    failed_gate: RoleAssignmentGate
    safe_detail: str
    diagnostic_facts: FrozenMap = field(default_factory=FrozenMap)
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.claim_command_id, CommandId, type(self).__name__, "claim_command_id")
        require_type(self.reason_code, ReasonCode, type(self).__name__, "reason_code")
        require_type(self.failed_gate, RoleAssignmentGate, type(self).__name__, "failed_gate")
        require_nonempty(self.safe_detail, type(self).__name__, "safe_detail")
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        if self.reason_code not in _ROLE_ASSIGNMENT_DENIAL_CODES:
            raise ValueError("reason code is invalid for Role Assignment denial")
        object.__setattr__(self, "diagnostic_facts", FrozenMap(self.diagnostic_facts))


RoleAssignmentResolution = RoleAssignmentTransitionProof | RoleAssignmentDenied


class RoleAssignmentEvaluator(Protocol):
    """Capability-neutral pure boundary over supplied immutable evidence."""

    def evaluate(self, claim: RoleAssignmentTransitionClaim) -> RoleAssignmentResolution: ...
