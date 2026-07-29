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
    IntegrityReference, OrganizationId, ResourceId, RoleAssignmentId, RoleId,
)
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.role_assignment import (
    ActiveRoleEvidence,
    RoleAssignmentAuthorityEvidence,
    RoleAssignmentDenied,
    RoleAssignmentExpiryEvidence,
    RoleAssignmentGate,
    RoleAssignmentLifecycle,
    RoleAssignmentPriorTransitionEvidence,
    RoleAssignmentProfile,
    RoleAssignmentQualificationEvidence,
    RoleAssignmentResolution,
    RoleAssignmentTransition,
    RoleAssignmentTransitionClaim,
    RoleAssignmentTransitionProof,
    RoleAssignmentEvaluator,
    RoleLifecycleState,
)
from aios_protocol.temporary_worker import (
    ActorEnrollmentEvidence, ActorIdentityState, ActorKind,
    FirstTemporaryWorkerBounds, TemporaryWorkerCompletionCondition,
    TemporaryWorkerEnrollment, TemporaryWorkerLifecycle,
    TemporaryWorkerTransition, TemporaryWorkerTransitionClaim,
    TemporaryWorkerTransitionProof,
)
from aios_protocol.validation import StructuralValidationError


T = datetime(2033, 3, 4, 5, 6, tzinfo=timezone.utc)


def actor(
    actor_id: str, kind: ActorKind, *,
    organization_id: OrganizationId = OrganizationId("org:alpha"),
    state: ActorIdentityState = ActorIdentityState.ACTIVE,
) -> ActorEnrollmentEvidence:
    return ActorEnrollmentEvidence(
        organization_id, ActorId(actor_id), kind, state, 2,
        EventId(f"event:{actor_id.split(':')[1]}-identity"), 4,
        IntegrityReference(f"integrity:{actor_id}"),
    )


def source_grant(command_id: CommandId) -> SourceAuthorityGrantProof:
    return SourceAuthorityGrantProof(
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
            ACCEPTED_DELEGATED_EXECUTION_UNIT, 1,
        ),
        completion_condition="task_terminal",
        lifecycle_state=SourceAuthorityGrantLifecycle.ACTIVE,
        evaluation_time=T,
        effective_at=T - timedelta(days=1),
        grant_entity_revision=1,
        source_event_id=EventId("event:worker-grant"),
        source_stream_position=6,
        grant_evidence_reference=IntegrityReference("integrity:worker-grant"),
        delegation_basis_reference=IntegrityReference("integrity:delegation"),
        delegation_permitted=True,
        evidence_references=(IntegrityReference("evidence:worker-grant"),),
    )


def active_enrollment() -> TemporaryWorkerTransitionProof:
    command_id = CommandId("command:worker-activate")
    enrollment = TemporaryWorkerEnrollment(
        worker_actor=actor("actor:worker", ActorKind.TEMPORARY_WORKER),
        sponsor_actor=actor("actor:sponsor", ActorKind.HUMAN),
        purpose="maintain-role-catalog",
        source_authority_grant_id=AuthorityGrantId("grant:worker-source"),
        source_grant_evidence_reference=IntegrityReference("integrity:worker-grant"),
        bounds=FirstTemporaryWorkerBounds(
            1, 1, 1, TemporaryWorkerCompletionCondition.TASK_TERMINAL, False, False,
        ),
        enrollment_evidence_references=(IntegrityReference("evidence:enrollment"),),
    )
    claim = TemporaryWorkerTransitionClaim(
        command_id=command_id,
        enrollment=enrollment,
        transition=TemporaryWorkerTransition.ACTIVATE,
        prior_state=TemporaryWorkerLifecycle.REQUESTED,
        resulting_state=TemporaryWorkerLifecycle.ACTIVE,
        expected_entity_revision=1,
        prior_transition_event_id=EventId("event:worker-requested"),
        prior_transition_integrity_reference=IntegrityReference("integrity:worker-requested"),
        evaluation_time=T,
        source_grant_proof=source_grant(command_id),
        task_assignment_evidence=None,
        task_terminal_evidence=None,
        transition_evidence_references=(IntegrityReference("evidence:worker-active"),),
    )
    return TemporaryWorkerTransitionProof(
        claim, 2, EventId("event:worker-active"), 8,
        AuditRecordId("audit:worker-active"),
        (IntegrityReference("evidence:worker-active-accepted"),),
    )


def profile(**changes) -> RoleAssignmentProfile:
    values = dict(
        role_assignment_id=RoleAssignmentId("role-assignment:first-worker"),
        organization_id=OrganizationId("org:alpha"),
        worker_actor_id=ActorId("actor:worker"),
        role_id=RoleId("role:operator"),
        assigned_by_actor_id=ActorId("actor:sponsor"),
        qualifying_role_entity_revision=2,
        effective_at=T - timedelta(days=1),
        duty_scope="maintain the bounded role catalog",
        review_or_completion_condition="task terminal or assignment review",
        review_or_completion_condition_reference=IntegrityReference("condition:assignment"),
        profile_evidence_references=(IntegrityReference("evidence:assignment-profile"),),
    )
    values.update(changes)
    return RoleAssignmentProfile(**values)


def authority(command_id: CommandId, **changes) -> RoleAssignmentAuthorityEvidence:
    values = dict(
        claim_command_id=command_id,
        organization_id=OrganizationId("org:alpha"),
        assigner_actor_id=ActorId("actor:sponsor"),
        authority_grant_id=AuthorityGrantId("grant:sponsor-role-assignment"),
        subject_actor_id=ActorId("actor:worker"),
        role_id=RoleId("role:operator"),
        assignment_permitted=True,
        lifecycle_state=SourceAuthorityGrantLifecycle.ACTIVE,
        evaluation_time=T,
        authority_entity_revision=3,
        source_event_id=EventId("event:assigner-authority"),
        source_stream_position=10,
        authority_evidence_reference=IntegrityReference("integrity:assigner-authority"),
        evidence_references=(IntegrityReference("evidence:assigner-authority"),),
    )
    values.update(changes)
    return RoleAssignmentAuthorityEvidence(**values)


def qualification(
    command_id: CommandId, *, role: ActiveRoleEvidence | None = None,
    assigner: ActorEnrollmentEvidence | None = None,
    assigner_authority: RoleAssignmentAuthorityEvidence | None = None,
) -> RoleAssignmentQualificationEvidence:
    return RoleAssignmentQualificationEvidence(
        claim_command_id=command_id,
        evaluation_time=T,
        observed_organization_stream_position=10,
        current_qualification_reference=IntegrityReference("integrity:current-qualification"),
        enrollment_proof=active_enrollment(),
        role_evidence=role or ActiveRoleEvidence(
            OrganizationId("org:alpha"), RoleId("role:operator"),
            RoleLifecycleState.ACTIVE, 2, EventId("event:role-active"), 9,
            IntegrityReference("integrity:role-active"),
        ),
        assigner_actor=assigner or actor("actor:sponsor", ActorKind.HUMAN),
        assigner_authority=assigner_authority or authority(command_id),
        evidence_references=(IntegrityReference("evidence:qualification"),),
    )


def expiry(**changes) -> RoleAssignmentExpiryEvidence:
    values = dict(
        organization_id=OrganizationId("org:alpha"),
        role_assignment_id=RoleAssignmentId("role-assignment:first-worker"),
        condition_reference=IntegrityReference("condition:assignment"),
        condition_satisfied_at=T,
        source_event_id=EventId("event:assignment-condition"),
        source_stream_position=24,
        integrity_reference=IntegrityReference("integrity:assignment-condition"),
    )
    values.update(changes)
    return RoleAssignmentExpiryEvidence(**values)


def prior_evidence(
    state: RoleAssignmentLifecycle, revision: int, **changes,
) -> RoleAssignmentPriorTransitionEvidence:
    values = dict(
        organization_id=OrganizationId("org:alpha"),
        role_assignment_id=RoleAssignmentId("role-assignment:first-worker"),
        lifecycle_state=state,
        entity_revision=revision,
        source_event_id=EventId("event:assignment-prior"),
        source_stream_position=20,
        integrity_reference=IntegrityReference("integrity:assignment-prior"),
    )
    values.update(changes)
    return RoleAssignmentPriorTransitionEvidence(**values)


def claim(**changes) -> RoleAssignmentTransitionClaim:
    command_id = changes.pop("command_id", CommandId("command:assignment-propose"))
    values = dict(
        command_id=command_id,
        profile=profile(),
        transition=RoleAssignmentTransition.PROPOSE,
        prior_state=None,
        resulting_state=RoleAssignmentLifecycle.PROPOSED,
        expected_entity_revision=0,
        prior_transition_evidence=None,
        evaluation_time=T,
        qualification_evidence=qualification(command_id),
        expiry_evidence=None,
        transition_evidence_references=(IntegrityReference("evidence:transition"),),
    )
    values.update(changes)
    return RoleAssignmentTransitionClaim(**values)


class RoleAssignmentContractTests(unittest.TestCase):
    def test_complete_supported_lifecycle_is_closed(self):
        cases = (
            (RoleAssignmentTransition.PROPOSE, None, RoleAssignmentLifecycle.PROPOSED, 0, True, False),
            (RoleAssignmentTransition.ACTIVATE, RoleAssignmentLifecycle.PROPOSED, RoleAssignmentLifecycle.ACTIVE, 1, True, False),
            (RoleAssignmentTransition.SUSPEND, RoleAssignmentLifecycle.ACTIVE, RoleAssignmentLifecycle.SUSPENDED, 2, False, False),
            (RoleAssignmentTransition.RESTORE, RoleAssignmentLifecycle.SUSPENDED, RoleAssignmentLifecycle.ACTIVE, 3, True, False),
            (RoleAssignmentTransition.EXPIRE, RoleAssignmentLifecycle.ACTIVE, RoleAssignmentLifecycle.EXPIRED, 4, False, True),
            (RoleAssignmentTransition.REVOKE, RoleAssignmentLifecycle.SUSPENDED, RoleAssignmentLifecycle.REVOKED, 4, False, False),
            (RoleAssignmentTransition.ARCHIVE, RoleAssignmentLifecycle.REVOKED, RoleAssignmentLifecycle.ARCHIVED, 5, False, False),
        )
        for transition, prior_state, result, revision, needs_qualification, needs_expiry in cases:
            command_id = CommandId(f"command:{transition.value}")
            with self.subTest(transition=transition):
                made = claim(
                    command_id=command_id,
                    transition=transition,
                    prior_state=prior_state,
                    resulting_state=result,
                    expected_entity_revision=revision,
                    prior_transition_evidence=(
                        None if prior_state is None
                        else prior_evidence(prior_state, revision)
                    ),
                    qualification_evidence=(
                        qualification(command_id) if needs_qualification else None
                    ),
                    expiry_evidence=expiry() if needs_expiry else None,
                )
                self.assertIs(made.resulting_state, result)

    def test_every_accepted_transition_advances_revision_once(self):
        accepted = RoleAssignmentTransitionProof(
            claim(), 1, EventId("event:assignment-proposed"), 13,
            AuditRecordId("audit:assignment-proposed"),
            (IntegrityReference("evidence:assignment-accepted"),),
        )
        self.assertEqual(accepted.resulting_entity_revision, 1)
        with self.assertRaises(ValueError):
            dataclasses.replace(accepted, resulting_entity_revision=2)
        with self.assertRaises(ValueError):
            dataclasses.replace(accepted, source_stream_position=10)

    def test_qualification_binds_one_organization_worker_role_and_assigner(self):
        command_id = CommandId("command:assignment-propose")
        wrongs = (
            lambda: qualification(command_id, role=ActiveRoleEvidence(
                OrganizationId("org:other"), RoleId("role:operator"),
                RoleLifecycleState.ACTIVE, 2, EventId("event:role-active"), 9,
                IntegrityReference("integrity:role-active"),
            )),
            lambda: qualification(command_id, assigner=actor("actor:other", ActorKind.HUMAN)),
            lambda: qualification(command_id, assigner_authority=authority(
                command_id, subject_actor_id=ActorId("actor:other"),
            )),
            lambda: qualification(command_id, assigner_authority=authority(
                command_id, role_id=RoleId("role:other"),
            )),
        )
        for make_evidence in wrongs:
            with self.subTest(make_evidence=make_evidence), self.assertRaises(ValueError):
                claim(qualification_evidence=make_evidence())
        for changed_profile in (
            profile(organization_id=OrganizationId("org:other")),
            profile(worker_actor_id=ActorId("actor:other")),
            profile(role_id=RoleId("role:other")),
            profile(assigned_by_actor_id=ActorId("actor:other")),
        ):
            with self.subTest(changed_profile=changed_profile), self.assertRaises(ValueError):
                claim(profile=changed_profile)

    def test_active_enrollment_and_active_exact_role_revision_are_required(self):
        enrollment = active_enrollment()
        inactive_claim = dataclasses.replace(
            enrollment.claim,
            transition=TemporaryWorkerTransition.SUSPEND,
            prior_state=TemporaryWorkerLifecycle.ACTIVE,
            resulting_state=TemporaryWorkerLifecycle.SUSPENDED,
            expected_entity_revision=2,
            prior_transition_event_id=EventId("event:worker-active"),
            prior_transition_integrity_reference=IntegrityReference("integrity:worker-active"),
            source_grant_proof=None,
        )
        inactive = dataclasses.replace(
            enrollment, claim=inactive_claim, resulting_entity_revision=3,
            source_event_id=EventId("event:worker-suspended"), source_stream_position=11,
        )
        command_id = CommandId("command:assignment-propose")
        with self.assertRaises(ValueError):
            RoleAssignmentQualificationEvidence(
                command_id, T, 11,
                IntegrityReference("integrity:current-qualification"),
                inactive, qualification(command_id).role_evidence,
                qualification(command_id).assigner_actor, authority(command_id),
                (IntegrityReference("evidence:qualification"),),
            )
        with self.assertRaises(ValueError):
            claim(qualification_evidence=qualification(
                command_id,
                role=ActiveRoleEvidence(
                    OrganizationId("org:alpha"), RoleId("role:operator"),
                    RoleLifecycleState.DRAFT, 2, EventId("event:role-draft"), 9,
                    IntegrityReference("integrity:role-draft"),
                ),
            ))
        with self.assertRaises(ValueError):
            claim(profile=profile(qualifying_role_entity_revision=3))

    def test_assigner_eligibility_authority_command_and_time_are_exact(self):
        command_id = CommandId("command:assignment-propose")
        with self.assertRaises(ValueError):
            qualification(command_id, assigner=actor("actor:sponsor", ActorKind.SERVICE))
        with self.assertRaises(ValueError):
            qualification(command_id, assigner_authority=authority(
                command_id, assignment_permitted=False,
            ))
        with self.assertRaises(ValueError):
            qualification(command_id, assigner_authority=authority(
                command_id, lifecycle_state=SourceAuthorityGrantLifecycle.REVOKED,
            ))
        with self.assertRaises(ValueError):
            claim(qualification_evidence=qualification(
                command_id,
                assigner_authority=authority(CommandId("command:other")),
            ))
        with self.assertRaises(ValueError):
            claim(qualification_evidence=qualification(
                command_id,
                assigner_authority=authority(
                    command_id, evaluation_time=T + timedelta(seconds=1),
                ),
            ))
        with self.assertRaises(ValueError):
            dataclasses.replace(
                qualification(command_id), observed_organization_stream_position=9,
            )

    def test_scope_and_review_condition_are_nonempty_and_immutable(self):
        with self.assertRaises(Exception):
            profile(duty_scope="")
        with self.assertRaises(Exception):
            profile(review_or_completion_condition="")
        made = profile()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            made.duty_scope = "broader"
        command_id = CommandId("command:activate")
        with self.assertRaises(ValueError):
            claim(
                command_id=command_id,
                profile=profile(effective_at=T + timedelta(seconds=1)),
                transition=RoleAssignmentTransition.ACTIVATE,
                prior_state=RoleAssignmentLifecycle.PROPOSED,
                resulting_state=RoleAssignmentLifecycle.ACTIVE,
                expected_entity_revision=1,
                prior_transition_evidence=prior_evidence(
                    RoleAssignmentLifecycle.PROPOSED, 1,
                ),
                qualification_evidence=qualification(command_id),
            )

    def test_prior_transition_lineage_is_required_and_consistent(self):
        with self.assertRaises(StructuralValidationError):
            claim(
                transition=RoleAssignmentTransition.SUSPEND,
                prior_state=RoleAssignmentLifecycle.ACTIVE,
                resulting_state=RoleAssignmentLifecycle.SUSPENDED,
                expected_entity_revision=2,
                prior_transition_evidence=None,
                qualification_evidence=None,
            )
        for bad in (
            prior_evidence(
                RoleAssignmentLifecycle.ACTIVE, 2,
                organization_id=OrganizationId("org:other"),
            ),
            prior_evidence(
                RoleAssignmentLifecycle.ACTIVE, 2,
                role_assignment_id=RoleAssignmentId("role-assignment:other"),
            ),
            prior_evidence(RoleAssignmentLifecycle.SUSPENDED, 2),
            prior_evidence(RoleAssignmentLifecycle.ACTIVE, 3),
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                claim(
                    transition=RoleAssignmentTransition.SUSPEND,
                    prior_state=RoleAssignmentLifecycle.ACTIVE,
                    resulting_state=RoleAssignmentLifecycle.SUSPENDED,
                    expected_entity_revision=2,
                    prior_transition_evidence=bad,
                    qualification_evidence=None,
                )
        suspended = claim(
            transition=RoleAssignmentTransition.SUSPEND,
            prior_state=RoleAssignmentLifecycle.ACTIVE,
            resulting_state=RoleAssignmentLifecycle.SUSPENDED,
            expected_entity_revision=2,
            prior_transition_evidence=prior_evidence(RoleAssignmentLifecycle.ACTIVE, 2),
            qualification_evidence=None,
        )
        with self.assertRaises(ValueError):
            RoleAssignmentTransitionProof(
                suspended, 3, EventId("event:assignment-suspended"), 20,
                AuditRecordId("audit:assignment-suspended"),
                (IntegrityReference("evidence:suspended"),),
            )

    def test_invalid_and_unsupported_transitions_fail_closed(self):
        with self.assertRaises(ValueError):
            claim(
                transition=RoleAssignmentTransition.ACTIVATE,
                prior_state=RoleAssignmentLifecycle.SUSPENDED,
                resulting_state=RoleAssignmentLifecycle.ACTIVE,
                expected_entity_revision=2,
            )
        with self.assertRaises(ValueError):
            claim(expected_entity_revision=1)
        with self.assertRaises(ValueError):
            claim(
                transition=RoleAssignmentTransition.ARCHIVE,
                prior_state=RoleAssignmentLifecycle.ACTIVE,
                resulting_state=RoleAssignmentLifecycle.ARCHIVED,
                expected_entity_revision=2,
            )

    def test_expiry_is_explicit_ordered_and_has_no_ambient_time(self):
        expired = claim(
            transition=RoleAssignmentTransition.EXPIRE,
            prior_state=RoleAssignmentLifecycle.ACTIVE,
            resulting_state=RoleAssignmentLifecycle.EXPIRED,
            expected_entity_revision=2,
            prior_transition_evidence=prior_evidence(RoleAssignmentLifecycle.ACTIVE, 2),
            qualification_evidence=None,
            expiry_evidence=expiry(),
        )
        self.assertEqual(expired.evaluation_time, T)
        for bad in (
            expiry(organization_id=OrganizationId("org:other")),
            expiry(role_assignment_id=RoleAssignmentId("role-assignment:other")),
            expiry(condition_reference=IntegrityReference("condition:other")),
            expiry(condition_satisfied_at=T + timedelta(seconds=1)),
            expiry(source_stream_position=20),
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                dataclasses.replace(expired, expiry_evidence=bad)
        accepted = RoleAssignmentTransitionProof(
            expired, 3, EventId("event:assignment-expired"), 25,
            AuditRecordId("audit:assignment-expired"),
            (IntegrityReference("evidence:assignment-expired"),),
        )
        self.assertEqual(accepted.source_stream_position, 25)
        with self.assertRaises(ValueError):
            dataclasses.replace(accepted, source_stream_position=24)

    def test_termination_does_not_represent_task_or_authority_inference(self):
        fields = {field.name for field in dataclasses.fields(RoleAssignmentTransitionClaim)}
        self.assertNotIn("task_id", fields)
        self.assertNotIn("task_terminal_state", fields)
        self.assertNotIn("capability_authority", {
            field.name for field in dataclasses.fields(RoleAssignmentProfile)
        })

    def test_proof_is_immutable_comparable_and_replay_sufficient(self):
        recorded = RoleAssignmentTransitionProof(
            claim(), 1, EventId("event:assignment-proposed"), 13,
            AuditRecordId("audit:assignment-proposed"),
            (IntegrityReference("evidence:assignment-accepted"),),
        )
        copied = RoleAssignmentTransitionProof(**{
            field.name: getattr(recorded, field.name)
            for field in dataclasses.fields(RoleAssignmentTransitionProof)
        })
        self.assertEqual(copied, recorded)
        self.assertEqual(copied.claim.profile.worker_actor_id, ActorId("actor:worker"))
        self.assertEqual(copied.claim.profile.role_id, RoleId("role:operator"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            recorded.resulting_entity_revision = 2

    def test_evidence_collections_are_canonical_and_duplicate_free(self):
        canonical = (
            IntegrityReference("evidence:assignment-a"),
            IntegrityReference("evidence:assignment-b"),
        )
        made = profile(profile_evidence_references=canonical)
        self.assertEqual(made.profile_evidence_references, canonical)
        with self.assertRaises(ValueError):
            profile(profile_evidence_references=tuple(reversed(canonical)))
        with self.assertRaises(ValueError):
            profile(profile_evidence_references=(canonical[0], canonical[0]))

    def test_denial_is_closed_and_evaluator_boundary_is_effect_free(self):
        denied = RoleAssignmentDenied(
            CommandId("command:assignment"), ReasonCode.LIFECYCLE_INVALID_TRANSITION,
            RoleAssignmentGate.LIFECYCLE, "transition is invalid",
        )
        resolution: RoleAssignmentResolution = denied
        self.assertIs(type(resolution), RoleAssignmentDenied)
        with self.assertRaises(ValueError):
            RoleAssignmentDenied(
                CommandId("command:assignment"), ReasonCode.TOOL_SCOPE_VIOLATION,
                RoleAssignmentGate.LIFECYCLE, "unrelated denial",
            )
        self.assertFalse(hasattr(claim(), "repository"))
        self.assertFalse(hasattr(claim(), "clock"))
        self.assertFalse(hasattr(claim(), "handler"))
        self.assertEqual(
            set(RoleAssignmentEvaluator.__dict__) & {"read", "append", "authorize"},
            set(),
        )


if __name__ == "__main__":
    unittest.main()
