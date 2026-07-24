"""Focused architectural-review tests for semantic and atomic idempotency."""
from __future__ import annotations

import dataclasses
import unittest

from aios_kernel.gates import GATE_ORDER, GateName
from aios_kernel.idempotency import semantic_command_fingerprint, semantic_command_identity
from aios_kernel.reference import InMemoryStore, deny
from aios_kernel.transaction import TransactionStatus
from aios_protocol.commands import ResourceDimension, ResourceEstimate
from aios_protocol.dispositions import PreviouslyAdmitted
from aios_protocol.identifiers import (
    ActorId, ApprovalId, AuthorityGrantId, DecisionId, GoalId,
    MessageId, OrganizationId, ResourceId,
)
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import RecordTypeVersion

from test_create_task_admission import command, engine, snapshot


def replace_submission(cmd, **changes):
    return dataclasses.replace(cmd, submission=dataclasses.replace(cmd.submission, **changes))


class SemanticCommandIdentityTests(unittest.TestCase):
    def test_independently_constructed_equivalent_commands_match(self):
        self.assertEqual(semantic_command_identity(command()), semantic_command_identity(command()))
        self.assertEqual(semantic_command_fingerprint(command()), semantic_command_fingerprint(command()))

    def test_mapping_insertion_order_is_not_semantic(self):
        first=replace_submission(command(),lifecycle_preconditions=FrozenMap((("a",1),("b",2))))
        second=replace_submission(command(),lifecycle_preconditions=FrozenMap((("b",2),("a",1))))
        self.assertEqual(semantic_command_fingerprint(first),semantic_command_fingerprint(second))

    def test_material_create_task_fields_are_semantic(self):
        base=command(); variants=(
            dataclasses.replace(base,title="Changed"),
            dataclasses.replace(base,purpose="Changed"),
            dataclasses.replace(base,proposed_task_id="task-2"),
            replace_submission(base,work_root=dataclasses.replace(base.work_root,goal_id=GoalId("goal-2"))),
            replace_submission(base,decision_reference=DecisionId("decision-2")),
            replace_submission(base,authority_references=(AuthorityGrantId("grant-2"),)),
            replace_submission(base,approval_references=(ApprovalId("approval-2"),)),
            replace_submission(base,expected_resource_use=(ResourceEstimate(ResourceId("resource-2"),ResourceDimension.MONEY,1,"USD",1),)),
        )
        original=semantic_command_fingerprint(base)
        self.assertTrue(all(semantic_command_fingerprint(item)!=original for item in variants))

    def test_scope_and_operation_fields_are_semantic(self):
        base=command(); env=base.submission.envelope
        variants=(
            replace_submission(base,envelope=dataclasses.replace(env,organization_id=OrganizationId("org-2"))),
            replace_submission(base,envelope=dataclasses.replace(env,initiating_actor_id=ActorId("actor-2"))),
            replace_submission(base,operation_version=RecordTypeVersion("2.0")),
            replace_submission(base,idempotency_key="idem-2"),
            replace_submission(base,operation_type="CreateTaskAlternate"),
        )
        original=semantic_command_fingerprint(base)
        self.assertTrue(all(semantic_command_fingerprint(item)!=original for item in variants))

    def test_delivery_message_identity_is_explicitly_nonsemantic(self):
        base=command()
        redelivery=replace_submission(base,envelope=dataclasses.replace(base.submission.envelope,message_id=MessageId("message-2")))
        self.assertEqual(semantic_command_fingerprint(base),semantic_command_fingerprint(redelivery))


class AtomicIdempotencyTests(unittest.TestCase):
    def test_gate_order_is_complete_and_explicit(self):
        self.assertEqual(GATE_ORDER,(
            GateName.STRUCTURE,GateName.SUPPORTED_OPERATION,GateName.ORGANIZATION,
            GateName.IDENTITY,GateName.IDEMPOTENCY,GateName.AUTHORITY,GateName.POLICY,
            GateName.WORK_ROOT,GateName.DECISION,GateName.APPROVAL,GateName.TARGET,
            GateName.INCIDENT,GateName.LIFECYCLE,GateName.RESOURCE,GateName.FINAL_INVARIANT,
        ))

    def test_exact_duplicate_after_acceptance_has_no_second_mutation(self):
        app,store,ids,cmd=engine(reservation="r",approval="a")
        original=app.admit(cmd); state=(len(store.stream(cmd.submission.envelope.organization_id)),len(store.audits),len(store.dispositions),tuple(store.resource_transitions),tuple(store.approval_use_transitions),len(ids.calls))
        duplicate=app.admit(cmd)
        self.assertEqual(duplicate.status,TransactionStatus.PREVIOUSLY_ADMITTED)
        self.assertIsInstance(duplicate.disposition,PreviouslyAdmitted)
        self.assertEqual(state,(len(store.stream(cmd.submission.envelope.organization_id)),len(store.audits),len(store.dispositions),tuple(store.resource_transitions),tuple(store.approval_use_transitions),len(ids.calls)))
        self.assertEqual(duplicate.disposition.original_disposition_id,original.disposition.envelope.message_id)

    def test_exact_duplicate_after_rejection_returns_original(self):
        evaluator=deny(GateName.POLICY,ReasonCode.POLICY_DENIED)
        app,store,ids,cmd=engine(overrides={GateName.POLICY:evaluator})
        original=app.admit(cmd); calls=len(ids.calls); events=len(store.stream(OrganizationId("org-1")))
        duplicate=app.admit(cmd)
        self.assertEqual(duplicate.status,TransactionStatus.PREVIOUSLY_ADMITTED)
        self.assertEqual(duplicate.disposition.original_disposition_id,original.disposition.envelope.message_id)
        self.assertEqual((len(ids.calls),len(store.stream(OrganizationId("org-1")))),(calls,events))

    def test_competing_fingerprint_cannot_overwrite_registration(self):
        app,store,_,cmd=engine(); app.admit(cmd)
        key=next(iter(store.idempotency)); original=store.idempotency[key]
        changed=dataclasses.replace(cmd,title="Competing title")
        contender,_,_,_=engine(cmd=changed,snap=dataclasses.replace(snapshot(),stream_position=5),store=store)
        result=contender.admit(changed)
        self.assertEqual((result.status,result.reason_code),(TransactionStatus.IDEMPOTENCY_CONFLICT,ReasonCode.IDEMPOTENCY_CONFLICT))
        self.assertIs(store.idempotency[key],original)
        self.assertEqual((len(store.stream(OrganizationId("org-1"))),len(store.audits),len(store.tasks[OrganizationId("org-1")])),(5,1,1))

    def test_stale_preflight_cannot_bypass_atomic_check(self):
        class StalePreflightStore(InMemoryStore):
            def inspect_idempotency(self, scope, fingerprint):
                from aios_kernel.idempotency import IdempotencyInspection, IdempotencyState
                return IdempotencyInspection(IdempotencyState.NEW)
        store=StalePreflightStore(); first,_,_,cmd=engine(store=store); first.admit(cmd)
        changed=dataclasses.replace(cmd,title="Race loser")
        second,_,_,_=engine(cmd=changed,snap=dataclasses.replace(snapshot(),stream_position=5),store=store)
        self.assertEqual(second.admit(changed).status,TransactionStatus.IDEMPOTENCY_CONFLICT)
        self.assertEqual(len(store.stream(OrganizationId("org-1"))),5)

    def test_uncertain_before_metadata_distinguishes_state_domains(self):
        from aios_kernel.reference import Fault
        app,_,_,cmd=engine(fault=Fault.UNCERTAIN_BEFORE)
        result=app.admit(cmd)
        self.assertFalse(result.authoritative_mutation_may_have_occurred)
        self.assertTrue(result.internal_reconciliation_metadata_recorded)
        self.assertFalse(result.external_domain_mutation_may_have_occurred)

    def test_uncertain_registration_blocks_retry(self):
        from aios_kernel.reference import Fault
        app,store,_,cmd=engine(fault=Fault.UNCERTAIN_AFTER); app.admit(cmd)
        store.fault=Fault.NONE
        retry=app.admit(cmd)
        self.assertEqual(retry.status,TransactionStatus.OUTCOME_UNCERTAIN)
        self.assertTrue(retry.authoritative_mutation_may_have_occurred)
        self.assertEqual(len(store.stream(OrganizationId("org-1"))),5)


if __name__ == "__main__":
    unittest.main()
