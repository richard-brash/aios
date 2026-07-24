"""Behavioral architecture tests for ordinary draft Role creation."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
import pathlib
import subprocess
import sys
import unittest

from aios_kernel.bootstrap_runtime import genesis_stream_id, replay_genesis
from aios_kernel.create_role import (
    CREATE_ROLE_OPERATION, CREATE_ROLE_VERSION, CreateRoleCommand,
    CreateRoleGovernanceEvaluator, CreateRoleHandler, OrganizationRoleProjection,
    RoleCreationAttributes, RoleProjection, replay_organization_roles,
)
from aios_kernel.create_task import CreateTaskCommand, CreateTaskHandler, InitialTaskState
from aios_kernel.reference import (
    DeterministicIdentifiers, DeterministicRecordingBoundaryResolver, FixedClock,
    InMemoryRuntimeEventStore,
)
from aios_kernel.reference.runtime_store import StoredRuntimeIdempotency
from aios_kernel.runtime import (
    AppendRejected, KernelRuntime, ProcessingAllowed, ProcessingDenied, RuntimeAccepted,
    RuntimeCommand, RuntimeRejected,
)
from aios_protocol.admission import AdmissionEstablished
from aios_protocol.commands import CommandSubmission, EntityReference, GoalWorkRoot, RiskClass
from aios_protocol.envelope import CallerEnvelope
from aios_protocol.identifiers import (
    ActorId, AuthorityGrantId, CommandId, CorrelationId, DecisionId, GoalId,
    IntegrityReference, MessageId, OperationId, OrganizationId, RoleId,
)
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import PAYLOAD_V1, RECORD_V1, RecordTypeVersion

from test_bootstrap_runtime import bootstrap_request, runtime as bootstrap_runtime


NOW=datetime(2044,5,6,7,8,9,tzinfo=timezone.utc)


def founded(organization="org-bootstrap"):
    kernel,store,_,_=bootstrap_runtime()
    request=bootstrap_request(organization=organization)
    kernel.execute(request)
    return replay_genesis(store.read(genesis_stream_id(request.organization.organization_id)))


def attributes(role="role-ordinary",name="Operations Steward"):
    return RoleCreationAttributes(
        RoleId(role),name,("maintain declared operations",),("operations",),
        FrozenMap({"actions":("propose",)}),"governance review",
        ("cannot approve own activation",),
    )


def role_seed(state):
    founding=state.founding_role
    projection=RoleProjection(
        founding.role_id,state.organization.organization_id,founding.name,founding.duties,
        founding.eligible_capability_references,founding.eligible_authority_scope,
        founding.escalation_path,founding.separation_of_duties_constraints,"active",1,
        state.verified_human.actor_id,state.recording_command_id,None,None,True,
    )
    return OrganizationRoleProjection(
        state.organization.organization_id,True,founding.role_id,(projection,),0,
    )


def command(*,role=None,organization="org-bootstrap",actor="human-founder",
            command_id="command-create-role",idempotency="create-role/1",
            expected_position=0,version=CREATE_ROLE_VERSION):
    role=role or attributes()
    organization_id=OrganizationId(organization)
    envelope=CallerEnvelope(
        MessageId(f"message-{command_id}"),"CommandSubmission",organization_id,
        ActorId(actor),CorrelationId(f"correlation-{command_id}"),NOW,"internal",
        "establish draft organizational structure",CREATE_ROLE_OPERATION,PAYLOAD_V1,
        FrozenMap({"role":role}),
    )
    submission=CommandSubmission(
        envelope,CommandId(command_id),OperationId(f"operation-{command_id}"),
        CREATE_ROLE_OPERATION,version,(EntityReference("Role",str(role.role_id),0),),
        idempotency,None,False,IntegrityReference(f"proof:{organization}:{actor}"),
        (AuthorityGrantId(f"grant-{organization}"),),
        risk=RiskClass.REVERSIBLE,
        result_criteria=FrozenMap({"lifecycle_state":"draft"}),
    )
    return CreateRoleCommand(submission,expected_position,role)


def task_command(*,suffix="one",expected_position=0):
    organization_id=OrganizationId("org-bootstrap"); actor_id=ActorId("human-founder")
    envelope=CallerEnvelope(
        MessageId(f"message-task-{suffix}"),"CommandSubmission",organization_id,actor_id,
        CorrelationId(f"correlation-task-{suffix}"),NOW,"internal","create task",
        "CreateTask",PAYLOAD_V1,FrozenMap({"task_id":f"task-{suffix}"}),
    )
    submission=CommandSubmission(
        envelope,CommandId(f"command-task-{suffix}"),OperationId(f"operation-task-{suffix}"),
        "CreateTask",RECORD_V1,(EntityReference("Task",f"task-{suffix}",0),),
        f"create-task/{suffix}",GoalWorkRoot(GoalId("goal-bootstrap")),True,
        IntegrityReference("proof:org-bootstrap:human-founder"),
        (AuthorityGrantId("grant-org-bootstrap"),),decision_reference=DecisionId("decision-org-bootstrap"),
        risk=RiskClass.REVERSIBLE,result_criteria=FrozenMap({"state":"proposed"}),
    )
    return CreateTaskCommand(
        submission=submission,expected_stream_position=expected_position,
        proposed_task_id=f"task-{suffix}",title=f"Task {suffix}",purpose="mixed history",
        initial_state=InitialTaskState.PROPOSED,
    )


class AllowAuthority:
    def __init__(self): self.calls=0
    def evaluate(self,context):
        self.calls+=1
        return ProcessingAllowed(FrozenMap({"authority":"verified"}))


class IndeterminateAuthority:
    def __init__(self): self.calls=0
    def evaluate(self,context): self.calls+=1; return object()


class CountingRoleHandler(CreateRoleHandler):
    def __init__(self,state): super().__init__(state); self.validations=0; self.calls=0
    def validate(self,command): self.validations+=1; return super().validate(command)
    def handle(self,context): self.calls+=1; return super().handle(context)


def admission_for(command):
    submission=command.submission
    return AdmissionEstablished(
        submission.envelope.message_id,submission.command_id,
        submission.envelope.organization_id,submission.envelope.initiating_actor_id,
        IntegrityReference("genesis-create-role"),IntegrityReference("identity-create-role"),
        submission.invocation_proof_reference,(IntegrityReference("authentication-create-role"),),
        IntegrityReference("create-role-resolver"),RECORD_V1,
    )


def role_runtime(*,state=None,authority=None,store=None,handler=None,resolver=None):
    state=state or founded(); authority=authority or AllowAuthority()
    store=store or InMemoryRuntimeEventStore()
    handler=handler or CountingRoleHandler(role_seed(state))
    evaluator=CreateRoleGovernanceEvaluator(authority_evaluator=authority)
    if resolver is None:
        established=(admission_for(command()),) if state.genesis_completed else ()
        resolver=DeterministicRecordingBoundaryResolver(established)
    identifiers=DeterministicIdentifiers(
        [f"role-disposition-{i}" for i in range(20)],
        [f"role-audit-{i}" for i in range(20)],
        [f"role-event-{i}" for i in range(100)],
    )
    kernel=KernelRuntime(clock=FixedClock(NOW),identifiers=identifiers,
                         evaluator=evaluator,store=store,resolver=resolver,handlers=(handler,))
    return kernel,store,identifiers,authority,handler,state


def task_runtime(cmd,store,*,authority=None):
    authority=authority or AllowAuthority()
    resolver=DeterministicRecordingBoundaryResolver((admission_for(cmd),))
    identifiers=DeterministicIdentifiers(
        [f"{cmd.proposed_task_id}-disposition"],[f"{cmd.proposed_task_id}-audit"],
        [f"{cmd.proposed_task_id}-event-{i}" for i in range(10)],
    )
    kernel=KernelRuntime(
        clock=FixedClock(NOW),identifiers=identifiers,evaluator=authority,store=store,
        resolver=resolver,handlers=(CreateTaskHandler(),),
    )
    return kernel,identifiers,authority


class CreateRoleCapabilityTests(unittest.TestCase):
    def test_valid_command_appends_one_draft_role_event_to_organization_stream(self):
        kernel,store,_,authority,handler,state=role_runtime()
        result=kernel.execute(command())
        self.assertIsInstance(result,RuntimeAccepted)
        self.assertEqual(authority.calls,1); self.assertEqual(handler.calls,1)
        self.assertEqual(tuple(event.event_type for event in result.domain_events),("RoleCreated",))
        event=result.domain_events[0]
        self.assertEqual(str(event.envelope.stream_id),"organization:org-bootstrap")
        self.assertEqual((event.payload["role"],event.payload["lifecycle_state"],event.payload["entity_revision"]),
                         (attributes(),"draft",1))
        self.assertEqual(store.read(state.organization.organization_id),result.recorded_events)
        self.assertFalse(hasattr(store,"role_streams"))

    def test_replay_reconstructs_founding_and_ordinary_roles_without_effects(self):
        kernel,store,ids,authority,handler,state=role_runtime(); kernel.execute(command())
        dependencies=(tuple(ids.calls),authority.calls,handler.calls)
        first=replay_organization_roles(role_seed(state),store.read(state.organization.organization_id))
        second=replay_organization_roles(role_seed(state),store.read(state.organization.organization_id))
        self.assertEqual(first,second); self.assertEqual(dependencies,(tuple(ids.calls),authority.calls,handler.calls))
        self.assertEqual(first.founding_role_id,state.founding_role.role_id)
        self.assertEqual(first.role(RoleId("role-ordinary")).lifecycle_state,"draft")
        self.assertTrue(first.role(state.founding_role.role_id).is_founding_role)

    def test_replay_traverses_valid_mixed_supported_history(self):
        kernel,store,_,_,_,state=role_runtime(); kernel.execute(command())
        events=store.read(state.organization.organization_id)
        self.assertEqual(tuple(event.event_type for event in events),
                         ("CommandAccepted","RoleCreated","AuditLinked"))
        projection=replay_organization_roles(role_seed(state),events)
        self.assertEqual(projection.last_organization_stream_position,3)
        self.assertEqual(projection.role(RoleId("role-ordinary")).lifecycle_state,"draft")

    def test_replay_consumes_actual_create_task_create_role_create_task_history(self):
        state=founded(); seed=role_seed(state); store=InMemoryRuntimeEventStore()
        first=task_command(suffix="before",expected_position=0)
        task_runtime(first,store)[0].execute(first)
        role=command(expected_position=5)
        role_resolver=DeterministicRecordingBoundaryResolver((admission_for(role),))
        role_runtime(state=state,store=store,resolver=role_resolver)[0].execute(role)
        second=task_command(suffix="after",expected_position=8)
        task_runtime(second,store)[0].execute(second)
        history=store.read(state.organization.organization_id)
        self.assertEqual(tuple(event.event_type for event in history),(
            "CommandAccepted","TaskCreated","DecisionLinked","WorkRootLinked","AuditLinked",
            "CommandAccepted","RoleCreated","AuditLinked",
            "CommandAccepted","TaskCreated","DecisionLinked","WorkRootLinked","AuditLinked",
        ))
        projection=replay_organization_roles(seed,history)
        self.assertEqual(projection.last_organization_stream_position,13)
        self.assertEqual(projection.role(RoleId("role-ordinary")).lifecycle_state,"draft")

    def test_replay_validates_rejected_transaction_without_changing_roles(self):
        state=founded(); seed=role_seed(state); store=InMemoryRuntimeEventStore()
        rejected=task_command(suffix="denied",expected_position=0)
        denied=ProcessingDenied(ReasonCode.AUTH_MISSING,"authority","denied")
        class Deny:
            def evaluate(self,context): return denied
        task_runtime(rejected,store,authority=Deny())[0].execute(rejected)
        role=command(expected_position=2)
        resolver=DeterministicRecordingBoundaryResolver((admission_for(role),))
        role_runtime(state=state,store=store,resolver=resolver)[0].execute(role)
        projection=replay_organization_roles(seed,store.read(state.organization.organization_id))
        self.assertEqual(projection.role(RoleId("role-ordinary")).lifecycle_state,"draft")
        self.assertEqual(projection.last_organization_stream_position,5)

    def test_multiple_distinct_role_transactions_replay_in_organization_order(self):
        kernel,store,_,_,_,state=role_runtime()
        first=command(); second=command(
            role=attributes("role-second","Operations Steward"),
            command_id="command-create-role-second",idempotency="create-role/2",
            expected_position=3,
        )
        kernel.execute(first); kernel.execute(second)
        projection=replay_organization_roles(role_seed(state),store.read(state.organization.organization_id))
        self.assertEqual(
            tuple(role.role_id for role in projection.roles if not role.is_founding_role),
            (RoleId("role-ordinary"),RoleId("role-second")),
        )

    def test_replay_rejects_incomplete_rejection_and_admission_evidence_mismatch(self):
        state=founded(); store=InMemoryRuntimeEventStore()
        rejected=task_command(suffix="denied",expected_position=0)
        class Deny:
            def evaluate(self,context):
                return ProcessingDenied(ReasonCode.AUTH_MISSING,"authority","denied")
        task_runtime(rejected,store,authority=Deny())[0].execute(rejected)
        disposition,audit=store.read(state.organization.organization_id)
        with self.assertRaisesRegex(ValueError,"incomplete rejected sequence"):
            replay_organization_roles(role_seed(state),(disposition,))
        evidence=dataclasses.replace(
            audit.payload["admission_evidence"],initiating_actor_id=ActorId("actor-other"))
        bad_audit=dataclasses.replace(
            audit,payload=FrozenMap({**dict(audit.payload),"admission_evidence":evidence}))
        with self.assertRaisesRegex(ValueError,"admission evidence"):
            replay_organization_roles(role_seed(state),(disposition,bad_audit))

    def test_replay_rejects_unknown_event_before_returning_projection(self):
        kernel,store,_,_,_,state=role_runtime(); kernel.execute(command())
        events=list(store.read(state.organization.organization_id)); seed=role_seed(state)
        events[1]=dataclasses.replace(
            events[1],event_type="UnknownOrganizationFact",
            envelope=dataclasses.replace(events[1].envelope,message_type="UnknownOrganizationFact"),
        )
        with self.assertRaisesRegex(ValueError,"type is unsupported"):
            replay_organization_roles(seed,tuple(events))
        self.assertEqual((seed.last_organization_stream_position,seed.role(RoleId("role-ordinary"))),
                         (0,None))

    def test_replay_rejects_unsupported_nonrole_event_version_before_advancement(self):
        kernel,store,_,_,_,state=role_runtime(); kernel.execute(command())
        events=list(store.read(state.organization.organization_id)); seed=role_seed(state)
        events[0]=dataclasses.replace(events[0],event_version=RecordTypeVersion("2.0"))
        with self.assertRaisesRegex(ValueError,"version is unsupported"):
            replay_organization_roles(seed,tuple(events))
        self.assertEqual(seed.last_organization_stream_position,0)

    def test_replay_rejects_malformed_recognized_event_and_envelope(self):
        kernel,store,_,_,_,state=role_runtime(); kernel.execute(command())
        events=list(store.read(state.organization.organization_id))
        malformed_payload=dataclasses.replace(
            events[0],payload=FrozenMap({"operation_type":CREATE_ROLE_OPERATION,
                                         "disposition_id":"role-disposition-0"}),
        )
        with self.assertRaisesRegex(ValueError,"supported ordinary acceptance"):
            replay_organization_roles(role_seed(state),(malformed_payload,*events[1:]))
        malformed_envelope=dataclasses.replace(
            events[0],envelope=dataclasses.replace(events[0].envelope,message_type="AuditLinked"),
        )
        with self.assertRaisesRegex(ValueError,"type is inconsistent"):
            replay_organization_roles(role_seed(state),(malformed_envelope,*events[1:]))

    def test_role_created_requires_matching_accepted_create_role_lineage(self):
        kernel,store,_,_,_,state=role_runtime(); kernel.execute(command())
        events=list(store.read(state.organization.organization_id)); role_event=events[1]
        orphan=dataclasses.replace(
            role_event,envelope=dataclasses.replace(role_event.envelope,stream_position=1),
        )
        with self.assertRaisesRegex(ValueError,"orphan domain"):
            replay_organization_roles(role_seed(state),(orphan,))
        wrong_operation=dataclasses.replace(
            events[0],payload=FrozenMap({"operation_type":"OtherOperation",
                                         "operation_version":RECORD_V1,
                                         "disposition_id":events[0].payload["disposition_id"]}),
        )
        with self.assertRaisesRegex(ValueError,"supported ordinary acceptance"):
            replay_organization_roles(role_seed(state),(wrong_operation,*events[1:]))
        mismatched=dataclasses.replace(
            role_event,envelope=dataclasses.replace(
                role_event.envelope,recording_command_id=CommandId("command-other")),
        )
        with self.assertRaisesRegex(ValueError,"lineage does not match"):
            replay_organization_roles(role_seed(state),(events[0],mismatched,events[2]))

    def test_one_acceptance_cannot_authorize_multiple_roles_and_audit_must_match(self):
        kernel,store,_,_,_,state=role_runtime(); kernel.execute(command())
        accepted,role_event,audit=store.read(state.organization.organization_id)
        duplicate=dataclasses.replace(
            role_event,event_id=type(role_event.event_id)("role-event-duplicate"),
            envelope=dataclasses.replace(role_event.envelope,stream_position=3),
        )
        shifted_audit=dataclasses.replace(
            audit,envelope=dataclasses.replace(audit.envelope,stream_position=4),
        )
        with self.assertRaisesRegex(ValueError,"lacks its AuditLinked"):
            replay_organization_roles(role_seed(state),(accepted,role_event,duplicate,shifted_audit))
        wrong_audit=dataclasses.replace(
            audit,envelope=dataclasses.replace(
                audit.envelope,recording_command_id=CommandId("command-other")),
        )
        with self.assertRaisesRegex(ValueError,"AuditLinked lineage"):
            replay_organization_roles(role_seed(state),(accepted,role_event,wrong_audit))

    def test_command_has_no_initial_state_and_cannot_smuggle_active(self):
        self.assertNotIn("initial_state",CreateRoleCommand.__dataclass_fields__)
        base=command(); bad_submission=dataclasses.replace(
            base.submission,envelope=dataclasses.replace(
                base.submission.envelope,
                payload=FrozenMap({"role":base.role,"lifecycle_state":"active"}),
            ),
        )
        with self.assertRaises(ValueError): CreateRoleCommand(bad_submission,0,base.role)

    def test_malformed_payload_stops_before_governance_and_handle(self):
        base=command(); malformed=RuntimeCommand(
            dataclasses.replace(base.submission,envelope=dataclasses.replace(
                base.submission.envelope,payload=FrozenMap({"role":"invalid"}))),0,
        )
        kernel,store,_,authority,handler,state=role_runtime()
        result=kernel.execute(malformed)
        self.assertEqual(result.reason_code,ReasonCode.INPUT_MALFORMED)
        self.assertEqual((authority.calls,handler.calls),(0,0))
        self.assertEqual(store.read_calls,0)
        self.assertFalse(any(event.event_type=="RoleCreated" for event in store.read(state.organization.organization_id)))

    def test_missing_actor_context_fails_before_governance(self):
        malformed=command()
        object.__setattr__(malformed.submission.envelope,"initiating_actor_id",None)
        kernel,store,_,authority,handler,state=role_runtime()
        result=kernel.execute(malformed)
        self.assertEqual(result.reason_code,ReasonCode.INPUT_MALFORMED)
        self.assertEqual((authority.calls,handler.calls),(0,0))
        self.assertEqual(store.read_calls,0)
        self.assertFalse(any(event.event_type=="RoleCreated" for event in store.read(state.organization.organization_id)))

    def test_bootstrap_request_cannot_enter_ordinary_role_path(self):
        kernel,store,_,authority,handler,state=role_runtime()
        result=kernel.execute(bootstrap_request())
        self.assertEqual(result.reason_code,ReasonCode.INPUT_MALFORMED); self.assertEqual(store.read_calls,0)
        self.assertEqual((authority.calls,handler.calls),(0,0)); self.assertEqual(store.read(state.organization.organization_id),())

    def test_unfounded_or_mismatched_organization_fails_without_stream_creation(self):
        state=founded(); unfounded=dataclasses.replace(state,genesis_completed=False)
        kernel,store,_,authority,handler,_=role_runtime(state=unfounded)
        result=kernel.execute(command())
        self.assertEqual(result.reason_code,ReasonCode.ORG_UNKNOWN)
        self.assertEqual((authority.calls,handler.calls),(0,0)); self.assertEqual(store.read_calls,0)
        self.assertEqual(store.read(OrganizationId("org-bootstrap")),())
        kernel,store,_,authority,handler,_=role_runtime(state=state)
        result=kernel.execute(command(organization="org-other"))
        self.assertEqual(result.reason_code,ReasonCode.ORG_UNKNOWN)
        self.assertEqual((authority.calls,handler.calls),(0,0)); self.assertEqual(store.read_calls,0)
        self.assertEqual(store.read(OrganizationId("org-other")),())

    def test_missing_or_indeterminate_authority_fails_closed(self):
        base=command(); no_authority=CreateRoleCommand(
            dataclasses.replace(base.submission,authority_references=()),0,base.role,
        )
        kernel,store,_,authority,handler,state=role_runtime()
        result=kernel.execute(no_authority)
        self.assertEqual(result.reason_code,ReasonCode.AUTH_MISSING); self.assertEqual(handler.calls,0)
        self.assertFalse(any(event.event_type=="RoleCreated" for event in store.read(state.organization.organization_id)))
        indeterminate=IndeterminateAuthority(); kernel,store,_,_,handler,state=role_runtime(authority=indeterminate)
        result=kernel.execute(command())
        self.assertEqual(result.reason_code,ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE)
        self.assertEqual((indeterminate.calls,handler.calls),(1,0))

    def test_handler_is_pure_and_performs_no_governance_or_storage(self):
        state=founded(); handler=CreateRoleHandler(role_seed(state)); context_command=command()
        from aios_kernel.runtime import HandlerContext, HandlerAccepted
        result=handler.handle(HandlerContext(
            context_command,(),NOW,OrganizationId("org-bootstrap"),ActorId("human-founder")))
        self.assertIsInstance(result,HandlerAccepted)
        self.assertEqual(tuple(event.event_type for event in result.events),("RoleCreated",))

    def test_existing_and_founding_role_duplicates_are_rejected_without_domain_event(self):
        kernel,store,_,_,_,state=role_runtime(); kernel.execute(command())
        prior=store.read(state.organization.organization_id)
        duplicate=command(command_id="command-duplicate",idempotency="create-role/2",expected_position=len(prior))
        result=kernel.execute(duplicate)
        self.assertEqual(result.reason_code,ReasonCode.LIFECYCLE_INVALID_TRANSITION)
        self.assertEqual(tuple(event for event in store.read(state.organization.organization_id)[len(prior):]
                               if event.event_type=="RoleCreated"),())
        founding=attributes(role=str(state.founding_role.role_id),name=state.founding_role.name)
        prior=store.read(state.organization.organization_id)
        result=kernel.execute(command(role=founding,command_id="command-founding",
                                      idempotency="create-role/3",expected_position=len(prior)))
        self.assertEqual(result.reason_code,ReasonCode.LIFECYCLE_INVALID_TRANSITION)

    def test_exact_redelivery_returns_original_without_evaluation_or_append(self):
        kernel,store,ids,authority,handler,state=role_runtime(); original=kernel.execute(command())
        before=(store.read(state.organization.organization_id),tuple(ids.calls),authority.calls,handler.calls)
        redelivery=command()
        redelivery=dataclasses.replace(
            redelivery,submission=dataclasses.replace(
                redelivery.submission,envelope=dataclasses.replace(
                    redelivery.submission.envelope,message_id=MessageId("message-redelivery"),
                ),
            ),
        )
        repeated=kernel.execute(redelivery)
        self.assertEqual(repeated,original)
        self.assertEqual((store.read(state.organization.organization_id),tuple(ids.calls),authority.calls,handler.calls),before)

    def test_exact_redelivery_of_recorded_rejection_returns_original(self):
        kernel,store,ids,authority,handler,state=role_runtime(); kernel.execute(command())
        rejected_command=command(command_id="command-duplicate",idempotency="duplicate",
                                 expected_position=len(store.read(state.organization.organization_id)))
        original=kernel.execute(rejected_command)
        before=(store.read(state.organization.organization_id),tuple(ids.calls),authority.calls,handler.calls)
        repeated=kernel.execute(rejected_command)
        self.assertEqual(repeated,original)
        self.assertEqual((store.read(state.organization.organization_id),tuple(ids.calls),authority.calls,handler.calls),before)

    def test_conflicting_idempotency_reuse_fails_without_mutation(self):
        kernel,store,_,_,_,state=role_runtime(); kernel.execute(command())
        before=store.read(state.organization.organization_id)
        changed=command(role=attributes(role="role-changed"),command_id="command-create-role",
                        idempotency="create-role/1",expected_position=0)
        result=kernel.execute(changed)
        self.assertEqual(result.reason_code,ReasonCode.IDEMPOTENCY_CONFLICT)
        self.assertEqual(store.read(state.organization.organization_id),before)

    def test_idempotency_is_rechecked_atomically_before_event_allocation(self):
        donor,donor_store,_,_,_,state=role_runtime(); donor.execute(command())
        registration=next(iter(donor_store._idempotency.values()))
        class RaceStore(InMemoryRuntimeEventStore):
            def __init__(self): super().__init__(); self.inserted=False
            def inspect_idempotency(self,scope,command_fingerprint):
                from aios_kernel.idempotency import IdempotencyInspection, IdempotencyState
                return IdempotencyInspection(IdempotencyState.NEW)
            def append_if_current(self,organization_id,expected_prior_position,
                                  scope,fingerprint,build_batch):
                if not self.inserted:
                    self._idempotency[self._scope_key(scope)]=StoredRuntimeIdempotency(
                        registration.fingerprint,registration.result,
                    )
                    self.inserted=True
                return super().append_if_current(
                    organization_id,expected_prior_position,scope,fingerprint,build_batch,
                )
        store=RaceStore(); kernel,_,ids,authority,handler,_=role_runtime(store=store,state=state)
        result=kernel.execute(command())
        self.assertIsInstance(result,RuntimeAccepted)
        self.assertEqual(ids.calls,[])
        self.assertEqual(store.read(state.organization.organization_id),())
        self.assertEqual((authority.calls,handler.calls),(1,1))

    def test_expected_version_race_allows_at_most_one_creation(self):
        kernel,store,_,_,_,state=role_runtime()
        first=kernel.execute(command(role=attributes(role="role-a"),command_id="command-a",idempotency="a"))
        prior=store.read(state.organization.organization_id)
        second=kernel.execute(command(role=attributes(role="role-b"),command_id="command-b",idempotency="b"))
        self.assertIsInstance(first,RuntimeAccepted)
        self.assertEqual(second.reason_code,ReasonCode.STREAM_CONCURRENCY_CONFLICT)
        self.assertEqual(store.read(state.organization.organization_id),prior)

    def test_same_name_different_role_ids_are_distinct_and_globally_ordered(self):
        kernel,store,_,_,_,state=role_runtime()
        kernel.execute(command(role=attributes(role="role-a",name="Shared"),command_id="command-a",idempotency="a"))
        position=len(store.read(state.organization.organization_id))
        kernel.execute(command(role=attributes(role="role-b",name="Shared"),command_id="command-b",idempotency="b",expected_position=position))
        events=store.read(state.organization.organization_id)
        projection=replay_organization_roles(role_seed(state),events)
        self.assertEqual(tuple(role.name for role in projection.roles if not role.is_founding_role),("Shared","Shared"))
        self.assertEqual(tuple(event.envelope.stream_position for event in events),tuple(range(1,len(events)+1)))
        self.assertEqual({str(event.envelope.stream_id) for event in events},{"organization:org-bootstrap"})

    def test_replay_rejects_duplicate_role_and_wrong_organization(self):
        kernel,store,_,_,_,state=role_runtime(); kernel.execute(command())
        events=store.read(state.organization.organization_id); role_event=events[1]
        duplicate=dataclasses.replace(role_event,envelope=dataclasses.replace(
            role_event.envelope,stream_position=len(events)+1),event_id=type(role_event.event_id)("duplicate-role-event"))
        with self.assertRaises(ValueError): replay_organization_roles(role_seed(state),events+(duplicate,))
        wrong=dataclasses.replace(role_event,envelope=dataclasses.replace(
            role_event.envelope,organization_id=OrganizationId("org-other")))
        with self.assertRaises(ValueError): replay_organization_roles(role_seed(state),(events[0],wrong,events[2]))

    def test_replay_rejects_unsupported_role_event_version(self):
        kernel,store,_,_,_,state=role_runtime(); kernel.execute(command())
        events=list(store.read(state.organization.organization_id))
        events[1]=dataclasses.replace(events[1],event_version=RecordTypeVersion("2.0"))
        with self.assertRaises(ValueError): replay_organization_roles(role_seed(state),tuple(events))

    def test_unsupported_command_and_schema_versions_fail_closed(self):
        base=command()
        unsupported=RuntimeCommand(
            dataclasses.replace(base.submission,operation_version=RecordTypeVersion("2.0")),0,
        )
        kernel,store,_,authority,handler,state=role_runtime()
        result=kernel.execute(unsupported)
        self.assertEqual(result.reason_code,ReasonCode.VER_UNSUPPORTED)
        self.assertEqual((authority.calls,handler.calls),(0,0))
        wrong_schema=RuntimeCommand(
            dataclasses.replace(base.submission,envelope=dataclasses.replace(
                base.submission.envelope,schema_version=RecordTypeVersion("2.0"))),0,
        )
        kernel,store,_,authority,handler,state=role_runtime()
        result=kernel.execute(wrong_schema)
        self.assertEqual(result.reason_code,ReasonCode.VER_UNSUPPORTED)
        self.assertEqual((authority.calls,handler.calls),(0,0))

    def test_append_failure_leaves_stream_without_role_event(self):
        class FailingStore(InMemoryRuntimeEventStore):
            def append_if_current(self,*args,**kwargs):
                return AppendRejected(ReasonCode.APPEND_FAILED,"synthetic failure")
        store=FailingStore(); kernel,_,_,_,handler,state=role_runtime(store=store)
        result=kernel.execute(command())
        self.assertEqual(result.reason_code,ReasonCode.APPEND_FAILED)
        self.assertEqual(handler.calls,1); self.assertEqual(store.read(state.organization.organization_id),())

    def test_no_tenant_or_role_stream_model_is_introduced(self):
        source=(pathlib.Path(__file__).parents[2]/"src"/"aios_kernel"/"create_role.py").read_text()
        self.assertNotIn("tenant_id",source.lower())
        self.assertNotIn("RoleEventStore",source)

    def test_imports_are_side_effect_free(self):
        completed=subprocess.run(
            [sys.executable,"-c","import aios_kernel; import aios_kernel.create_role"],
            env={**__import__("os").environ,"PYTHONDONTWRITEBYTECODE":"1","PYTHONPATH":"src"},
            cwd=pathlib.Path(__file__).parents[2],capture_output=True,text=True,check=False,
        )
        self.assertEqual((completed.returncode,completed.stdout,completed.stderr),(0,"",""))


if __name__=="__main__": unittest.main()
