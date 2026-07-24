"""Focused architectural-review tests for semantic and atomic idempotency."""
from __future__ import annotations

import dataclasses
import unittest

from aios_kernel.gates import GATE_ORDER, GateName
from aios_kernel.idempotency import IdempotencyScope, semantic_command_fingerprint, semantic_command_identity
from aios_kernel.reference import InMemoryStore, deny
from aios_kernel.reference.in_memory_store import StoredIdempotency
from aios_kernel.transaction import TransactionStatus
from aios_protocol.commands import ResourceDimension, ResourceEstimate
from aios_protocol.dispositions import PreviouslyAdmitted
from aios_protocol.identifiers import (
    ActorId, ApprovalId, AuthorityGrantId, DecisionId, GoalId,
    MessageId, OrganizationId, ResourceId, StreamId,
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
    @staticmethod
    def _allocation_counts(ids):
        return tuple(ids.calls.count(kind) for kind in ("disposition","audit","event"))

    @staticmethod
    def _store_state(store, organization_id=OrganizationId("org-1")):
        return (
            tuple(store.stream(organization_id)),dict(store.audits),tuple(store.task_projection(organization_id)),
            tuple(store.resource_transitions),tuple(store.approval_use_transitions),dict(store.idempotency),
        )

    @staticmethod
    def _race_store(stored):
        class InsertAtAppendStore(InMemoryStore):
            def __init__(self):
                super().__init__(); self.pending=stored; self.inserted=False
            def inspect_idempotency(self, scope, fingerprint):
                from aios_kernel.idempotency import IdempotencyInspection, IdempotencyState
                return IdempotencyInspection(IdempotencyState.NEW)
            def append_new(self, **kwargs):
                if not self.inserted:
                    self.idempotency[self._scope_key(kwargs["scope"])]=self.pending
                    self.inserted=True
                return super().append_new(**kwargs)
        return InsertAtAppendStore()

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

    def test_preflight_duplicate_does_not_advance_any_allocator_class(self):
        app,store,ids,cmd=engine(); app.admit(cmd); before=self._allocation_counts(ids)
        state=self._store_state(store); app.admit(cmd)
        self.assertEqual(self._allocation_counts(ids),before)
        self.assertEqual(self._store_state(store),state)

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

    def test_exact_duplicate_inserted_after_preflight_allocates_nothing(self):
        donor,donor_store,_,cmd=engine(); donor.admit(cmd)
        stored=next(iter(donor_store.idempotency.values())); store=self._race_store(stored)
        app,_,ids,_=engine(store=store); before=self._store_state(store)
        result=app.admit(cmd)
        self.assertEqual(result.status,TransactionStatus.PREVIOUSLY_ADMITTED)
        self.assertEqual(self._allocation_counts(ids),(0,0,0))
        self.assertEqual(store.builder_calls,0)
        self.assertEqual(self._store_state(store)[:-1],before[:-1])

    def test_conflict_inserted_after_preflight_allocates_nothing(self):
        donor,donor_store,_,original=engine(); donor.admit(original)
        stored=next(iter(donor_store.idempotency.values())); store=self._race_store(stored)
        changed=dataclasses.replace(original,title="Race loser")
        app,_,ids,_=engine(cmd=changed,store=store); result=app.admit(changed)
        self.assertEqual(result.status,TransactionStatus.IDEMPOTENCY_CONFLICT)
        self.assertEqual(self._allocation_counts(ids),(0,0,0)); self.assertEqual(store.builder_calls,0)
        self.assertEqual(next(iter(store.idempotency.values())),stored)
        self.assertFalse(store.streams); self.assertFalse(store.audits); self.assertFalse(store.tasks)
        self.assertFalse(store.resource_transitions); self.assertFalse(store.approval_use_transitions)

    def test_uncertain_registration_inserted_after_preflight_allocates_nothing(self):
        donor,donor_store,_,cmd=engine(); donor.admit(cmd)
        known=next(iter(donor_store.idempotency.values()))
        uncertain=StoredIdempotency(known.fingerprint,known.disposition,True,False,True)
        store=self._race_store(uncertain); app,_,ids,_=engine(store=store)
        result=app.admit(cmd)
        self.assertEqual(result.status,TransactionStatus.OUTCOME_UNCERTAIN)
        self.assertEqual(self._allocation_counts(ids),(0,0,0)); self.assertEqual(store.builder_calls,0)
        self.assertEqual(next(iter(store.idempotency.values())),uncertain)
        self.assertFalse(store.streams); self.assertFalse(store.audits); self.assertFalse(store.tasks)

    def test_concurrency_conflict_precedes_builder_and_allocation(self):
        from aios_kernel.reference import Fault
        app,store,ids,cmd=engine(fault=Fault.CONCURRENCY,reservation="r",approval="a")
        result=app.admit(cmd)
        self.assertEqual(result.status,TransactionStatus.CONCURRENCY_CONFLICT)
        self.assertEqual(self._allocation_counts(ids),(0,0,0)); self.assertEqual(store.builder_calls,0)
        self.assertFalse(store.streams); self.assertFalse(store.audits); self.assertFalse(store.tasks)
        self.assertFalse(store.resource_transitions); self.assertFalse(store.approval_use_transitions); self.assertFalse(store.idempotency)

    def test_new_transaction_builds_once_and_uses_allocated_ids(self):
        app,store,ids,cmd=engine(); result=app.admit(cmd)
        self.assertEqual(store.builder_calls,1); self.assertEqual(self._allocation_counts(ids),(1,1,5))
        events=store.stream(OrganizationId("org-1")); audit=next(iter(store.audits.values()))
        self.assertEqual(result.disposition.envelope.message_id,MessageId("disp-0"))
        self.assertEqual(audit.audit_record_id,events[0].audit_record_id)
        self.assertEqual(tuple(event.event_id for event in events),tuple(result.disposition.event_ids))

    def test_builder_failure_leaves_store_unchanged(self):
        store=InMemoryStore(); scope=IdempotencyScope(OrganizationId("org-1"),ActorId("actor-1"),"CreateTask","idem-1")
        calls=[]
        def fail_builder(): calls.append("called"); raise RuntimeError("safe synthetic failure")
        result=store.append_new(organization_id=OrganizationId("org-1"),stream_id=StreamId("organization:org-1"),
            scope=scope,fingerprint="fingerprint",expected_prior_position=0,build_transaction=fail_builder)
        self.assertEqual(result.status,TransactionStatus.APPEND_FAILURE); self.assertEqual(calls,["called"])
        self.assertEqual(store.builder_calls,1); self.assertFalse(store.streams); self.assertFalse(store.audits)
        self.assertFalse(store.tasks); self.assertFalse(store.idempotency)

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
