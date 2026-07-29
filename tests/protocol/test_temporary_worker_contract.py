from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timedelta, timezone

from aios_protocol.authority import (
    ACCEPTED_DELEGATED_EXECUTION_UNIT,
    SourceAuthorityGrantLifecycle,
    SourceAuthorityGrantProof,
    SourceGrantResourceCeiling,
)
from aios_protocol.commands import ResourceDimension
from aios_protocol.identifiers import (
    ActorId, AuditRecordId, AuthorityGrantId, CapabilityId, CommandId, EventId,
    IntegrityReference, OrganizationId, ResourceId, TaskId,
)
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import StructuralValidationError
from aios_protocol.temporary_worker import (
    ActorEnrollmentEvidence,
    ActorIdentityState,
    ActorKind,
    FirstTemporaryWorkerBounds,
    TemporaryWorkerCompletionCondition,
    TemporaryWorkerEnrollment,
    TemporaryWorkerEnrollmentDenied,
    TemporaryWorkerEnrollmentResolution,
    TemporaryWorkerGate,
    TemporaryWorkerLifecycle,
    TemporaryWorkerTaskAssignmentEvidence,
    TemporaryWorkerTaskTerminalEvidence,
    TemporaryWorkerTaskTerminalState,
    TemporaryWorkerTransition,
    TemporaryWorkerTransitionClaim,
    TemporaryWorkerTransitionProof,
)


T = datetime(2033, 2, 3, 4, 5, tzinfo=timezone.utc)


def actor(
    actor_id: str, kind: ActorKind, *,
    organization_id: OrganizationId = OrganizationId("org:alpha"),
    state: ActorIdentityState = ActorIdentityState.ACTIVE,
) -> ActorEnrollmentEvidence:
    return ActorEnrollmentEvidence(
        organization_id=organization_id,
        actor_id=ActorId(actor_id),
        actor_kind=kind,
        identity_state=state,
        actor_entity_revision=2,
        source_event_id=EventId(f"event:{actor_id.split(':')[1]}-identity"),
        source_stream_position=5,
        identity_evidence_reference=IntegrityReference(f"integrity:{actor_id}"),
    )


def bounds(**changes) -> FirstTemporaryWorkerBounds:
    values = dict(
        maximum_active_role_assignments=1,
        maximum_tasks=1,
        maximum_accepted_delegated_capability_executions=1,
        completion_condition=TemporaryWorkerCompletionCondition.TASK_TERMINAL,
        redelegation_permitted=False,
        subworker_creation_permitted=False,
    )
    values.update(changes)
    return FirstTemporaryWorkerBounds(**values)


def enrollment(**changes) -> TemporaryWorkerEnrollment:
    values = dict(
        worker_actor=actor("actor:worker", ActorKind.TEMPORARY_WORKER),
        sponsor_actor=actor("actor:sponsor", ActorKind.HUMAN),
        purpose="maintain-role-catalog",
        source_authority_grant_id=AuthorityGrantId("grant:worker-source"),
        source_grant_evidence_reference=IntegrityReference("integrity:grant"),
        bounds=bounds(),
        enrollment_evidence_references=(
            IntegrityReference("evidence:sponsor"),
            IntegrityReference("evidence:worker"),
        ),
    )
    values.update(changes)
    return TemporaryWorkerEnrollment(**values)


def grant_proof(
    command_id: CommandId = CommandId("command:worker-request"), **changes,
) -> SourceAuthorityGrantProof:
    values = dict(
        claim_command_id=command_id,
        organization_id=OrganizationId("org:alpha"),
        authority_grant_id=AuthorityGrantId("grant:worker-source"),
        grantor_actor_id=ActorId("actor:sponsor"),
        authorized_subject_actor_id=ActorId("actor:worker"),
        parent_authority_grant_id=AuthorityGrantId("grant:sponsor-parent"),
        purpose="maintain-role-catalog",
        permitted_capabilities=(CapabilityId("role.create"),),
        prohibited_capabilities=(),
        resource_ceiling=SourceGrantResourceCeiling(
            ResourceId("resource:delegated-execution"),
            ResourceDimension.ACCEPTED_DELEGATED_CAPABILITY_EXECUTION,
            ACCEPTED_DELEGATED_EXECUTION_UNIT,
            1,
        ),
        completion_condition="task_terminal",
        lifecycle_state=SourceAuthorityGrantLifecycle.ACTIVE,
        evaluation_time=T,
        effective_at=T - timedelta(days=1),
        grant_entity_revision=1,
        source_event_id=EventId("event:grant-active"),
        source_stream_position=7,
        grant_evidence_reference=IntegrityReference("integrity:grant"),
        delegation_basis_reference=IntegrityReference("integrity:delegation"),
        delegation_permitted=True,
        evidence_references=(IntegrityReference("evidence:grant"),),
    )
    values.update(changes)
    return SourceAuthorityGrantProof(**values)


def claim(**changes) -> TemporaryWorkerTransitionClaim:
    command_id = changes.pop("command_id", CommandId("command:worker-request"))
    values = dict(
        command_id=command_id,
        enrollment=enrollment(),
        transition=TemporaryWorkerTransition.REQUEST,
        prior_state=None,
        resulting_state=TemporaryWorkerLifecycle.REQUESTED,
        expected_entity_revision=0,
        prior_transition_event_id=None,
        prior_transition_integrity_reference=None,
        evaluation_time=T,
        source_grant_proof=grant_proof(command_id),
        task_assignment_evidence=None,
        task_terminal_evidence=None,
        transition_evidence_references=(IntegrityReference("evidence:request"),),
    )
    values.update(changes)
    return TemporaryWorkerTransitionClaim(**values)


def assignment_evidence(**changes) -> TemporaryWorkerTaskAssignmentEvidence:
    values = dict(
        organization_id=OrganizationId("org:alpha"),
        worker_actor_id=ActorId("actor:worker"),
        task_id=TaskId("task:first-worker"),
        enrollment_activation_event_id=EventId("event:worker-active"),
        enrollment_activation_stream_position=12,
        enrollment_activation_integrity_reference=IntegrityReference("integrity:worker-active"),
        assignment_event_id=EventId("event:task-assigned"),
        assignment_stream_position=20,
        assignment_integrity_reference=IntegrityReference("integrity:task-assigned"),
    )
    values.update(changes)
    return TemporaryWorkerTaskAssignmentEvidence(**values)


def terminal_evidence(**changes) -> TemporaryWorkerTaskTerminalEvidence:
    values = dict(
        organization_id=OrganizationId("org:alpha"),
        worker_actor_id=ActorId("actor:worker"),
        task_id=TaskId("task:first-worker"),
        terminal_state=TemporaryWorkerTaskTerminalState.COMPLETED,
        source_event_id=EventId("event:task-completed"),
        source_stream_position=29,
        integrity_reference=IntegrityReference("integrity:task-completed"),
    )
    values.update(changes)
    return TemporaryWorkerTaskTerminalEvidence(**values)


class TemporaryWorkerContractTests(unittest.TestCase):
    def test_enrollment_preserves_temporary_worker_actor_identity(self):
        record = enrollment()
        self.assertEqual(record.actor_id, ActorId("actor:worker"))
        self.assertIs(record.worker_actor.actor_kind, ActorKind.TEMPORARY_WORKER)
        self.assertNotIn("worker_id", {field.name for field in dataclasses.fields(record)})
        self.assertNotIn("task_id", {field.name for field in dataclasses.fields(record)})

    def test_worker_sponsor_and_organization_are_explicit_and_consistent(self):
        record = enrollment()
        self.assertEqual(record.organization_id, OrganizationId("org:alpha"))
        self.assertEqual(record.sponsor_actor.actor_id, ActorId("actor:sponsor"))
        with self.assertRaises(ValueError):
            enrollment(sponsor_actor=actor(
                "actor:sponsor", ActorKind.HUMAN,
                organization_id=OrganizationId("org:other"),
            ))

    def test_actor_kind_and_identity_state_fail_closed(self):
        with self.assertRaises(ValueError):
            enrollment(worker_actor=actor("actor:worker", ActorKind.SERVICE))
        with self.assertRaises(ValueError):
            enrollment(worker_actor=actor(
                "actor:worker", ActorKind.TEMPORARY_WORKER,
                state=ActorIdentityState.SUSPENDED,
            ))
        with self.assertRaises(ValueError):
            enrollment(sponsor_actor=actor("actor:sponsor", ActorKind.SERVICE))
        with self.assertRaises(ValueError):
            enrollment(sponsor_actor=actor(
                "actor:sponsor", ActorKind.HUMAN,
                state=ActorIdentityState.INACTIVE,
            ))

    def test_enrollment_is_eligibility_with_one_closed_profile_not_authority(self):
        record = enrollment()
        self.assertEqual(record.bounds.maximum_active_role_assignments, 1)
        self.assertEqual(record.bounds.maximum_tasks, 1)
        self.assertEqual(record.bounds.maximum_accepted_delegated_capability_executions, 1)
        self.assertFalse(record.bounds.redelegation_permitted)
        self.assertFalse(record.bounds.subworker_creation_permitted)
        self.assertNotIn("permitted_capabilities", {
            field.name for field in dataclasses.fields(record)
        })

    def test_malformed_bounds_and_redelegation_are_prohibited(self):
        for changes in (
            {"maximum_active_role_assignments": 2},
            {"maximum_tasks": 0},
            {"maximum_accepted_delegated_capability_executions": 2},
            {"redelegation_permitted": True},
            {"subworker_creation_permitted": True},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bounds(**changes)

    def test_request_activation_suspension_restoration_and_completion_are_closed(self):
        cases = (
            (TemporaryWorkerTransition.REQUEST, None, TemporaryWorkerLifecycle.REQUESTED, 0, True),
            (TemporaryWorkerTransition.ACTIVATE, TemporaryWorkerLifecycle.REQUESTED, TemporaryWorkerLifecycle.ACTIVE, 1, True),
            (TemporaryWorkerTransition.REVOKE_REQUEST, TemporaryWorkerLifecycle.REQUESTED, TemporaryWorkerLifecycle.REVOKED, 1, False),
            (TemporaryWorkerTransition.SUSPEND, TemporaryWorkerLifecycle.ACTIVE, TemporaryWorkerLifecycle.SUSPENDED, 2, False),
            (TemporaryWorkerTransition.RESTORE, TemporaryWorkerLifecycle.SUSPENDED, TemporaryWorkerLifecycle.ACTIVE, 3, True),
            (TemporaryWorkerTransition.COMPLETE, TemporaryWorkerLifecycle.ACTIVE, TemporaryWorkerLifecycle.COMPLETED, 4, False),
            (TemporaryWorkerTransition.REVOKE, TemporaryWorkerLifecycle.SUSPENDED, TemporaryWorkerLifecycle.REVOKED, 4, False),
            (TemporaryWorkerTransition.ARCHIVE, TemporaryWorkerLifecycle.COMPLETED, TemporaryWorkerLifecycle.ARCHIVED, 5, False),
        )
        for transition, prior, result, revision, needs_grant in cases:
            command_id = CommandId(f"command:{transition.value}")
            with self.subTest(transition=transition):
                made = claim(
                    command_id=command_id,
                    transition=transition,
                    prior_state=prior,
                    resulting_state=result,
                    expected_entity_revision=revision,
                    prior_transition_event_id=(
                        None if prior is None else EventId("event:prior-worker-state")
                    ),
                    prior_transition_integrity_reference=(
                        None if prior is None else IntegrityReference("integrity:prior-worker-state")
                    ),
                    source_grant_proof=grant_proof(command_id) if needs_grant else None,
                    task_assignment_evidence=(
                        assignment_evidence()
                        if transition is TemporaryWorkerTransition.COMPLETE else None
                    ),
                    task_terminal_evidence=(
                        terminal_evidence()
                        if transition is TemporaryWorkerTransition.COMPLETE else None
                    ),
                )
                self.assertIs(made.resulting_state, result)

    def test_invalid_or_unsupported_transitions_fail_closed(self):
        with self.assertRaises(ValueError):
            claim(
                transition=TemporaryWorkerTransition.ACTIVATE,
                prior_state=TemporaryWorkerLifecycle.SUSPENDED,
                resulting_state=TemporaryWorkerLifecycle.ACTIVE,
                expected_entity_revision=1,
            )
        with self.assertRaises(ValueError):
            claim(expected_entity_revision=2)
        with self.assertRaises(ValueError):
            claim(
                transition=TemporaryWorkerTransition.ARCHIVE,
                prior_state=TemporaryWorkerLifecycle.EXPIRED,
                resulting_state=TemporaryWorkerLifecycle.ARCHIVED,
                expected_entity_revision=2,
                prior_transition_event_id=EventId("event:worker-expired"),
                prior_transition_integrity_reference=IntegrityReference("integrity:worker-expired"),
                source_grant_proof=None,
            )
        with self.assertRaises(ValueError):
            claim(
                transition=TemporaryWorkerTransition.COMPLETE,
                prior_state=TemporaryWorkerLifecycle.ACTIVE,
                resulting_state=TemporaryWorkerLifecycle.COMPLETED,
                expected_entity_revision=2,
                prior_transition_event_id=EventId("event:worker-active"),
                prior_transition_integrity_reference=IntegrityReference("integrity:worker-active"),
                source_grant_proof=grant_proof(),
                task_assignment_evidence=assignment_evidence(),
                task_terminal_evidence=terminal_evidence(),
            )

    def test_completion_requires_same_organization_actor_terminal_task_evidence(self):
        terminal = terminal_evidence(
            terminal_state=TemporaryWorkerTaskTerminalState.FAILED,
            source_event_id=EventId("event:task-failed"),
            integrity_reference=IntegrityReference("integrity:task-failed"),
        )
        made = claim(
            transition=TemporaryWorkerTransition.COMPLETE,
            prior_state=TemporaryWorkerLifecycle.ACTIVE,
            resulting_state=TemporaryWorkerLifecycle.COMPLETED,
            expected_entity_revision=2,
            prior_transition_event_id=EventId("event:worker-active"),
            prior_transition_integrity_reference=IntegrityReference("integrity:worker-active"),
            source_grant_proof=None,
            task_assignment_evidence=assignment_evidence(),
            task_terminal_evidence=terminal,
        )
        self.assertIs(
            made.task_terminal_evidence.terminal_state,
            TemporaryWorkerTaskTerminalState.FAILED,
        )
        with self.assertRaises(ValueError):
            dataclasses.replace(
                made,
                task_terminal_evidence=dataclasses.replace(
                    terminal, organization_id=OrganizationId("org:other"),
                ),
            )
        with self.assertRaises(ValueError):
            dataclasses.replace(
                made,
                task_terminal_evidence=dataclasses.replace(
                    terminal, worker_actor_id=ActorId("actor:other"),
                ),
            )

    def test_completion_rejects_terminal_evidence_for_another_assigned_task(self):
        with self.assertRaisesRegex(ValueError, "terminal Task differs"):
            claim(
                transition=TemporaryWorkerTransition.COMPLETE,
                prior_state=TemporaryWorkerLifecycle.ACTIVE,
                resulting_state=TemporaryWorkerLifecycle.COMPLETED,
                expected_entity_revision=2,
                prior_transition_event_id=EventId("event:worker-active"),
                prior_transition_integrity_reference=IntegrityReference("integrity:worker-active"),
                source_grant_proof=None,
                task_assignment_evidence=assignment_evidence(),
                task_terminal_evidence=terminal_evidence(task_id=TaskId("task:other")),
            )

    def test_completion_rejects_assignment_for_another_worker_or_organization(self):
        for changed in (
            assignment_evidence(worker_actor_id=ActorId("actor:other")),
            assignment_evidence(organization_id=OrganizationId("org:other")),
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                claim(
                    transition=TemporaryWorkerTransition.COMPLETE,
                    prior_state=TemporaryWorkerLifecycle.ACTIVE,
                    resulting_state=TemporaryWorkerLifecycle.COMPLETED,
                    expected_entity_revision=2,
                    prior_transition_event_id=EventId("event:worker-active"),
                    prior_transition_integrity_reference=IntegrityReference("integrity:worker-active"),
                    source_grant_proof=None,
                    task_assignment_evidence=changed,
                    task_terminal_evidence=terminal_evidence(),
                )

    def test_completion_rejects_terminal_outcome_before_or_at_assignment(self):
        for position in (19, 20):
            with self.subTest(position=position), self.assertRaisesRegex(
                ValueError, "terminal Task outcome must follow",
            ):
                claim(
                    transition=TemporaryWorkerTransition.COMPLETE,
                    prior_state=TemporaryWorkerLifecycle.ACTIVE,
                    resulting_state=TemporaryWorkerLifecycle.COMPLETED,
                    expected_entity_revision=2,
                    prior_transition_event_id=EventId("event:worker-active"),
                    prior_transition_integrity_reference=IntegrityReference("integrity:worker-active"),
                    source_grant_proof=None,
                    task_assignment_evidence=assignment_evidence(),
                    task_terminal_evidence=terminal_evidence(source_stream_position=position),
                )
        with self.assertRaisesRegex(ValueError, "distinct Events"):
            claim(
                transition=TemporaryWorkerTransition.COMPLETE,
                prior_state=TemporaryWorkerLifecycle.ACTIVE,
                resulting_state=TemporaryWorkerLifecycle.COMPLETED,
                expected_entity_revision=2,
                prior_transition_event_id=EventId("event:worker-active"),
                prior_transition_integrity_reference=IntegrityReference("integrity:worker-active"),
                source_grant_proof=None,
                task_assignment_evidence=assignment_evidence(),
                task_terminal_evidence=terminal_evidence(
                    source_event_id=EventId("event:task-assigned"),
                ),
            )

    def test_assignment_lineage_is_required_well_formed_and_ordered(self):
        with self.assertRaises(StructuralValidationError):
            assignment_evidence(assignment_integrity_reference=None)
        with self.assertRaises(ValueError):
            assignment_evidence(assignment_stream_position=12)
        with self.assertRaises(ValueError):
            assignment_evidence(assignment_event_id=EventId("event:worker-active"))
        with self.assertRaises(StructuralValidationError):
            claim(
                transition=TemporaryWorkerTransition.COMPLETE,
                prior_state=TemporaryWorkerLifecycle.ACTIVE,
                resulting_state=TemporaryWorkerLifecycle.COMPLETED,
                expected_entity_revision=2,
                prior_transition_event_id=EventId("event:worker-active"),
                prior_transition_integrity_reference=IntegrityReference("integrity:worker-active"),
                source_grant_proof=None,
                task_assignment_evidence=None,
                task_terminal_evidence=terminal_evidence(),
            )

    def test_non_completion_transition_rejects_task_relationship_evidence(self):
        with self.assertRaisesRegex(ValueError, "non-completion transition"):
            claim(task_assignment_evidence=assignment_evidence())
        with self.assertRaisesRegex(ValueError, "non-completion transition"):
            claim(task_terminal_evidence=terminal_evidence())

    def test_assignment_evidence_is_immutable_comparable_and_effect_free(self):
        evidence = assignment_evidence()
        rebuilt = TemporaryWorkerTaskAssignmentEvidence(**{
            field.name: getattr(evidence, field.name)
            for field in dataclasses.fields(TemporaryWorkerTaskAssignmentEvidence)
        })
        self.assertEqual(rebuilt, evidence)
        self.assertFalse(hasattr(evidence, "repository"))
        self.assertFalse(hasattr(evidence, "clock"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            evidence.task_id = TaskId("task:changed")

    def test_source_grant_is_exact_but_does_not_make_enrollment_authority(self):
        mismatches = (
            {"organization_id": OrganizationId("org:other")},
            {"authority_grant_id": AuthorityGrantId("grant:other")},
            {"grantor_actor_id": ActorId("actor:other")},
            {"authorized_subject_actor_id": ActorId("actor:other")},
            {"purpose": "other-purpose"},
            {"grant_evidence_reference": IntegrityReference("integrity:other")},
        )
        for changes in mismatches:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                claim(source_grant_proof=grant_proof(**changes))

    def test_accepted_proof_is_immutable_comparable_and_replay_sufficient(self):
        accepted_claim = claim()
        recorded = TemporaryWorkerTransitionProof(
            claim=accepted_claim,
            resulting_entity_revision=1,
            source_event_id=EventId("event:worker-requested"),
            source_stream_position=8,
            audit_record_id=AuditRecordId("audit:worker-requested"),
            accepted_evidence_references=(IntegrityReference("evidence:accepted"),),
        )
        copied = TemporaryWorkerTransitionProof(**{
            field.name: getattr(recorded, field.name)
            for field in dataclasses.fields(TemporaryWorkerTransitionProof)
        })
        self.assertEqual(copied, recorded)
        self.assertEqual(copied.claim.enrollment.actor_id, ActorId("actor:worker"))
        self.assertEqual(copied.claim.enrollment.organization_id, OrganizationId("org:alpha"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            recorded.resulting_entity_revision = 2
        with self.assertRaises(ValueError):
            dataclasses.replace(recorded, resulting_entity_revision=2)

    def test_evidence_is_canonical_and_duplicate_free(self):
        canonical = (
            IntegrityReference("evidence:sponsor"),
            IntegrityReference("evidence:worker"),
        )
        self.assertEqual(enrollment().enrollment_evidence_references, canonical)
        with self.assertRaises(ValueError):
            enrollment(enrollment_evidence_references=tuple(reversed(canonical)))
        with self.assertRaises(ValueError):
            enrollment(enrollment_evidence_references=(canonical[0], canonical[0]))

    def test_denial_is_closed_typed_and_uses_stable_codes(self):
        denied = TemporaryWorkerEnrollmentDenied(
            CommandId("command:worker-request"),
            ReasonCode.LIFECYCLE_INVALID_TRANSITION,
            TemporaryWorkerGate.LIFECYCLE,
            "transition is not supported",
        )
        result: TemporaryWorkerEnrollmentResolution = denied
        self.assertIs(type(result), TemporaryWorkerEnrollmentDenied)
        with self.assertRaises(ValueError):
            TemporaryWorkerEnrollmentDenied(
                CommandId("command:worker-request"),
                ReasonCode.TOOL_SCOPE_VIOLATION,
                TemporaryWorkerGate.LIFECYCLE,
                "unrelated denial",
            )

    def test_contract_performs_no_lookup_time_or_runtime_effect(self):
        # Construction and replay consume only explicitly supplied immutable values.
        accepted_claim = claim()
        self.assertEqual(accepted_claim.evaluation_time, T)
        self.assertFalse(hasattr(accepted_claim, "credential"))
        self.assertFalse(hasattr(accepted_claim, "model_id"))
        self.assertFalse(hasattr(accepted_claim, "repository"))


if __name__ == "__main__":
    unittest.main()
