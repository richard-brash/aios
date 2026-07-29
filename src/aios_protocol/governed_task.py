"""Immutable constrained Task lifecycle contracts for governed delegation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol

from .admission import AdmissionEstablished
from .authority import (
    ACCEPTED_DELEGATED_EXECUTION_UNIT,
    SourceAuthorityGrantClaim,
    SourceAuthorityGrantProof,
    TaskResourceBound,
)
from .commands import DutyWorkRoot, GoalWorkRoot, ResourceDimension, Reversibility, RiskClass, WorkRoot
from .identifiers import (
    ActorId, AuditRecordId, AuthorityGrantId, CapabilityId, CommandId, EventId,
    IntegrityReference, OrganizationId, RoleAssignmentId, RoleId, TaskId,
)
from .reason_codes import ReasonCode
from .role_assignment import (
    RoleAssignmentLifecycle, RoleAssignmentTransitionProof, RoleLifecycleState,
)
from .temporary_worker import (
    TemporaryWorkerLifecycle, TemporaryWorkerTaskAssignmentEvidence,
    TemporaryWorkerTaskTerminalEvidence, TemporaryWorkerTaskTerminalState,
    TemporaryWorkerCompletionEventProof, TemporaryWorkerTransition,
    TemporaryWorkerTransitionClaim,
    TemporaryWorkerTransitionProof,
)
from .validation import FrozenMap, require_aware, require_nonempty, require_nonnegative, require_positive, require_type
from .versions import RECORD_V1, RecordTypeVersion


class TaskLifecycle(str, Enum):
    PROPOSED = "proposed"
    READY = "ready"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskTransition(str, Enum):
    PROPOSE = "propose"
    ACCEPT = "accept"
    ASSIGN = "assign"
    START = "start"
    COMPLETE = "complete"
    FAIL = "fail"
    CANCEL = "cancel"


class TaskGate(str, Enum):
    SHAPE = "task_shape"
    ORGANIZATION = "task_organization"
    ISSUER = "task_issuer"
    WORKER = "task_worker"
    ENROLLMENT = "task_enrollment"
    ROLE_ASSIGNMENT = "task_role_assignment"
    ROLE = "task_role"
    SOURCE_GRANT = "task_source_grant"
    CAPABILITY_SCOPE = "task_capability_scope"
    INPUT = "task_input"
    BUDGET = "task_budget"
    LIFECYCLE = "task_lifecycle"
    OUTCOME = "task_outcome"
    ATOMICITY = "task_atomicity"
    EVIDENCE = "task_evidence"
    DEPENDENCY = "task_dependency"


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


def _exact_capabilities(values: tuple[CapabilityId, ...]) -> tuple[CapabilityId, ...]:
    result = tuple(values)
    if not result:
        raise ValueError("permitted_capability_ids must be nonempty")
    prohibited_markers = ("*", "?", "[", "]", "{", "}")
    prohibited_prefixes = ("namespace:", "pattern:", "prefix:", "discovery:")
    for index, capability in enumerate(result):
        require_type(capability, CapabilityId, "ConstrainedTaskProfile", f"permitted_capability_ids[{index}]")
        value = str(capability)
        if (
            any(marker in value for marker in prohibited_markers)
            or value.endswith((".", ":", "/"))
            or value.lower().startswith(prohibited_prefixes)
        ):
            raise ValueError("Task capabilities must be exact identifiers, not expressions")
    if len(set(result)) != len(result):
        raise ValueError("permitted_capability_ids must not contain duplicates")
    if result != tuple(sorted(result, key=str)):
        raise ValueError("permitted_capability_ids must use canonical lexical ordering")
    return result


@dataclass(frozen=True, slots=True)
class GovernedTaskInput:
    """One immutable governed value or one immutable governed reference."""

    inline_value: FrozenMap | None
    input_reference: IntegrityReference | None
    integrity_reference: IntegrityReference
    evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.integrity_reference, IntegrityReference, type(self).__name__, "integrity_reference")
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        if (self.inline_value is None) == (self.input_reference is None):
            raise ValueError("Task input requires exactly one inline value or governed reference")
        if self.inline_value is not None:
            object.__setattr__(self, "inline_value", FrozenMap(self.inline_value))
            if not self.inline_value:
                raise ValueError("inline governed input must be nonempty")
        if self.input_reference is not None:
            require_type(self.input_reference, IntegrityReference, type(self).__name__, "input_reference")
        object.__setattr__(self, "evidence_references", _canonical_evidence(
            self.evidence_references, record_type=type(self).__name__, field_path="evidence_references",
        ))


@dataclass(frozen=True, slots=True)
class FirstWorkerTaskBudget:
    """The immutable one-execution Task Budget; never consumption administration."""

    resource_bound: TaskResourceBound
    maximum_accepted_capability_executions: int
    consumed_accepted_capability_executions: int
    evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.resource_bound, TaskResourceBound, type(self).__name__, "resource_bound")
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        if type(self.maximum_accepted_capability_executions) is not int or self.maximum_accepted_capability_executions != 1:
            raise ValueError("first-worker Task permits exactly one accepted capability execution")
        if type(self.consumed_accepted_capability_executions) is not int or self.consumed_accepted_capability_executions != 0:
            raise ValueError("accepted Task Budget must begin unconsumed")
        bound = self.resource_bound
        if (
            bound.resource_dimension is not ResourceDimension.ACCEPTED_DELEGATED_CAPABILITY_EXECUTION
            or bound.unit != ACCEPTED_DELEGATED_EXECUTION_UNIT
            or bound.requested_limit != 1
        ):
            raise ValueError("first-worker Task Budget must bind one accepted delegated execution")
        object.__setattr__(self, "evidence_references", _canonical_evidence(
            self.evidence_references, record_type=type(self).__name__, field_path="evidence_references",
        ))

    @property
    def budget_id(self):
        return self.resource_bound.task_budget_id


@dataclass(frozen=True, slots=True)
class ConstrainedTaskProfile:
    """Immutable identity, scope, and first-worker bounds of one governed Task."""

    task_id: TaskId
    organization_id: OrganizationId
    work_root: WorkRoot
    issuer_actor_id: ActorId
    worker_actor_id: ActorId
    role_assignment_id: RoleAssignmentId
    role_id: RoleId
    qualifying_role_entity_revision: int
    source_authority_grant_id: AuthorityGrantId
    permitted_capability_ids: tuple[CapabilityId, ...]
    governed_input: GovernedTaskInput
    purpose: str
    expected_output: str
    acceptance_criteria: tuple[str, ...]
    risk: RiskClass
    reversibility: Reversibility
    budget: FirstWorkerTaskBudget
    enrollment_evidence_reference: IntegrityReference
    role_assignment_evidence_reference: IntegrityReference
    source_grant_evidence_reference: IntegrityReference
    redelegation_permitted: bool
    worker_completion_condition: str
    profile_evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("task_id", TaskId), ("organization_id", OrganizationId),
            ("issuer_actor_id", ActorId), ("worker_actor_id", ActorId),
            ("role_assignment_id", RoleAssignmentId), ("role_id", RoleId),
            ("source_authority_grant_id", AuthorityGrantId),
            ("governed_input", GovernedTaskInput), ("risk", RiskClass),
            ("reversibility", Reversibility), ("budget", FirstWorkerTaskBudget),
            ("enrollment_evidence_reference", IntegrityReference),
            ("role_assignment_evidence_reference", IntegrityReference),
            ("source_grant_evidence_reference", IntegrityReference),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        if type(self.work_root) not in (GoalWorkRoot, DutyWorkRoot):
            raise TypeError("Task requires exactly one concrete Work Root")
        require_positive(self.qualifying_role_entity_revision, type(self).__name__, "qualifying_role_entity_revision")
        if type(self.qualifying_role_entity_revision) is not int:
            raise TypeError("qualifying_role_entity_revision must be int")
        for name in ("purpose", "expected_output", "worker_completion_condition"):
            require_nonempty(getattr(self, name), type(self).__name__, name)
        if self.worker_completion_condition != "task_terminal":
            raise ValueError("first-worker completion condition must be Task terminality")
        criteria = tuple(self.acceptance_criteria)
        if not criteria or any(not isinstance(item, str) or not item.strip() for item in criteria):
            raise ValueError("acceptance_criteria must be nonempty exact text")
        if len(set(criteria)) != len(criteria):
            raise ValueError("acceptance_criteria must not contain duplicates")
        if type(self.redelegation_permitted) is not bool or self.redelegation_permitted:
            raise ValueError("first-worker Task redelegation must be prohibited")
        object.__setattr__(self, "acceptance_criteria", criteria)
        object.__setattr__(self, "permitted_capability_ids", _exact_capabilities(self.permitted_capability_ids))
        object.__setattr__(self, "profile_evidence_references", _canonical_evidence(
            self.profile_evidence_references, record_type=type(self).__name__, field_path="profile_evidence_references",
        ))


@dataclass(frozen=True, slots=True)
class TaskIssuanceAuthorityEvidence:
    """Source-Grant attenuation bound to one exact Task transition Command."""

    claim: SourceAuthorityGrantClaim
    proof: SourceAuthorityGrantProof
    enrollment_proof: TemporaryWorkerTransitionProof
    observed_organization_stream_position: int
    current_enrollment_reference: IntegrityReference
    evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.claim, SourceAuthorityGrantClaim, type(self).__name__, "claim")
        require_type(self.proof, SourceAuthorityGrantProof, type(self).__name__, "proof")
        require_type(
            self.enrollment_proof, TemporaryWorkerTransitionProof,
            type(self).__name__, "enrollment_proof",
        )
        require_type(
            self.current_enrollment_reference, IntegrityReference,
            type(self).__name__, "current_enrollment_reference",
        )
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        self.proof.validate_claim(self.claim)
        if self.enrollment_proof.claim.resulting_state is not TemporaryWorkerLifecycle.ACTIVE:
            raise ValueError("Task issuance requires active Temporary Worker enrollment")
        require_positive(
            self.observed_organization_stream_position,
            type(self).__name__, "observed_organization_stream_position",
        )
        if type(self.observed_organization_stream_position) is not int:
            raise TypeError("observed_organization_stream_position must be int")
        if max(
            self.enrollment_proof.source_stream_position,
            self.proof.source_stream_position,
        ) > self.observed_organization_stream_position:
            raise ValueError("Task issuance observation predates authoritative evidence")
        object.__setattr__(self, "evidence_references", _canonical_evidence(
            self.evidence_references, record_type=type(self).__name__, field_path="evidence_references",
        ))


@dataclass(frozen=True, slots=True)
class TaskWorkerQualificationEvidence:
    """Current active enrollment and Role Assignment evidence for assignment/start."""

    claim_command_id: CommandId
    evaluation_time: datetime
    observed_organization_stream_position: int
    enrollment_proof: TemporaryWorkerTransitionProof
    role_assignment_proof: RoleAssignmentTransitionProof
    evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.claim_command_id, CommandId, type(self).__name__, "claim_command_id")
        require_type(self.enrollment_proof, TemporaryWorkerTransitionProof, type(self).__name__, "enrollment_proof")
        require_type(self.role_assignment_proof, RoleAssignmentTransitionProof, type(self).__name__, "role_assignment_proof")
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        require_positive(self.observed_organization_stream_position, type(self).__name__, "observed_organization_stream_position")
        if type(self.observed_organization_stream_position) is not int:
            raise TypeError("observed_organization_stream_position must be int")
        if self.enrollment_proof.claim.resulting_state is not TemporaryWorkerLifecycle.ACTIVE:
            raise ValueError("Task requires active Temporary Worker enrollment")
        if self.role_assignment_proof.claim.resulting_state is not RoleAssignmentLifecycle.ACTIVE:
            raise ValueError("Task requires active Role Assignment")
        if self.role_assignment_proof.source_stream_position > self.observed_organization_stream_position:
            raise ValueError("Task qualification predates Role Assignment evidence")
        if self.enrollment_proof.source_stream_position > self.observed_organization_stream_position:
            raise ValueError("Task qualification predates enrollment evidence")
        object.__setattr__(self, "evidence_references", _canonical_evidence(
            self.evidence_references, record_type=type(self).__name__, field_path="evidence_references",
        ))

    @property
    def organization_id(self) -> OrganizationId:
        return self.enrollment_proof.claim.enrollment.organization_id

    @property
    def worker_actor_id(self) -> ActorId:
        return self.enrollment_proof.claim.enrollment.actor_id


@dataclass(frozen=True, slots=True)
class TaskPriorTransitionEvidence:
    organization_id: OrganizationId
    task_id: TaskId
    lifecycle_state: TaskLifecycle
    entity_revision: int
    source_event_id: EventId
    source_stream_position: int
    integrity_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("organization_id", OrganizationId), ("task_id", TaskId),
            ("lifecycle_state", TaskLifecycle), ("source_event_id", EventId),
            ("integrity_reference", IntegrityReference), ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_positive(self.entity_revision, type(self).__name__, "entity_revision")
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")


@dataclass(frozen=True, slots=True)
class AcceptedDelegatedCapabilityExecutionEvidence:
    """Historical accepted execution lineage; never a Task transition or attempt."""

    command_id: CommandId
    organization_id: OrganizationId
    task_id: TaskId
    worker_actor_id: ActorId
    capability_id: CapabilityId
    source_event_id: EventId
    source_stream_position: int
    integrity_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("command_id", CommandId), ("organization_id", OrganizationId),
            ("task_id", TaskId), ("worker_actor_id", ActorId),
            ("capability_id", CapabilityId), ("source_event_id", EventId),
            ("integrity_reference", IntegrityReference), ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if type(self.source_stream_position) is not int:
            raise TypeError("source_stream_position must be int")


@dataclass(frozen=True, slots=True)
class TaskOutcomeEvidence:
    organization_id: OrganizationId
    task_id: TaskId
    worker_actor_id: ActorId
    terminal_state: TaskLifecycle
    outcome_reference: IntegrityReference
    acceptance_criteria_satisfaction_reference: IntegrityReference | None
    accepted_execution_evidence: tuple["AcceptedDelegatedCapabilityExecutionEvidence", ...]
    evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("organization_id", OrganizationId), ("task_id", TaskId),
            ("worker_actor_id", ActorId), ("terminal_state", TaskLifecycle),
            ("outcome_reference", IntegrityReference), ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        if self.terminal_state not in (TaskLifecycle.COMPLETED, TaskLifecycle.FAILED, TaskLifecycle.CANCELLED):
            raise ValueError("Task outcome must name a terminal state")
        if self.terminal_state is TaskLifecycle.COMPLETED:
            require_type(
                self.acceptance_criteria_satisfaction_reference, IntegrityReference,
                type(self).__name__, "acceptance_criteria_satisfaction_reference",
            )
        elif self.acceptance_criteria_satisfaction_reference is not None:
            raise ValueError("only TaskCompleted may claim acceptance-criteria satisfaction")
        executions = tuple(self.accepted_execution_evidence)
        for index, item in enumerate(executions):
            require_type(
                item, AcceptedDelegatedCapabilityExecutionEvidence,
                type(self).__name__, f"accepted_execution_evidence[{index}]",
            )
            if (
                item.organization_id != self.organization_id
                or item.task_id != self.task_id
                or item.worker_actor_id != self.worker_actor_id
            ):
                raise ValueError("accepted execution evidence names another Task boundary")
        keys = tuple(item.integrity_reference for item in executions)
        if len(set(keys)) != len(keys):
            raise ValueError("accepted execution evidence must not contain duplicates")
        if executions != tuple(sorted(executions, key=lambda item: str(item.integrity_reference))):
            raise ValueError("accepted execution evidence must use canonical integrity ordering")
        object.__setattr__(self, "accepted_execution_evidence", executions)
        object.__setattr__(self, "evidence_references", _canonical_evidence(
            self.evidence_references, record_type=type(self).__name__, field_path="evidence_references",
        ))


_TRANSITIONS = {
    TaskTransition.PROPOSE: ((None,), TaskLifecycle.PROPOSED),
    TaskTransition.ACCEPT: ((TaskLifecycle.PROPOSED,), TaskLifecycle.READY),
    TaskTransition.ASSIGN: ((TaskLifecycle.READY,), TaskLifecycle.ASSIGNED),
    TaskTransition.START: ((TaskLifecycle.ASSIGNED,), TaskLifecycle.IN_PROGRESS),
    TaskTransition.COMPLETE: ((TaskLifecycle.IN_PROGRESS,), TaskLifecycle.COMPLETED),
    TaskTransition.FAIL: ((TaskLifecycle.IN_PROGRESS,), TaskLifecycle.FAILED),
    TaskTransition.CANCEL: ((TaskLifecycle.READY, TaskLifecycle.ASSIGNED, TaskLifecycle.IN_PROGRESS, TaskLifecycle.BLOCKED, TaskLifecycle.SUSPENDED), TaskLifecycle.CANCELLED),
}


@dataclass(frozen=True, slots=True)
class TaskTransitionClaim:
    """One pure constrained Task transition over supplied immutable evidence."""

    command_id: CommandId
    profile: ConstrainedTaskProfile
    transition: TaskTransition
    prior_state: TaskLifecycle | None
    resulting_state: TaskLifecycle
    expected_entity_revision: int
    prior_transition_evidence: TaskPriorTransitionEvidence | None
    evaluation_time: datetime
    issuance_authority_evidence: TaskIssuanceAuthorityEvidence | None
    worker_qualification_evidence: TaskWorkerQualificationEvidence | None
    initiating_actor_admission: AdmissionEstablished | None
    outcome_evidence: TaskOutcomeEvidence | None
    transition_evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("command_id", CommandId), ("profile", ConstrainedTaskProfile),
            ("transition", TaskTransition), ("resulting_state", TaskLifecycle),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        if self.prior_state is not None:
            require_type(self.prior_state, TaskLifecycle, type(self).__name__, "prior_state")
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        require_nonnegative(self.expected_entity_revision, type(self).__name__, "expected_entity_revision")
        allowed_prior, result = _TRANSITIONS[self.transition]
        if self.prior_state not in allowed_prior or self.resulting_state is not result:
            raise ValueError("unsupported Task lifecycle transition")
        if self.transition is TaskTransition.PROPOSE:
            if self.expected_entity_revision != 0 or self.prior_transition_evidence is not None:
                raise ValueError("TaskProposed requires nonexistent revision zero")
        else:
            require_type(self.prior_transition_evidence, TaskPriorTransitionEvidence, type(self).__name__, "prior_transition_evidence")
            prior = self.prior_transition_evidence
            if (
                prior.organization_id != self.profile.organization_id
                or prior.task_id != self.profile.task_id
                or prior.lifecycle_state is not self.prior_state
                or prior.entity_revision != self.expected_entity_revision
            ):
                raise ValueError("prior Task evidence is stale or contradictory")
        if self.transition in (TaskTransition.PROPOSE, TaskTransition.ACCEPT):
            require_type(self.issuance_authority_evidence, TaskIssuanceAuthorityEvidence, type(self).__name__, "issuance_authority_evidence")
            self._validate_authority()
        elif self.issuance_authority_evidence is not None:
            raise ValueError("transition does not accept unrelated issuance authority")
        if self.transition in (TaskTransition.ASSIGN, TaskTransition.START):
            require_type(self.worker_qualification_evidence, TaskWorkerQualificationEvidence, type(self).__name__, "worker_qualification_evidence")
            self._validate_qualification()
        elif self.worker_qualification_evidence is not None:
            raise ValueError("transition does not accept unrelated worker qualification")
        if self.transition is TaskTransition.START:
            require_type(
                self.initiating_actor_admission, AdmissionEstablished,
                type(self).__name__, "initiating_actor_admission",
            )
            self._validate_start_attribution()
        elif self.initiating_actor_admission is not None:
            raise ValueError("only TaskStarted accepts initiating-Actor admission evidence")
        terminal = self.transition in (TaskTransition.COMPLETE, TaskTransition.FAIL, TaskTransition.CANCEL)
        if terminal:
            require_type(self.outcome_evidence, TaskOutcomeEvidence, type(self).__name__, "outcome_evidence")
            if (
                self.outcome_evidence.organization_id != self.profile.organization_id
                or self.outcome_evidence.task_id != self.profile.task_id
                or self.outcome_evidence.worker_actor_id != self.profile.worker_actor_id
                or self.outcome_evidence.terminal_state is not self.resulting_state
            ):
                raise ValueError("Task outcome evidence is inconsistent")
        elif self.outcome_evidence is not None:
            raise ValueError("nonterminal Task transition cannot claim outcome evidence")
        object.__setattr__(self, "transition_evidence_references", _canonical_evidence(
            self.transition_evidence_references, record_type=type(self).__name__, field_path="transition_evidence_references",
        ))

    def _validate_start_attribution(self) -> None:
        admission = self.initiating_actor_admission
        assert admission is not None
        if admission.schema_version != RECORD_V1 or admission.admission_mechanism_version != RECORD_V1:
            raise ValueError("TaskStarted admission attribution is stale or unsupported")
        if admission.command_id != self.command_id:
            raise ValueError("TaskStarted admission attributes another Command")
        if admission.organization_id != self.profile.organization_id:
            raise ValueError("TaskStarted admission crosses Organization boundary")
        if admission.initiating_actor_id != self.profile.worker_actor_id:
            raise ValueError("TaskStarted must be initiated by the assigned Worker Actor")
        required_lineage = {
            admission.organization_genesis_reference,
            admission.actor_identity_reference,
            admission.invocation_proof_reference,
            admission.admission_mechanism_reference,
            *admission.authentication_evidence_references,
        }
        if not required_lineage.issubset(self.transition_evidence_references):
            raise ValueError("TaskStarted lacks immutable admission integrity lineage")

    def _validate_authority(self) -> None:
        evidence = self.issuance_authority_evidence
        assert evidence is not None
        claim = evidence.claim
        profile = self.profile
        if (
            claim.command_id != self.command_id
            or claim.organization_id != profile.organization_id
            or claim.authority_grant_id != profile.source_authority_grant_id
            or claim.grantor_actor_id != profile.issuer_actor_id
            or claim.authorized_subject_actor_id != profile.worker_actor_id
            or claim.purpose != profile.purpose
            or claim.requested_capabilities != profile.permitted_capability_ids
            or claim.requested_resource_ceiling != profile.budget.resource_bound
            or claim.completion_condition != profile.worker_completion_condition
            or claim.evaluation_time != self.evaluation_time
            or evidence.proof.grant_evidence_reference != profile.source_grant_evidence_reference
            or evidence.enrollment_proof.claim.enrollment.organization_id != profile.organization_id
            or evidence.enrollment_proof.claim.enrollment.actor_id != profile.worker_actor_id
            or evidence.enrollment_proof.claim.enrollment.sponsor_actor.actor_id != profile.issuer_actor_id
            or profile.enrollment_evidence_reference not in evidence.enrollment_proof.accepted_evidence_references
            or evidence.current_enrollment_reference != profile.enrollment_evidence_reference
        ):
            raise ValueError("Task issuance authority does not bind the exact Task scope")

    def _validate_qualification(self) -> None:
        evidence = self.worker_qualification_evidence
        assert evidence is not None
        profile = self.profile
        assignment = evidence.role_assignment_proof.claim.profile
        if evidence.claim_command_id != self.command_id or evidence.evaluation_time != self.evaluation_time:
            raise ValueError("Task qualification does not bind the Command and evaluation point")
        if evidence.organization_id != profile.organization_id or evidence.worker_actor_id != profile.worker_actor_id:
            raise ValueError("Task qualification crosses Organization or Worker boundary")
        if (
            assignment.role_assignment_id != profile.role_assignment_id
            or assignment.role_id != profile.role_id
            or assignment.qualifying_role_entity_revision != profile.qualifying_role_entity_revision
            or assignment.organization_id != profile.organization_id
            or assignment.worker_actor_id != profile.worker_actor_id
            or evidence.role_assignment_proof.claim.resulting_state is not RoleAssignmentLifecycle.ACTIVE
        ):
            raise ValueError("Task qualification names an inactive or different Role Assignment")
        qualification = evidence.role_assignment_proof.claim.qualification_evidence
        if qualification is None or qualification.role_evidence.lifecycle_state is not RoleLifecycleState.ACTIVE:
            raise ValueError("Task qualification lacks active exact Role evidence")
        if profile.enrollment_evidence_reference not in evidence.enrollment_proof.accepted_evidence_references:
            raise ValueError("Task enrollment evidence differs from pinned profile")
        if profile.role_assignment_evidence_reference not in evidence.role_assignment_proof.accepted_evidence_references:
            raise ValueError("Task Role Assignment evidence differs from pinned profile")


@dataclass(frozen=True, slots=True)
class _TaskAcceptedEventProof:
    """Shared immutable accepted-Event evidence; not an evaluator result."""

    claim: TaskTransitionClaim
    resulting_entity_revision: int
    source_event_id: EventId
    source_stream_position: int
    audit_record_id: AuditRecordId
    atomic_append_reference: IntegrityReference
    event_integrity_reference: IntegrityReference
    accepted_evidence_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("claim", TaskTransitionClaim), ("source_event_id", EventId),
            ("audit_record_id", AuditRecordId), ("atomic_append_reference", IntegrityReference),
            ("event_integrity_reference", IntegrityReference), ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        require_positive(self.resulting_entity_revision, type(self).__name__, "resulting_entity_revision")
        require_positive(self.source_stream_position, type(self).__name__, "source_stream_position")
        if self.resulting_entity_revision != self.claim.expected_entity_revision + 1:
            raise ValueError("accepted Task revision must advance exactly once")
        if self.claim.prior_transition_evidence is not None and self.source_stream_position <= self.claim.prior_transition_evidence.source_stream_position:
            raise ValueError("accepted Task Event must follow prior transition evidence")
        qualification = self.claim.worker_qualification_evidence
        if qualification is not None and self.source_stream_position <= qualification.observed_organization_stream_position:
            raise ValueError("accepted Task Event must follow current qualification evidence")
        object.__setattr__(self, "accepted_evidence_references", _canonical_evidence(
            self.accepted_evidence_references, record_type=type(self).__name__, field_path="accepted_evidence_references",
        ))


@dataclass(frozen=True, slots=True)
class TaskTransitionProof(_TaskAcceptedEventProof):
    """Replay-sufficient accepted evidence for one nonterminal Task transition."""

    def __post_init__(self) -> None:
        super(TaskTransitionProof, self).__post_init__()
        if self.claim.transition in (
            TaskTransition.COMPLETE, TaskTransition.FAIL, TaskTransition.CANCEL,
        ):
            raise ValueError("terminal Task acceptance requires the paired atomic proof")

    @property
    def qualifies_delegated_execution(self) -> bool:
        return self.claim.resulting_state is TaskLifecycle.IN_PROGRESS


@dataclass(frozen=True, slots=True)
class TaskTerminalEventProof(_TaskAcceptedEventProof):
    """Terminal Task Event component accepted only inside an atomic pair."""

    def __post_init__(self) -> None:
        super(TaskTerminalEventProof, self).__post_init__()
        if self.claim.transition not in (
            TaskTransition.COMPLETE, TaskTransition.FAIL, TaskTransition.CANCEL,
        ):
            raise ValueError("Task terminal Event proof requires a terminal transition")


@dataclass(frozen=True, slots=True)
class AtomicTaskTerminalTransitionProof:
    """Indivisible terminal Task and WorkerCompleted accepted evidence."""

    task_proof: TaskTerminalEventProof
    worker_completion_proof: TemporaryWorkerCompletionEventProof
    atomic_append_reference: IntegrityReference
    canonical_integrity_references: tuple[IntegrityReference, ...]
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.task_proof, TaskTerminalEventProof, type(self).__name__, "task_proof")
        require_type(self.worker_completion_proof, TemporaryWorkerCompletionEventProof, type(self).__name__, "worker_completion_proof")
        require_type(self.atomic_append_reference, IntegrityReference, type(self).__name__, "atomic_append_reference")
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        task = self.task_proof
        worker = self.worker_completion_proof
        profile = task.claim.profile
        worker_claim = worker.claim
        if task.claim.transition not in (TaskTransition.COMPLETE, TaskTransition.FAIL, TaskTransition.CANCEL):
            raise ValueError("atomic terminal proof requires a terminal Task transition")
        if worker_claim.transition is not TemporaryWorkerTransition.COMPLETE:
            raise ValueError("atomic terminal proof requires WorkerCompleted")
        if task.claim.command_id != worker_claim.command_id:
            raise ValueError("paired terminal transitions must share one Command")
        if task.atomic_append_reference != self.atomic_append_reference or worker.atomic_append_reference != self.atomic_append_reference:
            raise ValueError("paired terminal transitions must share one atomic append boundary")
        if task.audit_record_id != worker.audit_record_id:
            raise ValueError("paired terminal transitions must share canonical audit lineage")
        assignment = worker_claim.task_assignment_evidence
        terminal = worker_claim.task_terminal_evidence
        if assignment is None or terminal is None:
            raise ValueError("WorkerCompleted lacks exact Task relationship evidence")
        expected_terminal = {
            TaskLifecycle.COMPLETED: TemporaryWorkerTaskTerminalState.COMPLETED,
            TaskLifecycle.FAILED: TemporaryWorkerTaskTerminalState.FAILED,
            TaskLifecycle.CANCELLED: TemporaryWorkerTaskTerminalState.CANCELLED,
        }[task.claim.resulting_state]
        if (
            profile.organization_id != worker_claim.enrollment.organization_id
            or profile.worker_actor_id != worker_claim.enrollment.actor_id
            or assignment.organization_id != profile.organization_id
            or assignment.worker_actor_id != profile.worker_actor_id
            or assignment.task_id != profile.task_id
            or terminal.organization_id != profile.organization_id
            or terminal.worker_actor_id != profile.worker_actor_id
            or terminal.task_id != profile.task_id
            or terminal.terminal_state is not expected_terminal
            or terminal.source_event_id != task.source_event_id
            or terminal.source_stream_position != task.source_stream_position
            or terminal.integrity_reference != task.event_integrity_reference
        ):
            raise ValueError("paired Task and Worker completion lineage is inconsistent")
        if worker.source_stream_position != task.source_stream_position + 1:
            raise ValueError("WorkerCompleted must immediately follow the terminal Task Event")
        references = _canonical_evidence(
            self.canonical_integrity_references,
            record_type=type(self).__name__, field_path="canonical_integrity_references",
        )
        required = {
            task.event_integrity_reference,
            assignment.assignment_integrity_reference,
            terminal.integrity_reference,
            worker_claim.prior_transition_integrity_reference,
            worker.event_integrity_reference,
        }
        if None in required or not required.issubset(references):
            raise ValueError("paired terminal transition lacks canonical integrity lineage")
        object.__setattr__(self, "canonical_integrity_references", references)


_TASK_DENIAL_CODES = frozenset({
    ReasonCode.INPUT_MALFORMED, ReasonCode.VER_UNSUPPORTED,
    ReasonCode.ORG_BOUNDARY_VIOLATION, ReasonCode.IDENTITY_UNKNOWN,
    ReasonCode.AUTH_MISSING, ReasonCode.AUTH_EXPIRED, ReasonCode.AUTH_REVOKED,
    ReasonCode.AUTH_INSUFFICIENT, ReasonCode.AUTH_DELEGATION_INVALID,
    ReasonCode.WORK_ROOT_MISSING, ReasonCode.WORK_ROOT_INVALID_KIND,
    ReasonCode.RESOURCE_EXCEEDED, ReasonCode.RESOURCE_UNVERIFIED,
    ReasonCode.LIFECYCLE_INVALID_TRANSITION, ReasonCode.STATE_STALE_VERSION,
    ReasonCode.STREAM_CONCURRENCY_CONFLICT, ReasonCode.AUDIT_LINKAGE_MISSING,
    ReasonCode.RELATIONSHIP_INTEGRITY_CONFLICT,
    ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
    ReasonCode.INTEGRITY_VERIFICATION_FAILED,
})


@dataclass(frozen=True, slots=True)
class TaskTransitionDenied:
    claim_command_id: CommandId
    reason_code: ReasonCode
    failed_gate: TaskGate
    safe_detail: str
    diagnostic_facts: FrozenMap = field(default_factory=FrozenMap)
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.claim_command_id, CommandId, type(self).__name__, "claim_command_id")
        require_type(self.reason_code, ReasonCode, type(self).__name__, "reason_code")
        require_type(self.failed_gate, TaskGate, type(self).__name__, "failed_gate")
        require_nonempty(self.safe_detail, type(self).__name__, "safe_detail")
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        if self.reason_code not in _TASK_DENIAL_CODES:
            raise ValueError("reason code is invalid for Task transition denial")
        object.__setattr__(self, "diagnostic_facts", FrozenMap(self.diagnostic_facts))


TaskTransitionResolution = TaskTransitionProof | AtomicTaskTerminalTransitionProof | TaskTransitionDenied


class TaskLifecycleEvaluator(Protocol):
    """Capability-neutral pure boundary over supplied immutable Task evidence."""

    def evaluate(self, claim: TaskTransitionClaim) -> TaskTransitionResolution: ...
