"""Immutable Temporary Worker enrollment and lifecycle contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol

from .authority import SourceAuthorityGrantProof
from .identifiers import (
    ActorId, AuditRecordId, AuthorityGrantId, CommandId, EventId,
    IntegrityReference, OrganizationId, TaskId,
)
from .reason_codes import ReasonCode
from .validation import FrozenMap, require_aware, require_nonempty, require_nonnegative, require_positive, require_type
from .versions import RECORD_V1, RecordTypeVersion


class ActorKind(str, Enum):
    HUMAN = "human"
    EMPLOYEE = "employee"
    TEMPORARY_WORKER = "temporary_worker"
    SERVICE = "service"


class ActorIdentityState(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TemporaryWorkerLifecycle(str, Enum):
    REQUESTED = "requested"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ARCHIVED = "archived"


class TemporaryWorkerTransition(str, Enum):
    REQUEST = "request"
    ACTIVATE = "activate"
    REVOKE_REQUEST = "revoke_request"
    SUSPEND = "suspend"
    RESTORE = "restore"
    COMPLETE = "complete"
    REVOKE = "revoke"
    ARCHIVE = "archive"


class TemporaryWorkerCompletionCondition(str, Enum):
    TASK_TERMINAL = "task_terminal"


class TemporaryWorkerTaskTerminalState(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TemporaryWorkerGate(str, Enum):
    SHAPE = "temporary_worker_shape"
    ORGANIZATION = "temporary_worker_organization"
    ACTOR = "temporary_worker_actor"
    SPONSOR = "temporary_worker_sponsor"
    PURPOSE = "temporary_worker_purpose"
    SOURCE_GRANT = "temporary_worker_source_grant"
    BOUNDS = "temporary_worker_bounds"
    LIFECYCLE = "temporary_worker_lifecycle"
    EVIDENCE = "temporary_worker_evidence"
    DEPENDENCY = "temporary_worker_dependency"


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
class ActorEnrollmentEvidence:
    """Authoritative Actor facts used by enrollment; never credentials."""

    organization_id: OrganizationId
    actor_id: ActorId
    actor_kind: ActorKind
    identity_state: ActorIdentityState
    actor_entity_revision: int
    source_event_id: EventId
    source_stream_position: int
    identity_evidence_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("organization_id", OrganizationId),
            ("actor_id", ActorId),
            ("actor_kind", ActorKind),
            ("identity_state", ActorIdentityState),
            ("source_event_id", EventId),
            ("identity_evidence_reference", IntegrityReference),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_positive(self.actor_entity_revision, type(self).__name__, "actor_entity_revision")
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if type(self.actor_entity_revision) is not int:
            raise TypeError("actor_entity_revision must be int")
        if type(self.source_stream_position) is not int:
            raise TypeError("source_stream_position must be int")


@dataclass(frozen=True, slots=True)
class FirstTemporaryWorkerBounds:
    """Closed Milestone 3 profile limits; no Budget administration or usage state."""

    maximum_active_role_assignments: int
    maximum_tasks: int
    maximum_accepted_delegated_capability_executions: int
    completion_condition: TemporaryWorkerCompletionCondition
    redelegation_permitted: bool
    subworker_creation_permitted: bool
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name in (
            "maximum_active_role_assignments",
            "maximum_tasks",
            "maximum_accepted_delegated_capability_executions",
        ):
            value = getattr(self, name)
            if type(value) is not int:
                raise TypeError(f"{name} must be int")
            if value != 1:
                raise ValueError(f"{name} must be exactly one for the first-worker profile")
        require_type(
            self.completion_condition, TemporaryWorkerCompletionCondition,
            type(self).__name__, "completion_condition",
        )
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        if type(self.redelegation_permitted) is not bool or self.redelegation_permitted:
            raise ValueError("first-worker redelegation must be prohibited")
        if type(self.subworker_creation_permitted) is not bool or self.subworker_creation_permitted:
            raise ValueError("first-worker sub-worker creation must be prohibited")


@dataclass(frozen=True, slots=True)
class TemporaryWorkerEnrollment:
    """Immutable eligibility profile for one existing Temporary Worker Actor."""

    worker_actor: ActorEnrollmentEvidence
    sponsor_actor: ActorEnrollmentEvidence
    purpose: str
    source_authority_grant_id: AuthorityGrantId
    source_grant_evidence_reference: IntegrityReference
    bounds: FirstTemporaryWorkerBounds
    enrollment_evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("worker_actor", ActorEnrollmentEvidence),
            ("sponsor_actor", ActorEnrollmentEvidence),
            ("source_authority_grant_id", AuthorityGrantId),
            ("source_grant_evidence_reference", IntegrityReference),
            ("bounds", FirstTemporaryWorkerBounds),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_nonempty(self.purpose, type(self).__name__, "purpose")
        if self.worker_actor.actor_kind is not ActorKind.TEMPORARY_WORKER:
            raise ValueError("enrollment Actor must have temporary_worker kind")
        if self.worker_actor.identity_state is not ActorIdentityState.ACTIVE:
            raise ValueError("enrollment Actor identity must be active")
        if self.sponsor_actor.actor_kind not in (ActorKind.HUMAN, ActorKind.EMPLOYEE):
            raise ValueError("Sponsor must be a Human or Employee Actor")
        if self.sponsor_actor.identity_state is not ActorIdentityState.ACTIVE:
            raise ValueError("Sponsor Actor identity must be active")
        if self.worker_actor.organization_id != self.sponsor_actor.organization_id:
            raise ValueError("Worker and Sponsor must share one Organization")
        if self.worker_actor.actor_id == self.sponsor_actor.actor_id:
            raise ValueError("Temporary Worker cannot sponsor itself")
        object.__setattr__(self, "enrollment_evidence_references", _canonical_evidence(
            self.enrollment_evidence_references,
            record_type=type(self).__name__,
            field_path="enrollment_evidence_references",
        ))

    @property
    def organization_id(self) -> OrganizationId:
        return self.worker_actor.organization_id

    @property
    def actor_id(self) -> ActorId:
        """Enrollment deliberately uses the accountable Actor's durable identity."""

        return self.worker_actor.actor_id


@dataclass(frozen=True, slots=True)
class TemporaryWorkerTaskTerminalEvidence:
    """Immutable evidence that the profile's one Task reached a terminal state."""

    organization_id: OrganizationId
    worker_actor_id: ActorId
    task_id: TaskId
    terminal_state: TemporaryWorkerTaskTerminalState
    source_event_id: EventId
    source_stream_position: int
    integrity_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("organization_id", OrganizationId),
            ("worker_actor_id", ActorId),
            ("task_id", TaskId),
            ("terminal_state", TemporaryWorkerTaskTerminalState),
            ("source_event_id", EventId),
            ("integrity_reference", IntegrityReference),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if type(self.source_stream_position) is not int:
            raise TypeError("source_stream_position must be int")


@dataclass(frozen=True, slots=True)
class TemporaryWorkerTaskAssignmentEvidence:
    """Authoritative lineage from an active enrollment to its one assigned Task."""

    organization_id: OrganizationId
    worker_actor_id: ActorId
    task_id: TaskId
    enrollment_activation_event_id: EventId
    enrollment_activation_stream_position: int
    enrollment_activation_integrity_reference: IntegrityReference
    assignment_event_id: EventId
    assignment_stream_position: int
    assignment_integrity_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("organization_id", OrganizationId),
            ("worker_actor_id", ActorId),
            ("task_id", TaskId),
            ("enrollment_activation_event_id", EventId),
            ("enrollment_activation_integrity_reference", IntegrityReference),
            ("assignment_event_id", EventId),
            ("assignment_integrity_reference", IntegrityReference),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        for name in (
            "enrollment_activation_stream_position", "assignment_stream_position",
        ):
            value = getattr(self, name)
            require_positive(value, type(self).__name__, name)
            if type(value) is not int:
                raise TypeError(f"{name} must be int")
        if self.enrollment_activation_event_id == self.assignment_event_id:
            raise ValueError("enrollment activation and Task assignment require distinct Events")
        if self.enrollment_activation_stream_position >= self.assignment_stream_position:
            raise ValueError("Task assignment must follow active enrollment evidence")


_TRANSITIONS = {
    TemporaryWorkerTransition.REQUEST: (None, TemporaryWorkerLifecycle.REQUESTED),
    TemporaryWorkerTransition.ACTIVATE: (
        TemporaryWorkerLifecycle.REQUESTED, TemporaryWorkerLifecycle.ACTIVE,
    ),
    TemporaryWorkerTransition.REVOKE_REQUEST: (
        TemporaryWorkerLifecycle.REQUESTED, TemporaryWorkerLifecycle.REVOKED,
    ),
    TemporaryWorkerTransition.SUSPEND: (
        TemporaryWorkerLifecycle.ACTIVE, TemporaryWorkerLifecycle.SUSPENDED,
    ),
    TemporaryWorkerTransition.RESTORE: (
        TemporaryWorkerLifecycle.SUSPENDED, TemporaryWorkerLifecycle.ACTIVE,
    ),
    TemporaryWorkerTransition.COMPLETE: (
        TemporaryWorkerLifecycle.ACTIVE, TemporaryWorkerLifecycle.COMPLETED,
    ),
    TemporaryWorkerTransition.REVOKE: (
        (TemporaryWorkerLifecycle.ACTIVE, TemporaryWorkerLifecycle.SUSPENDED),
        TemporaryWorkerLifecycle.REVOKED,
    ),
    TemporaryWorkerTransition.ARCHIVE: (
        (TemporaryWorkerLifecycle.COMPLETED, TemporaryWorkerLifecycle.REVOKED),
        TemporaryWorkerLifecycle.ARCHIVED,
    ),
}


@dataclass(frozen=True, slots=True)
class TemporaryWorkerTransitionClaim:
    """One pure lifecycle request over pinned authoritative enrollment evidence."""

    command_id: CommandId
    enrollment: TemporaryWorkerEnrollment
    transition: TemporaryWorkerTransition
    prior_state: TemporaryWorkerLifecycle | None
    resulting_state: TemporaryWorkerLifecycle
    expected_entity_revision: int
    prior_transition_event_id: EventId | None
    prior_transition_integrity_reference: IntegrityReference | None
    evaluation_time: datetime
    source_grant_proof: SourceAuthorityGrantProof | None
    task_assignment_evidence: TemporaryWorkerTaskAssignmentEvidence | None
    task_terminal_evidence: TemporaryWorkerTaskTerminalEvidence | None
    transition_evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("command_id", CommandId),
            ("enrollment", TemporaryWorkerEnrollment),
            ("transition", TemporaryWorkerTransition),
            ("resulting_state", TemporaryWorkerLifecycle),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        if self.prior_state is not None:
            require_type(
                self.prior_state, TemporaryWorkerLifecycle,
                type(self).__name__, "prior_state",
            )
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        require_nonnegative(
            self.expected_entity_revision, type(self).__name__, "expected_entity_revision",
        )
        if type(self.expected_entity_revision) is not int:
            raise TypeError("expected_entity_revision must be int")
        expected_prior, expected_result = _TRANSITIONS[self.transition]
        allowed_prior = (
            expected_prior if isinstance(expected_prior, tuple) else (expected_prior,)
        )
        if self.prior_state not in allowed_prior or self.resulting_state is not expected_result:
            raise ValueError("unsupported Temporary Worker lifecycle transition")
        if self.transition is TemporaryWorkerTransition.REQUEST:
            if self.expected_entity_revision != 0:
                raise ValueError("WorkerRequested requires nonexistent revision zero")
            if (
                self.prior_transition_event_id is not None
                or self.prior_transition_integrity_reference is not None
            ):
                raise ValueError("WorkerRequested cannot claim prior enrollment history")
        elif self.expected_entity_revision < 1:
            raise ValueError("existing Temporary Worker transition requires a positive revision")
        else:
            require_type(
                self.prior_transition_event_id, EventId,
                type(self).__name__, "prior_transition_event_id",
            )
            require_type(
                self.prior_transition_integrity_reference, IntegrityReference,
                type(self).__name__, "prior_transition_integrity_reference",
            )
        needs_current_grant = self.transition in (
            TemporaryWorkerTransition.REQUEST,
            TemporaryWorkerTransition.ACTIVATE,
            TemporaryWorkerTransition.RESTORE,
        )
        if needs_current_grant:
            require_type(
                self.source_grant_proof, SourceAuthorityGrantProof,
                type(self).__name__, "source_grant_proof",
            )
            self._validate_source_grant()
        elif self.source_grant_proof is not None:
            raise ValueError("transition does not accept unrelated current Grant evidence")
        if self.transition is TemporaryWorkerTransition.COMPLETE:
            require_type(
                self.task_assignment_evidence, TemporaryWorkerTaskAssignmentEvidence,
                type(self).__name__, "task_assignment_evidence",
            )
            require_type(
                self.task_terminal_evidence, TemporaryWorkerTaskTerminalEvidence,
                type(self).__name__, "task_terminal_evidence",
            )
            assignment = self.task_assignment_evidence
            terminal = self.task_terminal_evidence
            if assignment.organization_id != self.enrollment.organization_id:
                raise ValueError("Task assignment evidence crosses Organization boundary")
            if assignment.worker_actor_id != self.enrollment.actor_id:
                raise ValueError("Task assignment evidence names another Actor")
            if self.task_terminal_evidence.organization_id != self.enrollment.organization_id:
                raise ValueError("terminal Task evidence crosses Organization boundary")
            if self.task_terminal_evidence.worker_actor_id != self.enrollment.actor_id:
                raise ValueError("terminal Task evidence names another Actor")
            if assignment.task_id != terminal.task_id:
                raise ValueError("terminal Task differs from the enrolled Task assignment")
            if assignment.assignment_event_id == terminal.source_event_id:
                raise ValueError("Task assignment and terminal outcome require distinct Events")
            if assignment.assignment_stream_position >= terminal.source_stream_position:
                raise ValueError("terminal Task outcome must follow Task assignment")
        elif (
            self.task_assignment_evidence is not None
            or self.task_terminal_evidence is not None
        ):
            raise ValueError("non-completion transition cannot claim Task relationship evidence")
        object.__setattr__(self, "transition_evidence_references", _canonical_evidence(
            self.transition_evidence_references,
            record_type=type(self).__name__,
            field_path="transition_evidence_references",
        ))

    def _validate_source_grant(self) -> None:
        proof = self.source_grant_proof
        assert proof is not None
        enrollment = self.enrollment
        if proof.claim_command_id != self.command_id:
            raise ValueError("source Grant proof does not bind the transition Command")
        if proof.organization_id != enrollment.organization_id:
            raise ValueError("source Grant proof crosses Organization boundary")
        if proof.authority_grant_id != enrollment.source_authority_grant_id:
            raise ValueError("source Grant identity differs from enrollment")
        if proof.grantor_actor_id != enrollment.sponsor_actor.actor_id:
            raise ValueError("source Grant issuer differs from Sponsor")
        if proof.authorized_subject_actor_id != enrollment.actor_id:
            raise ValueError("source Grant recipient differs from Temporary Worker Actor")
        if proof.purpose != enrollment.purpose:
            raise ValueError("source Grant purpose differs from enrollment purpose")
        if proof.evaluation_time != self.evaluation_time:
            raise ValueError("source Grant proof is not evaluated for this transition")
        if proof.resource_ceiling.authorized_limit < 1:
            raise ValueError("source Grant lacks the first-worker Resource ceiling")
        if proof.completion_condition != enrollment.bounds.completion_condition.value:
            raise ValueError("source Grant completion condition differs from enrollment")
        if proof.grant_evidence_reference != enrollment.source_grant_evidence_reference:
            raise ValueError("source Grant evidence differs from enrollment lineage")


@dataclass(frozen=True, slots=True)
class _TemporaryWorkerAcceptedEventProof:
    """Shared immutable accepted-Event evidence; not an evaluator result."""

    claim: TemporaryWorkerTransitionClaim
    resulting_entity_revision: int
    source_event_id: EventId
    source_stream_position: int
    audit_record_id: AuditRecordId
    accepted_evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1
    atomic_append_reference: IntegrityReference | None = None
    event_integrity_reference: IntegrityReference | None = None

    def __post_init__(self) -> None:
        for name, expected in (
            ("claim", TemporaryWorkerTransitionClaim),
            ("source_event_id", EventId),
            ("audit_record_id", AuditRecordId),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        if self.atomic_append_reference is not None:
            require_type(
                self.atomic_append_reference, IntegrityReference,
                type(self).__name__, "atomic_append_reference",
            )
        if self.event_integrity_reference is not None:
            require_type(
                self.event_integrity_reference, IntegrityReference,
                type(self).__name__, "event_integrity_reference",
            )
        require_positive(
            self.resulting_entity_revision, type(self).__name__, "resulting_entity_revision",
        )
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if type(self.resulting_entity_revision) is not int:
            raise TypeError("resulting_entity_revision must be int")
        if type(self.source_stream_position) is not int:
            raise TypeError("source_stream_position must be int")
        if self.resulting_entity_revision != self.claim.expected_entity_revision + 1:
            raise ValueError("accepted transition revision must advance exactly once")
        object.__setattr__(self, "accepted_evidence_references", _canonical_evidence(
            self.accepted_evidence_references,
            record_type=type(self).__name__,
            field_path="accepted_evidence_references",
        ))


@dataclass(frozen=True, slots=True)
class TemporaryWorkerTransitionProof(_TemporaryWorkerAcceptedEventProof):
    """Replay-sufficient accepted evidence for a non-completion transition."""

    def __post_init__(self) -> None:
        super(TemporaryWorkerTransitionProof, self).__post_init__()
        if self.claim.transition is TemporaryWorkerTransition.COMPLETE:
            raise ValueError("WorkerCompleted requires the paired atomic Task terminal proof")
        if self.atomic_append_reference is not None:
            raise ValueError("non-completion Worker transition cannot claim terminal append coupling")


@dataclass(frozen=True, slots=True)
class TemporaryWorkerCompletionEventProof(_TemporaryWorkerAcceptedEventProof):
    """WorkerCompleted component accepted only with its terminal Task Event."""

    def __post_init__(self) -> None:
        super(TemporaryWorkerCompletionEventProof, self).__post_init__()
        if self.claim.transition is not TemporaryWorkerTransition.COMPLETE:
            raise ValueError("Worker completion Event proof requires WorkerCompleted")
        require_type(
            self.atomic_append_reference, IntegrityReference,
            type(self).__name__, "atomic_append_reference",
        )
        require_type(
            self.event_integrity_reference, IntegrityReference,
            type(self).__name__, "event_integrity_reference",
        )


_TEMPORARY_WORKER_DENIAL_CODES = frozenset({
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
    ReasonCode.RESOURCE_EXCEEDED,
    ReasonCode.LIFECYCLE_INVALID_TRANSITION,
    ReasonCode.STATE_STALE_VERSION,
    ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
    ReasonCode.INTEGRITY_VERIFICATION_FAILED,
})


@dataclass(frozen=True, slots=True)
class TemporaryWorkerEnrollmentDenied:
    claim_command_id: CommandId
    reason_code: ReasonCode
    failed_gate: TemporaryWorkerGate
    safe_detail: str
    diagnostic_facts: FrozenMap = field(default_factory=FrozenMap)
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.claim_command_id, CommandId, type(self).__name__, "claim_command_id")
        require_type(self.reason_code, ReasonCode, type(self).__name__, "reason_code")
        require_type(self.failed_gate, TemporaryWorkerGate, type(self).__name__, "failed_gate")
        require_nonempty(self.safe_detail, type(self).__name__, "safe_detail")
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        if self.reason_code not in _TEMPORARY_WORKER_DENIAL_CODES:
            raise ValueError("reason code is invalid for Temporary Worker enrollment denial")
        object.__setattr__(self, "diagnostic_facts", FrozenMap(self.diagnostic_facts))


TemporaryWorkerEnrollmentResolution = (
    TemporaryWorkerTransitionProof | TemporaryWorkerEnrollmentDenied
)


class TemporaryWorkerEnrollmentEvaluator(Protocol):
    """Capability-neutral pure boundary over supplied immutable evidence."""

    def evaluate(
        self, claim: TemporaryWorkerTransitionClaim,
    ) -> TemporaryWorkerEnrollmentResolution: ...
