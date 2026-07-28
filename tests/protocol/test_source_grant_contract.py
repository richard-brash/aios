from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timedelta, timezone

from aios_protocol.authority import (
    ACCEPTED_DELEGATED_EXECUTION_UNIT,
    SourceAuthorityGrantClaim,
    SourceAuthorityGrantDenied,
    SourceAuthorityGrantGate,
    SourceAuthorityGrantLifecycle,
    SourceAuthorityGrantProof,
    SourceAuthorityGrantResolution,
    SourceGrantResourceCeiling,
    TaskResourceBound,
)
from aios_protocol.commands import ResourceDimension
from aios_protocol.identifiers import (
    ActorId, AuthorityGrantId, BudgetId, CapabilityId, CommandId, EventId,
    IntegrityReference, OrganizationId, ResourceId,
)
from aios_protocol.reason_codes import ReasonCode


T = datetime(2032, 1, 2, 3, 4, tzinfo=timezone.utc)


def ceiling(limit: int = 1) -> SourceGrantResourceCeiling:
    return SourceGrantResourceCeiling(
        ResourceId("resource:delegated-execution"),
        ResourceDimension.ACCEPTED_DELEGATED_CAPABILITY_EXECUTION,
        ACCEPTED_DELEGATED_EXECUTION_UNIT,
        limit,
    )


def task_bound(
    limit: int = 1, *,
    task_budget_id: BudgetId = BudgetId("budget:task-delegated-execution"),
    source_resource_id: ResourceId = ResourceId("resource:delegated-execution"),
) -> TaskResourceBound:
    return TaskResourceBound(
        task_budget_id,
        source_resource_id,
        ResourceDimension.ACCEPTED_DELEGATED_CAPABILITY_EXECUTION,
        ACCEPTED_DELEGATED_EXECUTION_UNIT,
        limit,
    )


def claim(**changes) -> SourceAuthorityGrantClaim:
    values = dict(
        command_id=CommandId("command:task-accept"),
        organization_id=OrganizationId("org:alpha"),
        authority_grant_id=AuthorityGrantId("grant:worker-source"),
        grantor_actor_id=ActorId("actor:sponsor"),
        authorized_subject_actor_id=ActorId("actor:worker"),
        purpose="maintain-role-catalog",
        requested_capabilities=(CapabilityId("role.create"),),
        requested_resource_ceiling=task_bound(),
        completion_condition="task:delegated-role:terminal",
        evaluation_time=T,
    )
    values.update(changes)
    return SourceAuthorityGrantClaim(**values)


def proof(**changes) -> SourceAuthorityGrantProof:
    values = dict(
        claim_command_id=CommandId("command:task-accept"),
        organization_id=OrganizationId("org:alpha"),
        authority_grant_id=AuthorityGrantId("grant:worker-source"),
        grantor_actor_id=ActorId("actor:sponsor"),
        authorized_subject_actor_id=ActorId("actor:worker"),
        parent_authority_grant_id=AuthorityGrantId("grant:sponsor-parent"),
        purpose="maintain-role-catalog",
        permitted_capabilities=(CapabilityId("role.activate"), CapabilityId("role.create")),
        prohibited_capabilities=(CapabilityId("role.delete"),),
        resource_ceiling=ceiling(2),
        completion_condition="task:delegated-role:terminal",
        lifecycle_state=SourceAuthorityGrantLifecycle.ACTIVE,
        evaluation_time=T,
        effective_at=T - timedelta(days=1),
        grant_entity_revision=3,
        source_event_id=EventId("event:grant-active"),
        source_stream_position=19,
        grant_evidence_reference=IntegrityReference("integrity:grant"),
        delegation_basis_reference=IntegrityReference("integrity:delegation"),
        delegation_permitted=True,
        evidence_references=(
            IntegrityReference("evidence:grant"),
            IntegrityReference("evidence:parent"),
        ),
    )
    values.update(changes)
    return SourceAuthorityGrantProof(**values)


class SourceAuthorityGrantContractTests(unittest.TestCase):
    def test_exact_attenuated_claim_is_valid(self):
        proof().validate_claim(claim())

    def test_capability_scope_is_canonical_finite_and_duplicate_free(self):
        with self.assertRaises(ValueError):
            claim(requested_capabilities=())
        with self.assertRaises(ValueError):
            claim(requested_capabilities=(CapabilityId("role.create"), CapabilityId("role.create")))
        with self.assertRaises(ValueError):
            claim(requested_capabilities=(CapabilityId("role.create"), CapabilityId("role.activate")))
        with self.assertRaises(ValueError):
            CapabilityId("role.*")

    def test_capability_containment_and_prohibition_fail_closed(self):
        with self.assertRaises(ValueError):
            proof().validate_claim(claim(
                requested_capabilities=(CapabilityId("role.retire"),),
            ))
        with self.assertRaises(ValueError):
            proof().validate_claim(claim(
                requested_capabilities=(CapabilityId("role.delete"),),
            ))

    def test_resource_ceiling_is_one_comparable_dimension(self):
        self.assertTrue(ceiling(2).contains(task_bound(1)))
        self.assertTrue(ceiling(2).contains(task_bound(2)))
        self.assertFalse(ceiling(1).contains(task_bound(2)))
        with self.assertRaises(ValueError):
            SourceGrantResourceCeiling(
                ResourceId("resource:x"), ResourceDimension.COMPUTE, "tokens", 1,
            )
        with self.assertRaises(TypeError):
            SourceGrantResourceCeiling(
                ResourceId("resource:x"),
                ResourceDimension.ACCEPTED_DELEGATED_CAPABILITY_EXECUTION,
                ACCEPTED_DELEGATED_EXECUTION_UNIT, 1.0,
            )

    def test_task_budget_identity_is_distinct_from_source_resource_identity(self):
        requested = task_bound(
            task_budget_id=BudgetId("budget:task-specific"),
            source_resource_id=ResourceId("resource:delegated-execution"),
        )
        self.assertIs(type(requested.task_budget_id), BudgetId)
        self.assertIs(type(requested.source_resource_id), ResourceId)
        self.assertNotEqual(str(requested.task_budget_id), str(requested.source_resource_id))
        self.assertTrue(ceiling().contains(requested))

    def test_resource_containment_requires_exact_dimension_unit_and_source_lineage(self):
        self.assertFalse(ceiling().contains(task_bound(
            source_resource_id=ResourceId("resource:unrelated"),
        )))
        with self.assertRaises(ValueError):
            TaskResourceBound(
                BudgetId("budget:task"), ResourceId("resource:delegated-execution"),
                ResourceDimension.COMPUTE, "tokens", 1,
            )
        with self.assertRaises(ValueError):
            TaskResourceBound(
                BudgetId("budget:task"), ResourceId("resource:delegated-execution"),
                ResourceDimension.ACCEPTED_DELEGATED_CAPABILITY_EXECUTION,
                "another-unit", 1,
            )
        with self.assertRaises(ValueError):
            TaskResourceBound(
                BudgetId("budget:task"), None,
                ResourceDimension.ACCEPTED_DELEGATED_CAPABILITY_EXECUTION,
                ACCEPTED_DELEGATED_EXECUTION_UNIT, 1,
            )

    def test_resource_expansion_fails_closed(self):
        with self.assertRaises(ValueError):
            proof(resource_ceiling=ceiling(1)).validate_claim(
                claim(requested_resource_ceiling=task_bound(2)),
            )

    def test_organization_grantor_subject_and_grant_bind_exactly(self):
        mismatches = (
            {"organization_id": OrganizationId("org:beta")},
            {"authority_grant_id": AuthorityGrantId("grant:other")},
            {"grantor_actor_id": ActorId("actor:other-sponsor")},
            {"authorized_subject_actor_id": ActorId("actor:other-worker")},
        )
        for changes in mismatches:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                proof().validate_claim(claim(**changes))

    def test_purpose_uses_exact_normalized_equality_not_prose_inference(self):
        with self.assertRaises(ValueError):
            proof().validate_claim(claim(purpose="maintain one role"))
        with self.assertRaises(Exception):
            claim(purpose=" maintain-role-catalog")

    def test_completion_condition_and_command_are_bound(self):
        with self.assertRaises(ValueError):
            proof().validate_claim(claim(completion_condition="another-task:terminal"))
        with self.assertRaises(ValueError):
            proof().validate_claim(claim(command_id=CommandId("command:other")))

    def test_only_active_effective_grant_can_form_proof(self):
        for state in (
            SourceAuthorityGrantLifecycle.SUSPENDED,
            SourceAuthorityGrantLifecycle.EXPIRED,
            SourceAuthorityGrantLifecycle.REVOKED,
        ):
            with self.subTest(state=state), self.assertRaises(ValueError):
                proof(lifecycle_state=state)
        with self.assertRaises(ValueError):
            proof(effective_at=T + timedelta(seconds=1))
        with self.assertRaises(ValueError):
            proof(delegation_permitted=False)

    def test_authoritative_event_and_evidence_lineage_is_required(self):
        with self.assertRaises(ValueError):
            proof(source_stream_position=0)
        with self.assertRaises(ValueError):
            proof(grant_entity_revision=0)
        with self.assertRaises(ValueError):
            proof(evidence_references=())
        with self.assertRaises(ValueError):
            proof(evidence_references=(IntegrityReference("evidence:x"),) * 2)

    def test_evidence_references_require_canonical_lexical_order(self):
        canonical = (
            IntegrityReference("evidence:grant"),
            IntegrityReference("evidence:parent"),
        )
        self.assertEqual(proof(evidence_references=canonical).evidence_references, canonical)
        with self.assertRaises(ValueError):
            proof(evidence_references=tuple(reversed(canonical)))
        rebuilt = tuple(sorted(set(reversed(canonical)), key=str))
        self.assertEqual(proof(evidence_references=rebuilt), proof(evidence_references=canonical))

    def test_proof_and_claim_are_immutable(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            proof().purpose = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            claim().purpose = "changed"

    def test_denial_is_closed_typed_and_safe(self):
        denied = SourceAuthorityGrantDenied(
            CommandId("command:task-accept"), ReasonCode.AUTH_REVOKED,
            SourceAuthorityGrantGate.LIFECYCLE, "source Grant is not usable",
        )
        result: SourceAuthorityGrantResolution = denied
        self.assertIs(type(result), SourceAuthorityGrantDenied)
        with self.assertRaises(ValueError):
            SourceAuthorityGrantDenied(
                CommandId("command:task-accept"), ReasonCode.POLICY_DENIED,
                SourceAuthorityGrantGate.LIFECYCLE, "not a source Grant reason",
            )

    def test_historical_proof_is_self_contained_and_revalidates_without_lookup(self):
        recorded = proof()
        copied = SourceAuthorityGrantProof(**{
            field.name: getattr(recorded, field.name)
            for field in dataclasses.fields(SourceAuthorityGrantProof)
        })
        copied.validate_claim(claim())
        self.assertEqual(copied, recorded)
        self.assertEqual(copied.source_event_id, EventId("event:grant-active"))
        self.assertEqual(copied.source_stream_position, 19)


if __name__ == "__main__":
    unittest.main()
