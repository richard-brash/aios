from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timedelta, timezone

from aios_protocol.admission import AdmissionEstablished
from aios_protocol.authority import (
    ACCEPTED_DELEGATED_EXECUTION_UNIT, SourceAuthorityGrantClaim,
    SourceAuthorityGrantLifecycle, SourceAuthorityGrantProof,
    SourceGrantResourceCeiling, TaskResourceBound,
)
from aios_protocol.commands import DutyWorkRoot, ResourceDimension, Reversibility, RiskClass
from aios_protocol.governed_task import (
    AcceptedDelegatedCapabilityExecutionEvidence, AtomicTaskTerminalTransitionProof,
    ConstrainedTaskProfile, FirstWorkerTaskBudget, GovernedTaskInput,
    TaskGate, TaskIssuanceAuthorityEvidence, TaskLifecycle, TaskLifecycleEvaluator,
    TaskOutcomeEvidence, TaskPriorTransitionEvidence, TaskTransition,
    TaskTransitionClaim, TaskTransitionDenied, TaskTransitionProof,
    TaskTerminalEventProof, TaskTransitionResolution, TaskWorkerQualificationEvidence,
)
from aios_protocol.identifiers import (
    ActorId, AuditRecordId, AuthorityGrantId, BudgetId, CapabilityId, CommandId,
    EventId, IntegrityReference, MessageId, OrganizationId, ResourceId, RoleAssignmentId,
    RoleId, TaskId,
)
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.role_assignment import (
    ActiveRoleEvidence, RoleAssignmentAuthorityEvidence, RoleAssignmentLifecycle,
    RoleAssignmentPriorTransitionEvidence, RoleAssignmentProfile,
    RoleAssignmentQualificationEvidence,
    RoleAssignmentTransition, RoleAssignmentTransitionClaim,
    RoleAssignmentTransitionProof, RoleLifecycleState,
)
from aios_protocol.temporary_worker import (
    ActorEnrollmentEvidence, ActorIdentityState, ActorKind, FirstTemporaryWorkerBounds,
    TemporaryWorkerCompletionCondition, TemporaryWorkerEnrollment,
    TemporaryWorkerLifecycle, TemporaryWorkerTaskAssignmentEvidence,
    TemporaryWorkerTaskTerminalEvidence, TemporaryWorkerTaskTerminalState,
    TemporaryWorkerCompletionEventProof, TemporaryWorkerTransition,
    TemporaryWorkerTransitionClaim,
    TemporaryWorkerTransitionProof,
)
from aios_protocol.validation import FrozenMap, StructuralValidationError
from aios_protocol.versions import RECORD_V1, RecordTypeVersion


T = datetime(2034, 5, 6, 7, 8, tzinfo=timezone.utc)
ORG = OrganizationId("org:alpha")
WORKER = ActorId("actor:worker")
SPONSOR = ActorId("actor:sponsor")
TASK = TaskId("task:first")
ROLE = RoleId("role:operator")
ASSIGNMENT = RoleAssignmentId("role-assignment:first")
GRANT = AuthorityGrantId("grant:worker")
CAPABILITY = CapabilityId("role.create")


def actor(actor_id: ActorId, kind: ActorKind) -> ActorEnrollmentEvidence:
    return ActorEnrollmentEvidence(
        ORG, actor_id, kind, ActorIdentityState.ACTIVE, 1,
        EventId(f"event:{str(actor_id).split(':')[1]}"), 2,
        IntegrityReference(f"integrity:{actor_id}"),
    )


def grant(command_id: CommandId) -> SourceAuthorityGrantProof:
    return SourceAuthorityGrantProof(
        command_id, ORG, GRANT, SPONSOR, WORKER,
        AuthorityGrantId("grant:parent"), "bounded-role-maintenance",
        (CAPABILITY,), (),
        SourceGrantResourceCeiling(
            ResourceId("resource:delegated"),
            ResourceDimension.ACCEPTED_DELEGATED_CAPABILITY_EXECUTION,
            ACCEPTED_DELEGATED_EXECUTION_UNIT, 1,
        ),
        "task_terminal", SourceAuthorityGrantLifecycle.ACTIVE, T,
        T - timedelta(days=1), 1, EventId("event:grant"), 5,
        IntegrityReference("integrity:grant"),
        IntegrityReference("integrity:delegation"), True,
        (IntegrityReference("evidence:grant"),),
    )


def enrollment() -> TemporaryWorkerEnrollment:
    return TemporaryWorkerEnrollment(
        actor(WORKER, ActorKind.TEMPORARY_WORKER), actor(SPONSOR, ActorKind.HUMAN),
        "bounded-role-maintenance", GRANT, IntegrityReference("integrity:grant"),
        FirstTemporaryWorkerBounds(
            1, 1, 1, TemporaryWorkerCompletionCondition.TASK_TERMINAL, False, False,
        ),
        (IntegrityReference("evidence:enrollment"),),
    )


def active_enrollment() -> TemporaryWorkerTransitionProof:
    command_id = CommandId("command:worker-active")
    claim = TemporaryWorkerTransitionClaim(
        command_id, enrollment(), TemporaryWorkerTransition.ACTIVATE,
        TemporaryWorkerLifecycle.REQUESTED, TemporaryWorkerLifecycle.ACTIVE, 1,
        EventId("event:worker-request"), IntegrityReference("integrity:worker-request"),
        T, grant(command_id), None, None,
        (IntegrityReference("evidence:worker-active"),),
    )
    return TemporaryWorkerTransitionProof(
        claim, 2, EventId("event:worker-active"), 8,
        AuditRecordId("audit:worker-active"),
        (IntegrityReference("evidence:worker-active-accepted"),),
    )


def role_qualification(command_id: CommandId) -> RoleAssignmentQualificationEvidence:
    authority = RoleAssignmentAuthorityEvidence(
        command_id, ORG, SPONSOR, AuthorityGrantId("grant:assigner"), WORKER, ROLE,
        True, SourceAuthorityGrantLifecycle.ACTIVE, T, 1,
        EventId("event:assigner-authority"), 10,
        IntegrityReference("integrity:assigner-authority"),
        (IntegrityReference("evidence:assigner-authority"),),
    )
    return RoleAssignmentQualificationEvidence(
        command_id, T, 10, IntegrityReference("integrity:qualification"),
        active_enrollment(),
        ActiveRoleEvidence(
            ORG, ROLE, RoleLifecycleState.ACTIVE, 2,
            EventId("event:role-active"), 9, IntegrityReference("integrity:role-active"),
        ),
        actor(SPONSOR, ActorKind.HUMAN), authority,
        (IntegrityReference("evidence:qualification"),),
    )


def active_assignment() -> RoleAssignmentTransitionProof:
    command_id = CommandId("command:assignment-active")
    profile = RoleAssignmentProfile(
        ASSIGNMENT, ORG, WORKER, ROLE, SPONSOR, 2, T - timedelta(days=1),
        "bounded role maintenance", "task terminal",
        IntegrityReference("condition:task-terminal"),
        (IntegrityReference("evidence:assignment-profile"),),
    )
    claim = RoleAssignmentTransitionClaim(
        command_id, profile, RoleAssignmentTransition.PROPOSE, None,
        RoleAssignmentLifecycle.PROPOSED, 0, None, T,
        role_qualification(command_id), None,
        (IntegrityReference("evidence:assignment-transition"),),
    )
    # An active result is required as current immutable evidence. The proof's
    # complete accepted claim remains replay evidence for the qualification.
    active_claim = dataclasses.replace(
        claim, transition=RoleAssignmentTransition.ACTIVATE,
        prior_state=RoleAssignmentLifecycle.PROPOSED,
        resulting_state=RoleAssignmentLifecycle.ACTIVE,
        expected_entity_revision=1,
        prior_transition_evidence=RoleAssignmentPriorTransitionEvidence(
            ORG, ASSIGNMENT, RoleAssignmentLifecycle.PROPOSED, 1,
            EventId("event:assignment-proposed"), 11,
            IntegrityReference("integrity:assignment-proposed"),
        ),
    )
    return RoleAssignmentTransitionProof(
        active_claim, 2, EventId("event:assignment-active"), 12,
        AuditRecordId("audit:assignment-active"),
        (IntegrityReference("evidence:assignment-active-accepted"),),
    )


def budget() -> FirstWorkerTaskBudget:
    return FirstWorkerTaskBudget(
        TaskResourceBound(
            BudgetId("budget:task"), ResourceId("resource:delegated"),
            ResourceDimension.ACCEPTED_DELEGATED_CAPABILITY_EXECUTION,
            ACCEPTED_DELEGATED_EXECUTION_UNIT, 1,
        ),
        1, 0, (IntegrityReference("evidence:budget"),),
    )


def profile(**changes) -> ConstrainedTaskProfile:
    values = dict(
        task_id=TASK, organization_id=ORG,
        work_root=DutyWorkRoot(
            "role-maintenance", "mandate:first-worker", SPONSOR,
            "one bounded change", "task terminal",
        ),
        issuer_actor_id=SPONSOR, worker_actor_id=WORKER,
        role_assignment_id=ASSIGNMENT, role_id=ROLE,
        qualifying_role_entity_revision=2, source_authority_grant_id=GRANT,
        permitted_capability_ids=(CAPABILITY,),
        governed_input=GovernedTaskInput(
            FrozenMap({"role": "auditor"}), None,
            IntegrityReference("integrity:input"),
            (IntegrityReference("evidence:input"),),
        ),
        purpose="bounded-role-maintenance", expected_output="one draft Role",
        acceptance_criteria=("Role is draft", "No assignment is created"),
        risk=RiskClass.REVERSIBLE,
        reversibility=Reversibility(
            True, IntegrityReference("plan:restore"), "replay comparison", "before activation",
        ),
        budget=budget(),
        enrollment_evidence_reference=IntegrityReference("evidence:worker-active-accepted"),
        role_assignment_evidence_reference=IntegrityReference("evidence:assignment-active-accepted"),
        source_grant_evidence_reference=IntegrityReference("integrity:grant"),
        redelegation_permitted=False, worker_completion_condition="task_terminal",
        profile_evidence_references=(IntegrityReference("evidence:task-profile"),),
    )
    values.update(changes)
    return ConstrainedTaskProfile(**values)


def issuance(command_id: CommandId) -> TaskIssuanceAuthorityEvidence:
    bound = budget().resource_bound
    claim = SourceAuthorityGrantClaim(
        command_id, ORG, GRANT, SPONSOR, WORKER, "bounded-role-maintenance",
        (CAPABILITY,), bound, "task_terminal", T,
    )
    return TaskIssuanceAuthorityEvidence(
        claim, grant(command_id), active_enrollment(),
        8, IntegrityReference("evidence:worker-active-accepted"),
        (IntegrityReference("evidence:issuance-authority"),),
    )


def worker_qualification(command_id: CommandId) -> TaskWorkerQualificationEvidence:
    return TaskWorkerQualificationEvidence(
        command_id, T, 12, active_enrollment(), active_assignment(),
        (IntegrityReference("evidence:task-qualification"),),
    )


def admitted_worker(command_id: CommandId, **changes) -> AdmissionEstablished:
    values = dict(
        claim_message_id=MessageId(f"message:{command_id}"),
        command_id=command_id,
        organization_id=ORG,
        initiating_actor_id=WORKER,
        organization_genesis_reference=IntegrityReference("integrity:organization-genesis"),
        actor_identity_reference=IntegrityReference("integrity:worker-identity"),
        invocation_proof_reference=IntegrityReference("integrity:invocation-proof"),
        authentication_evidence_references=(IntegrityReference("integrity:authentication"),),
        admission_mechanism_reference=IntegrityReference("integrity:admission-mechanism"),
        admission_mechanism_version=RECORD_V1,
    )
    values.update(changes)
    return AdmissionEstablished(**values)


def start_evidence_references() -> tuple[IntegrityReference, ...]:
    return tuple(sorted((
        IntegrityReference("evidence:task-transition"),
        IntegrityReference("integrity:admission-mechanism"),
        IntegrityReference("integrity:authentication"),
        IntegrityReference("integrity:invocation-proof"),
        IntegrityReference("integrity:organization-genesis"),
        IntegrityReference("integrity:worker-identity"),
    ), key=str))


def accepted_execution(
    suffix: str = "one", **changes,
) -> AcceptedDelegatedCapabilityExecutionEvidence:
    values = dict(
        command_id=CommandId(f"command:execution-{suffix}"),
        organization_id=ORG,
        task_id=TASK,
        worker_actor_id=WORKER,
        capability_id=CAPABILITY,
        source_event_id=EventId(f"event:execution-{suffix}"),
        source_stream_position=25,
        integrity_reference=IntegrityReference(f"integrity:execution-{suffix}"),
    )
    values.update(changes)
    return AcceptedDelegatedCapabilityExecutionEvidence(**values)


def prior(state: TaskLifecycle, revision: int, **changes) -> TaskPriorTransitionEvidence:
    values = dict(
        organization_id=ORG, task_id=TASK, lifecycle_state=state,
        entity_revision=revision, source_event_id=EventId("event:task-prior"),
        source_stream_position=20, integrity_reference=IntegrityReference("integrity:task-prior"),
    )
    values.update(changes)
    return TaskPriorTransitionEvidence(**values)


def outcome(state: TaskLifecycle, **changes) -> TaskOutcomeEvidence:
    values = dict(
        organization_id=ORG, task_id=TASK, worker_actor_id=WORKER,
        terminal_state=state, outcome_reference=IntegrityReference("outcome:task"),
        acceptance_criteria_satisfaction_reference=(
            IntegrityReference("evidence:acceptance-criteria")
            if state is TaskLifecycle.COMPLETED else None
        ),
        accepted_execution_evidence=(),
        evidence_references=(IntegrityReference("evidence:outcome"),),
    )
    values.update(changes)
    return TaskOutcomeEvidence(**values)


def claim(transition: TaskTransition = TaskTransition.PROPOSE, **changes) -> TaskTransitionClaim:
    mapping = {
        TaskTransition.PROPOSE: (None, TaskLifecycle.PROPOSED, 0),
        TaskTransition.ACCEPT: (TaskLifecycle.PROPOSED, TaskLifecycle.READY, 1),
        TaskTransition.ASSIGN: (TaskLifecycle.READY, TaskLifecycle.ASSIGNED, 2),
        TaskTransition.START: (TaskLifecycle.ASSIGNED, TaskLifecycle.IN_PROGRESS, 3),
        TaskTransition.COMPLETE: (TaskLifecycle.IN_PROGRESS, TaskLifecycle.COMPLETED, 4),
        TaskTransition.FAIL: (TaskLifecycle.IN_PROGRESS, TaskLifecycle.FAILED, 4),
        TaskTransition.CANCEL: (TaskLifecycle.READY, TaskLifecycle.CANCELLED, 2),
    }
    prior_state, result, revision = mapping[transition]
    command_id = changes.pop("command_id", CommandId(f"command:task-{transition.value}"))
    values = dict(
        command_id=command_id, profile=profile(), transition=transition,
        prior_state=prior_state, resulting_state=result,
        expected_entity_revision=revision,
        prior_transition_evidence=(None if prior_state is None else prior(prior_state, revision)),
        evaluation_time=T,
        issuance_authority_evidence=(issuance(command_id) if transition in (TaskTransition.PROPOSE, TaskTransition.ACCEPT) else None),
        worker_qualification_evidence=(worker_qualification(command_id) if transition in (TaskTransition.ASSIGN, TaskTransition.START) else None),
        initiating_actor_admission=(admitted_worker(command_id) if transition is TaskTransition.START else None),
        outcome_evidence=(outcome(result) if transition in (TaskTransition.COMPLETE, TaskTransition.FAIL, TaskTransition.CANCEL) else None),
        transition_evidence_references=(
            start_evidence_references()
            if transition is TaskTransition.START
            else (IntegrityReference("evidence:task-transition"),)
        ),
    )
    values.update(changes)
    return TaskTransitionClaim(**values)


def task_proof(transition: TaskTransition, **changes) -> TaskTransitionProof | TaskTerminalEventProof:
    made_claim = changes.pop("claim", claim(transition))
    values = dict(
        claim=made_claim,
        resulting_entity_revision=made_claim.expected_entity_revision + 1,
        source_event_id=EventId(f"event:task-{transition.value}"),
        source_stream_position=30,
        audit_record_id=AuditRecordId("audit:terminal"),
        atomic_append_reference=IntegrityReference("append:terminal"),
        event_integrity_reference=IntegrityReference("integrity:task-terminal"),
        accepted_evidence_references=(IntegrityReference("evidence:task-accepted"),),
    )
    values.update(changes)
    proof_type = (
        TaskTerminalEventProof
        if transition in (TaskTransition.COMPLETE, TaskTransition.FAIL, TaskTransition.CANCEL)
        else TaskTransitionProof
    )
    return proof_type(**values)


def paired_terminal(transition: TaskTransition, **changes) -> AtomicTaskTerminalTransitionProof:
    task = changes.pop("task_proof", task_proof(transition))
    terminal_state = {
        TaskTransition.COMPLETE: TemporaryWorkerTaskTerminalState.COMPLETED,
        TaskTransition.FAIL: TemporaryWorkerTaskTerminalState.FAILED,
        TaskTransition.CANCEL: TemporaryWorkerTaskTerminalState.CANCELLED,
    }[transition]
    worker_claim = TemporaryWorkerTransitionClaim(
        task.claim.command_id, enrollment(), TemporaryWorkerTransition.COMPLETE,
        TemporaryWorkerLifecycle.ACTIVE, TemporaryWorkerLifecycle.COMPLETED, 2,
        EventId("event:worker-active"), IntegrityReference("integrity:worker-active"),
        T, None,
        TemporaryWorkerTaskAssignmentEvidence(
            ORG, WORKER, TASK, EventId("event:worker-active"), 8,
            IntegrityReference("integrity:worker-active"),
            EventId("event:task-assigned"), 18,
            IntegrityReference("integrity:task-assigned"),
        ),
        TemporaryWorkerTaskTerminalEvidence(
            ORG, WORKER, TASK, terminal_state, task.source_event_id,
            task.source_stream_position, task.event_integrity_reference,
        ),
        (IntegrityReference("evidence:worker-complete"),),
    )
    worker = changes.pop("worker_completion_proof", TemporaryWorkerCompletionEventProof(
        worker_claim, 3, EventId("event:worker-completed"), task.source_stream_position + 1,
        task.audit_record_id, (IntegrityReference("evidence:worker-completed"),),
        atomic_append_reference=task.atomic_append_reference,
        event_integrity_reference=IntegrityReference("integrity:worker-completed"),
    ))
    values = dict(
        task_proof=task, worker_completion_proof=worker,
        atomic_append_reference=task.atomic_append_reference,
        canonical_integrity_references=tuple(sorted((
            task.event_integrity_reference,
            IntegrityReference("integrity:task-assigned"),
            IntegrityReference("integrity:worker-active"),
            IntegrityReference("integrity:worker-completed"),
        ), key=str)),
    )
    values.update(changes)
    return AtomicTaskTerminalTransitionProof(**values)


class GovernedTaskContractTests(unittest.TestCase):
    def test_supported_lifecycle_and_revision_advancement(self):
        for transition in TaskTransition:
            with self.subTest(transition=transition):
                made = task_proof(transition)
                self.assertEqual(made.resulting_entity_revision, made.claim.expected_entity_revision + 1)

    def test_cancellation_is_closed_for_every_authoritative_source_state(self):
        for index, state in enumerate((
            TaskLifecycle.READY, TaskLifecycle.ASSIGNED, TaskLifecycle.IN_PROGRESS,
            TaskLifecycle.BLOCKED, TaskLifecycle.SUSPENDED,
        ), start=2):
            with self.subTest(state=state):
                made = claim(
                    TaskTransition.CANCEL, prior_state=state,
                    expected_entity_revision=index,
                    prior_transition_evidence=prior(state, index),
                )
                self.assertIs(made.resulting_state, TaskLifecycle.CANCELLED)

    def test_complete_fail_and_cancel_require_paired_atomic_transition(self):
        for transition in (TaskTransition.COMPLETE, TaskTransition.FAIL, TaskTransition.CANCEL):
            with self.subTest(transition=transition):
                paired = paired_terminal(transition)
                self.assertEqual(paired.task_proof.claim.command_id, paired.worker_completion_proof.claim.command_id)
                self.assertEqual(paired.task_proof.atomic_append_reference, paired.worker_completion_proof.atomic_append_reference)
                self.assertEqual(paired.worker_completion_proof.source_stream_position, paired.task_proof.source_stream_position + 1)

    def test_atomic_pair_rejects_identity_command_order_and_integrity_mismatch(self):
        valid = paired_terminal(TaskTransition.COMPLETE)
        worker = valid.worker_completion_proof
        cases = (
            dataclasses.replace(worker.claim.task_terminal_evidence, task_id=TaskId("task:other")),
            dataclasses.replace(worker.claim.task_terminal_evidence, worker_actor_id=ActorId("actor:other")),
            dataclasses.replace(worker.claim.task_terminal_evidence, organization_id=OrganizationId("org:other")),
            dataclasses.replace(worker.claim.task_terminal_evidence, integrity_reference=IntegrityReference("integrity:other")),
        )
        for terminal in cases:
            with self.subTest(terminal=terminal):
                with self.assertRaises(ValueError):
                    replaced_claim = dataclasses.replace(worker.claim, task_terminal_evidence=terminal)
                    paired_terminal(TaskTransition.COMPLETE, worker_completion_proof=dataclasses.replace(worker, claim=replaced_claim))
        with self.assertRaises(ValueError):
            paired_terminal(TaskTransition.COMPLETE, worker_completion_proof=dataclasses.replace(worker, source_stream_position=33))
        with self.assertRaises(ValueError):
            replaced_claim = dataclasses.replace(worker.claim, command_id=CommandId("command:other"))
            paired_terminal(TaskTransition.COMPLETE, worker_completion_proof=dataclasses.replace(worker, claim=replaced_claim))
        with self.assertRaises(ValueError):
            paired_terminal(
                TaskTransition.COMPLETE,
                worker_completion_proof=dataclasses.replace(
                    worker, atomic_append_reference=IntegrityReference("append:other"),
                ),
            )
        with self.assertRaises(ValueError):
            paired_terminal(
                TaskTransition.COMPLETE,
                canonical_integrity_references=tuple(sorted((
                    IntegrityReference("integrity:task-assigned"),
                    IntegrityReference("integrity:task-terminal"),
                    IntegrityReference("integrity:worker-active"),
                ), key=str)),
            )

    def test_neither_terminal_transition_is_an_accepted_resolution_alone(self):
        self.assertNotIsInstance(task_proof(TaskTransition.COMPLETE), AtomicTaskTerminalTransitionProof)
        self.assertNotIsInstance(task_proof(TaskTransition.COMPLETE), TaskTransitionResolution.__args__)
        self.assertNotIsInstance(paired_terminal(TaskTransition.COMPLETE).worker_completion_proof, AtomicTaskTerminalTransitionProof)
        self.assertIsInstance(paired_terminal(TaskTransition.COMPLETE), AtomicTaskTerminalTransitionProof)

    def test_denial_contains_no_partial_lifecycle_proof(self):
        denied = TaskTransitionDenied(
            CommandId("command:terminal"), ReasonCode.LIFECYCLE_INVALID_TRANSITION,
            TaskGate.LIFECYCLE, "Task is not in progress",
        )
        self.assertIsInstance(denied, TaskTransitionResolution.__args__)
        self.assertFalse(hasattr(denied, "task_proof"))
        self.assertFalse(hasattr(denied, "worker_completion_proof"))

    def test_successful_delegated_execution_is_not_a_lifecycle_transition(self):
        execution = accepted_execution()
        self.assertNotIsInstance(execution, (TaskTransitionProof, TemporaryWorkerTransitionProof))
        self.assertTrue(task_proof(TaskTransition.START).qualifies_delegated_execution)
        self.assertFalse(task_proof(TaskTransition.ACCEPT).qualifies_delegated_execution)

    def test_task_start_requires_exact_authenticated_worker_attribution(self):
        started = claim(TaskTransition.START)
        self.assertEqual(started.initiating_actor_admission.initiating_actor_id, WORKER)
        mismatches = (
            {"initiating_actor_id": ActorId("actor:other")},
            {"organization_id": OrganizationId("org:other")},
            {"command_id": CommandId("command:other")},
            {"schema_version": RecordTypeVersion("2.0")},
        )
        for changes in mismatches:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                claim(
                    TaskTransition.START,
                    initiating_actor_admission=dataclasses.replace(
                        admitted_worker(CommandId("command:task-start")), **changes,
                    ),
                )

    def test_qualification_alone_does_not_establish_start_command_authorship(self):
        with self.assertRaises(ValueError):
            claim(TaskTransition.START, initiating_actor_admission=None)
        with self.assertRaises(ValueError):
            claim(
                TaskTransition.START,
                transition_evidence_references=(IntegrityReference("evidence:task-transition"),),
            )

    def test_failure_and_cancellation_allow_zero_or_more_accepted_executions(self):
        failed_without = outcome(TaskLifecycle.FAILED)
        self.assertEqual(failed_without.accepted_execution_evidence, ())
        failed_with = outcome(
            TaskLifecycle.FAILED,
            accepted_execution_evidence=(accepted_execution(),),
        )
        self.assertEqual(len(failed_with.accepted_execution_evidence), 1)
        for executions in ((), (accepted_execution(),)):
            with self.subTest(executions=executions):
                cancelled = outcome(
                    TaskLifecycle.CANCELLED,
                    accepted_execution_evidence=executions,
                )
                self.assertEqual(cancelled.accepted_execution_evidence, executions)
        failed_claim = claim(
            TaskTransition.FAIL,
            outcome_evidence=outcome(
                TaskLifecycle.FAILED,
                accepted_execution_evidence=(accepted_execution(),),
            ),
        )
        self.assertEqual(
            len(paired_terminal(
                TaskTransition.FAIL,
                task_proof=task_proof(TaskTransition.FAIL, claim=failed_claim),
            ).task_proof.claim.outcome_evidence.accepted_execution_evidence),
            1,
        )
        cancelled_claim = claim(
            TaskTransition.CANCEL,
            outcome_evidence=outcome(
                TaskLifecycle.CANCELLED,
                accepted_execution_evidence=(accepted_execution(),),
            ),
        )
        self.assertEqual(
            len(paired_terminal(
                TaskTransition.CANCEL,
                task_proof=task_proof(TaskTransition.CANCEL, claim=cancelled_claim),
            ).task_proof.claim.outcome_evidence.accepted_execution_evidence),
            1,
        )

    def test_accepted_execution_lineage_is_structured_unique_and_canonical(self):
        first = accepted_execution("a")
        second = accepted_execution("b")
        with self.assertRaises(ValueError):
            outcome(TaskLifecycle.FAILED, accepted_execution_evidence=(first, first))
        with self.assertRaises(ValueError):
            outcome(TaskLifecycle.FAILED, accepted_execution_evidence=(second, first))
        with self.assertRaises((TypeError, ValueError)):
            outcome(
                TaskLifecycle.FAILED,
                accepted_execution_evidence=(IntegrityReference("execution:rejected"),),
            )
        with self.assertRaises(ValueError):
            outcome(
                TaskLifecycle.FAILED,
                accepted_execution_evidence=(
                    accepted_execution("other", task_id=TaskId("task:other")),
                ),
            )

    def test_completed_task_requires_acceptance_criteria_evidence_not_execution(self):
        completed = outcome(TaskLifecycle.COMPLETED)
        self.assertEqual(completed.accepted_execution_evidence, ())
        self.assertIsNotNone(completed.acceptance_criteria_satisfaction_reference)
        with self.assertRaises(StructuralValidationError):
            outcome(
                TaskLifecycle.COMPLETED,
                acceptance_criteria_satisfaction_reference=None,
            )

    def test_exact_capability_scope_rejects_nonexact_empty_duplicate_and_noncanonical(self):
        invalid = (
            (),
            (CAPABILITY, CAPABILITY),
            (CapabilityId("task.execute"), CAPABILITY),
            (CapabilityId("namespace:role"),),
            (CapabilityId("role."),),
            (CapabilityId("discovery:capabilities"),),
        )
        for capabilities in invalid:
            with self.subTest(capabilities=capabilities), self.assertRaises(ValueError):
                profile(permitted_capability_ids=capabilities)
        for value in ("role.*", "role.?", "role.[a]"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                CapabilityId(value)

    def test_budget_input_and_redelegation_are_closed(self):
        with self.assertRaises(ValueError):
            FirstWorkerTaskBudget(budget().resource_bound, 2, 0, (IntegrityReference("evidence:x"),))
        with self.assertRaises(ValueError):
            FirstWorkerTaskBudget(budget().resource_bound, 1, 1, (IntegrityReference("evidence:x"),))
        with self.assertRaises(ValueError):
            profile(redelegation_permitted=True)
        with self.assertRaises(ValueError):
            GovernedTaskInput(None, None, IntegrityReference("integrity:x"), (IntegrityReference("evidence:x"),))

    def test_authority_and_qualification_bind_exact_profile(self):
        with self.assertRaises(ValueError):
            claim(TaskTransition.PROPOSE, profile=profile(worker_actor_id=ActorId("actor:other")))
        with self.assertRaises(ValueError):
            claim(TaskTransition.ASSIGN, profile=profile(role_id=RoleId("role:other")))
        with self.assertRaises(ValueError):
            claim(TaskTransition.START, command_id=CommandId("command:different"), worker_qualification_evidence=worker_qualification(CommandId("command:task-start")))

    def test_prior_state_and_terminal_order_fail_closed(self):
        with self.assertRaises(ValueError):
            claim(TaskTransition.START, prior_transition_evidence=prior(TaskLifecycle.READY, 3))
        with self.assertRaises(ValueError):
            task_proof(TaskTransition.COMPLETE, source_stream_position=20)
        with self.assertRaises(ValueError):
            claim(TaskTransition.COMPLETE, prior_state=TaskLifecycle.ASSIGNED)
        with self.assertRaises(ValueError):
            task_proof(
                TaskTransition.ASSIGN,
                source_stream_position=12,
            )

    def test_records_are_frozen_comparable_and_replay_sufficient(self):
        first = paired_terminal(TaskTransition.COMPLETE)
        second = paired_terminal(TaskTransition.COMPLETE)
        self.assertEqual(first, second)
        self.assertEqual(first.task_proof.claim.profile.task_id, TASK)
        self.assertEqual(first.worker_completion_proof.claim.task_assignment_evidence.task_id, TASK)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first.task_proof.claim.profile.purpose = "changed"

    def test_evaluator_boundary_is_capability_neutral(self):
        self.assertTrue(hasattr(TaskLifecycleEvaluator, "evaluate"))
        self.assertIsInstance(
            TaskTransitionDenied(
                CommandId("command:deny"), ReasonCode.AUTH_INSUFFICIENT,
                TaskGate.SOURCE_GRANT, "source Grant is insufficient",
            ),
            TaskTransitionResolution.__args__,
        )
        fields = {item.name for item in dataclasses.fields(ConstrainedTaskProfile)}
        self.assertNotIn("role_assignment_resulting_state", fields)
        self.assertNotIn("enrollment_resulting_state", fields)
        self.assertNotIn("capability_execution_result", fields)


if __name__ == "__main__":
    unittest.main()
