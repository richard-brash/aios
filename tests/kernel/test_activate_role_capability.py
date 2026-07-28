"""Behavioral architecture tests for governed Role activation."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
import pathlib
import subprocess
import sys
import unittest

from aios_kernel.activate_role import (
    ACTIVATE_ROLE_OPERATION, ACTIVATE_ROLE_VERSION, ROLE_ACTIVATE_AUTHORITY_SCOPE,
    ActivateRoleCommand, ActivateRoleGovernanceEvaluator, ActivateRoleHandler,
    ActivateRolePayload,
)
from aios_kernel.create_role import (
    OrganizationRoleReducer, ROLE_ACTIVATED_EVENT, RoleProjection,
    replay_organization_roles,
)
from aios_kernel.reference import (
    DeterministicIdentifiers, DeterministicRecordingBoundaryResolver, FixedClock,
    InMemoryRuntimeEventStore,
)
from aios_kernel.runtime import (
    HandlerAccepted, HandlerContext, KernelRuntime, ProcessingAllowed, ProcessingDenied,
    RuntimeAccepted, RuntimeCommand,
)
from aios_protocol.admission import AdmissionEstablished
from aios_protocol.commands import CommandSubmission, EntityReference, RiskClass
from aios_protocol.envelope import CallerEnvelope
from aios_protocol.identifiers import (
    ActorId, AuditRecordId, AuthorityGrantId, CommandId, CorrelationId, EventId,
    IntegrityReference, MessageId, OperationId, OrganizationId, RoleId, StreamId,
)
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import PAYLOAD_V1, RECORD_V1, RecordTypeVersion
from conformance_map import ACTIVATE_ROLE_SCENARIO_MAP

from test_create_role_capability import (
    AllowAuthority, attributes, command as create_command, founded, role_runtime, role_seed,
    task_command, task_runtime,
)


NOW=datetime(2045,6,7,8,9,10,tzinfo=timezone.utc)


def activation_command(*,role="role-ordinary",revision=1,organization="org-bootstrap",
                       command_id="command-activate-role",idempotency="activate-role/1",
                       expected_position=3,version=ACTIVATE_ROLE_VERSION):
    payload=ActivateRolePayload(RoleId(role),revision)
    envelope=CallerEnvelope(
        MessageId(f"message-{command_id}"),"CommandSubmission",OrganizationId(organization),
        ActorId("human-founder"),CorrelationId(f"correlation-{command_id}"),NOW,"internal",
        "activate governed organizational structure",ACTIVATE_ROLE_OPERATION,PAYLOAD_V1,
        FrozenMap({"role_id":payload.role_id,"expected_entity_revision":revision}),
    )
    submission=CommandSubmission(
        envelope,CommandId(command_id),OperationId(f"operation-{command_id}"),
        ACTIVATE_ROLE_OPERATION,version,
        (EntityReference("Role",role,revision),),idempotency,None,False,
        IntegrityReference(f"proof:{organization}:human-founder"),
        (AuthorityGrantId(f"grant-{organization}"),),
        lifecycle_preconditions=FrozenMap({"current_state":"draft","requested_state":"active"}),
        risk=RiskClass.REVERSIBLE,result_criteria=FrozenMap({"lifecycle_state":"active"}),
    )
    return ActivateRoleCommand(submission,expected_position,payload)


class AllowActivation:
    def __init__(self): self.calls=0
    def evaluate(self,context):
        self.calls+=1
        return ProcessingAllowed(FrozenMap({"authority_scope":ROLE_ACTIVATE_AUTHORITY_SCOPE}))


class DenyActivation:
    def __init__(self): self.calls=0
    def evaluate(self,context):
        self.calls+=1
        return ProcessingDenied(ReasonCode.AUTH_INSUFFICIENT,"authority","role.activate denied")


class CountingActivationHandler(ActivateRoleHandler):
    def __init__(self,state): super().__init__(state); self.validations=0; self.calls=0
    def validate(self,command): self.validations+=1; return super().validate(command)
    def handle(self,context): self.calls+=1; return super().handle(context)


def activation_admission_for(command):
    submission=command.submission
    return AdmissionEstablished(
        submission.envelope.message_id,submission.command_id,
        submission.envelope.organization_id,submission.envelope.initiating_actor_id,
        IntegrityReference("genesis-activate-role"),IntegrityReference("identity-activate-role"),
        submission.invocation_proof_reference,(IntegrityReference("authentication-activate-role"),),
        IntegrityReference("activate-role-resolver"),RECORD_V1,
    )


def activation_runtime(*,authority=None,store=None,state=None,create_role=True,resolver=None):
    state=state or founded(); store=store or InMemoryRuntimeEventStore()
    if create_role:
        creator,_,_,_,_,_=role_runtime(state=state,store=store)
        created=creator.execute(create_command())
        if not isinstance(created,RuntimeAccepted):
            raise AssertionError("activation fixture could not create draft Role")
    authority=authority or AllowActivation(); handler=CountingActivationHandler(role_seed(state))
    evaluator=ActivateRoleGovernanceEvaluator(authority_evaluator=authority)
    resolver=resolver or DeterministicRecordingBoundaryResolver(
        (activation_admission_for(activation_command()),),
    )
    identifiers=DeterministicIdentifiers(
        [f"activate-disposition-{i}" for i in range(30)],
        [f"activate-audit-{i}" for i in range(30)],
        [f"activate-event-{i}" for i in range(100)],
    )
    kernel=KernelRuntime(clock=FixedClock(NOW),identifiers=identifiers,
                         evaluator=evaluator,store=store,resolver=resolver,handlers=(handler,))
    return kernel,store,identifiers,authority,handler,state


class ActivateRoleCapabilityTests(unittest.TestCase):
    def test_authorized_activation_appends_one_versioned_domain_event(self):
        kernel,store,_,authority,handler,state=activation_runtime()
        result=kernel.execute(activation_command())
        self.assertIsInstance(result,RuntimeAccepted)
        self.assertEqual((authority.calls,handler.calls),(1,1))
        self.assertEqual(len(result.domain_events),1)
        event=result.domain_events[0]
        self.assertEqual((event.event_type,event.event_version),(ROLE_ACTIVATED_EVENT,RECORD_V1))
        self.assertEqual(str(event.envelope.stream_id),"organization:org-bootstrap")
        self.assertEqual(event.envelope.stream_position,5)
        self.assertEqual(store.read(state.organization.organization_id)[-3:],result.recorded_events)
        evidence=result.recorded_events[-1].payload["admission_evidence"]
        self.assertEqual((evidence.organization_id,evidence.initiating_actor_id,
                          evidence.command_id,evidence.invocation_proof_reference),(
            OrganizationId("org-bootstrap"),ActorId("human-founder"),
            CommandId("command-activate-role"),
            IntegrityReference("proof:org-bootstrap:human-founder"),
        ))
        self.assertEqual(
            tuple(record.envelope.stream_position for record in store.read(state.organization.organization_id)),
            tuple(range(1,7)),
        )

    def test_activation_changes_only_state_and_revision(self):
        kernel,store,_,_,_,state=activation_runtime()
        before=replay_organization_roles(role_seed(state),store.read(state.organization.organization_id))
        kernel.execute(activation_command())
        after=replay_organization_roles(role_seed(state),store.read(state.organization.organization_id))
        original=before.role(RoleId("role-ordinary")); activated=after.role(RoleId("role-ordinary"))
        self.assertEqual((original.lifecycle_state,original.entity_revision),("draft",1))
        self.assertEqual((activated.lifecycle_state,activated.entity_revision),("active",2))
        self.assertEqual(dataclasses.replace(activated,lifecycle_state="draft",entity_revision=1),original)

    def test_event_payload_is_exact_and_replay_is_deterministic_without_effects(self):
        kernel,store,ids,authority,handler,state=activation_runtime(); result=kernel.execute(activation_command())
        self.assertEqual(result.domain_events[0].payload,FrozenMap({
            "role_id":RoleId("role-ordinary"),"prior_lifecycle_state":"draft",
            "lifecycle_state":"active","prior_entity_revision":1,"entity_revision":2,
        }))
        dependencies=(tuple(ids.calls),authority.calls,handler.calls)
        events=store.read(state.organization.organization_id)
        self.assertEqual(replay_organization_roles(role_seed(state),events),
                         replay_organization_roles(role_seed(state),events))
        self.assertEqual((tuple(ids.calls),authority.calls,handler.calls),dependencies)

    def test_nonexistent_and_already_active_roles_reject_invalid_transition(self):
        kernel,store,_,_,_,state=activation_runtime()
        position=len(store.read(state.organization.organization_id))
        missing=kernel.execute(activation_command(role="role-missing",command_id="missing",
                                                  idempotency="missing",expected_position=position))
        self.assertEqual(missing.reason_code,ReasonCode.LIFECYCLE_INVALID_TRANSITION)
        position=len(store.read(state.organization.organization_id))
        accepted=kernel.execute(activation_command(command_id="accepted",idempotency="accepted",
                                                   expected_position=position))
        self.assertIsInstance(accepted,RuntimeAccepted)
        position=len(store.read(state.organization.organization_id))
        repeated=kernel.execute(activation_command(command_id="new-command",idempotency="new-key",
                                                   expected_position=position))
        self.assertEqual(repeated.reason_code,ReasonCode.LIFECYCLE_INVALID_TRANSITION)
        self.assertFalse(any(event.event_type==ROLE_ACTIVATED_EVENT
                             for event in store.read(state.organization.organization_id)[position:]))

    def test_founding_role_uses_the_general_already_active_rejection(self):
        kernel,store,_,_,_,state=activation_runtime()
        position=len(store.read(state.organization.organization_id))
        result=kernel.execute(activation_command(
            role=str(state.founding_role.role_id),command_id="founding",idempotency="founding",
            expected_position=position,
        ))
        self.assertEqual(result.reason_code,ReasonCode.LIFECYCLE_INVALID_TRANSITION)

    def test_stale_role_revision_rejects_without_activation(self):
        kernel,store,_,_,_,state=activation_runtime(); position=len(store.read(state.organization.organization_id))
        result=kernel.execute(activation_command(revision=2,expected_position=position))
        self.assertEqual(result.reason_code,ReasonCode.STATE_STALE_VERSION)
        self.assertFalse(any(event.event_type==ROLE_ACTIVATED_EVENT
                             for event in store.read(state.organization.organization_id)[position:]))

    def test_stale_organization_position_precedes_governance_and_allocates_nothing(self):
        kernel,store,ids,authority,handler,state=activation_runtime()
        before=store.read(state.organization.organization_id)
        result=kernel.execute(activation_command(expected_position=0))
        self.assertEqual(result.reason_code,ReasonCode.STREAM_CONCURRENCY_CONFLICT)
        self.assertEqual((store.read(state.organization.organization_id),ids.calls,authority.calls,handler.calls),
                         (before,[],0,0))

    def test_governance_denial_and_invalid_output_fail_closed(self):
        denied=DenyActivation(); kernel,store,_,_,handler,state=activation_runtime(authority=denied)
        before_projection=replay_organization_roles(role_seed(state),store.read(state.organization.organization_id))
        result=kernel.execute(activation_command())
        self.assertEqual(result.reason_code,ReasonCode.AUTH_INSUFFICIENT)
        self.assertEqual(handler.calls,0)
        rejected=store.read(state.organization.organization_id)[-2:]
        self.assertEqual(tuple(event.event_type for event in rejected),
                         ("CommandRejected","AuditLinked"))
        self.assertEqual(rejected[-1].payload["admission_evidence"].command_id,
                         CommandId("command-activate-role"))
        self.assertFalse(any(event.event_type==ROLE_ACTIVATED_EVENT for event in rejected))
        self.assertEqual(replay_organization_roles(role_seed(state),store.read(state.organization.organization_id)).role(RoleId("role-ordinary")),
                         before_projection.role(RoleId("role-ordinary")))
        class InvalidAuthority:
            def evaluate(self,context): return ProcessingAllowed(FrozenMap())
        kernel,store,_,_,handler,state=activation_runtime(authority=InvalidAuthority())
        result=kernel.execute(activation_command())
        self.assertEqual(result.reason_code,ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE)
        self.assertEqual(handler.calls,0)

    def test_handler_is_pure_and_does_not_evaluate_governance_or_persist(self):
        kernel,store,_,_,_,state=activation_runtime(); events=store.read(state.organization.organization_id)
        result=ActivateRoleHandler(role_seed(state)).handle(HandlerContext(
            activation_command(),events,NOW,OrganizationId("org-bootstrap"),ActorId("human-founder")))
        self.assertIsInstance(result,HandlerAccepted)
        self.assertEqual(tuple(event.event_type for event in result.events),(ROLE_ACTIVATED_EVENT,))
        self.assertEqual(store.read(state.organization.organization_id),events)

    def test_exact_redelivery_returns_original_without_append_or_allocation(self):
        kernel,store,ids,authority,handler,state=activation_runtime(); original=kernel.execute(activation_command())
        before=(store.read(state.organization.organization_id),tuple(ids.calls),authority.calls,handler.calls)
        repeated=kernel.execute(activation_command())
        self.assertEqual(repeated,original)
        self.assertEqual((store.read(state.organization.organization_id),tuple(ids.calls),authority.calls,handler.calls),before)

    def test_conflicting_idempotency_reuse_fails_closed(self):
        kernel,store,_,_,_,state=activation_runtime(); kernel.execute(activation_command())
        before=store.read(state.organization.organization_id)
        conflict=activation_command(role=str(state.founding_role.role_id),expected_position=0)
        result=kernel.execute(conflict)
        self.assertEqual(result.reason_code,ReasonCode.IDEMPOTENCY_CONFLICT)
        self.assertEqual(store.read(state.organization.organization_id),before)

    def test_malformed_contract_stops_before_governance_and_handler(self):
        valid=activation_command(); malformed=RuntimeCommand(dataclasses.replace(
            valid.submission,lifecycle_preconditions=FrozenMap({"current_state":"active"})),3)
        kernel,store,_,authority,handler,state=activation_runtime()
        result=kernel.execute(malformed)
        self.assertEqual(result.reason_code,ReasonCode.INPUT_MALFORMED)
        self.assertEqual((authority.calls,handler.calls),(0,0))
        self.assertFalse(any(event.event_type==ROLE_ACTIVATED_EVENT
                             for event in store.read(state.organization.organization_id)))
        with self.assertRaises(ValueError):
            dataclasses.replace(valid,submission=dataclasses.replace(
                valid.submission,envelope=dataclasses.replace(
                    valid.submission.envelope,payload=FrozenMap({
                        "role_id":valid.payload.role_id,
                        "expected_entity_revision":1,"extra":"prohibited",
                    }),
                ),
            ))

    def test_unsupported_operation_version_fails_before_governance(self):
        valid=activation_command(); unsupported=RuntimeCommand(
            dataclasses.replace(valid.submission,operation_version=RecordTypeVersion("2.0")),3,
        )
        kernel,_,_,authority,handler,_=activation_runtime()
        result=kernel.execute(unsupported)
        self.assertEqual(result.reason_code,ReasonCode.VER_UNSUPPORTED)
        self.assertEqual((authority.calls,handler.calls),(0,0))
        wrong_schema=RuntimeCommand(dataclasses.replace(
            valid.submission,envelope=dataclasses.replace(
                valid.submission.envelope,schema_version=RecordTypeVersion("2.0")),
        ),3)
        kernel,_,_,authority,handler,_=activation_runtime()
        result=kernel.execute(wrong_schema)
        self.assertEqual(result.reason_code,ReasonCode.VER_UNSUPPORTED)
        self.assertEqual((authority.calls,handler.calls),(0,0))

    def test_organization_isolation_fails_closed(self):
        kernel,store,_,authority,handler,_=activation_runtime()
        prior_reads=store.read_calls
        result=kernel.execute(activation_command(organization="org-other",expected_position=0))
        self.assertEqual(result.reason_code,ReasonCode.ORG_UNKNOWN)
        self.assertEqual((authority.calls,handler.calls),(0,0))
        self.assertEqual(store.read_calls,prior_reads)
        self.assertEqual(store.read(OrganizationId("org-other")),())

    def test_replay_rejects_nonexistent_non_draft_and_bad_revisions(self):
        kernel,store,_,_,_,state=activation_runtime(); result=kernel.execute(activation_command())
        events=store.read(state.organization.organization_id); activation=result.domain_events[0]
        without_creation=(events[0],dataclasses.replace(activation,envelope=dataclasses.replace(
            activation.envelope,stream_position=2)),events[-1])
        with self.assertRaises(ValueError): replay_organization_roles(role_seed(state),without_creation)
        duplicate=dataclasses.replace(activation,event_id=type(activation.event_id)("duplicate-activation"),
                                      envelope=dataclasses.replace(activation.envelope,stream_position=len(events)+1))
        with self.assertRaises(ValueError): replay_organization_roles(role_seed(state),events+(duplicate,))
        bad_revision=dataclasses.replace(activation,payload=FrozenMap({
            **dict(activation.payload),"entity_revision":4,
        }))
        with self.assertRaises(ValueError): replay_organization_roles(
            role_seed(state),events[:4]+(bad_revision,)+events[5:])

    def test_replay_rejects_event_version_organization_and_stream_mismatch(self):
        kernel,store,_,_,_,state=activation_runtime(); result=kernel.execute(activation_command())
        events=store.read(state.organization.organization_id); activation=result.domain_events[0]
        variants=(
            dataclasses.replace(activation,event_version=RecordTypeVersion("2.0")),
            dataclasses.replace(activation,envelope=dataclasses.replace(
                activation.envelope,organization_id=OrganizationId("org-other"))),
            dataclasses.replace(activation,envelope=dataclasses.replace(
                activation.envelope,stream_id=StreamId("organization:org-other"))),
        )
        for invalid in variants:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    replay_organization_roles(role_seed(state),events[:4]+(invalid,)+events[5:])

    def test_replay_rejects_activation_without_matching_accepted_operation(self):
        kernel,store,_,_,_,state=activation_runtime(); kernel.execute(activation_command())
        events=list(store.read(state.organization.organization_id))
        events[3]=dataclasses.replace(events[3],payload=FrozenMap({
            **dict(events[3].payload),"operation_type":"CreateRole",
        }))
        with self.assertRaises(ValueError): replay_organization_roles(role_seed(state),tuple(events))

    def test_replay_rejects_orphan_and_duplicate_activation_lineage(self):
        kernel,store,_,_,_,state=activation_runtime(); result=kernel.execute(activation_command())
        events=store.read(state.organization.organization_id); activation=result.domain_events[0]
        orphan=dataclasses.replace(
            activation,envelope=dataclasses.replace(activation.envelope,stream_position=4),
        )
        orphan_audit=dataclasses.replace(
            events[5],envelope=dataclasses.replace(events[5].envelope,stream_position=5),
        )
        with self.assertRaisesRegex(ValueError,"orphan domain"):
            replay_organization_roles(role_seed(state),events[:3]+(orphan,orphan_audit))

        duplicate=dataclasses.replace(
            activation,event_id=EventId("duplicate-activation"),
            envelope=dataclasses.replace(
                activation.envelope,message_id=MessageId("message-duplicate-activation"),
                stream_position=6,
                integrity_reference=IntegrityReference("integrity:duplicate-activation"),
            ),
            integrity_reference=IntegrityReference("integrity:duplicate-activation"),
        )
        shifted_audit=dataclasses.replace(
            events[5],envelope=dataclasses.replace(events[5].envelope,stream_position=7),
        )
        with self.assertRaisesRegex(ValueError,"lacks its AuditLinked"):
            replay_organization_roles(
                role_seed(state),events[:5]+(duplicate,shifted_audit),
            )

    def test_replay_rejects_activation_command_target_and_audit_mismatch(self):
        kernel,store,_,_,_,state=activation_runtime(); kernel.execute(activation_command())
        events=list(store.read(state.organization.organization_id))
        variants=[]
        variants.append(dataclasses.replace(
            events[4],envelope=dataclasses.replace(
                events[4].envelope,recording_command_id=CommandId("command-other"),
            ),
        ))
        variants.append(dataclasses.replace(
            events[3],entity_references=(EntityReference("Role","role-other",1),),
        ))
        for invalid in variants:
            history=list(events)
            history[4 if invalid.event_type == ROLE_ACTIVATED_EVENT else 3]=invalid
            with self.subTest(event=invalid):
                with self.assertRaises(ValueError):
                    replay_organization_roles(role_seed(state),tuple(history))

        invalid_audit=dataclasses.replace(
            events[5],audit_record_id=AuditRecordId("audit-other"),
        )
        with self.assertRaisesRegex(ValueError,"AuditLinked lineage"):
            replay_organization_roles(role_seed(state),tuple(events[:5]+[invalid_audit]))

    def test_replay_rejects_unsupported_accepted_operation_version(self):
        kernel,store,_,_,_,state=activation_runtime(); kernel.execute(activation_command())
        events=list(store.read(state.organization.organization_id))
        events[3]=dataclasses.replace(events[3],payload=FrozenMap({
            **dict(events[3].payload),"operation_version":RecordTypeVersion("2.0"),
        }))
        with self.assertRaisesRegex(ValueError,"supported ordinary acceptance"):
            replay_organization_roles(role_seed(state),tuple(events))

    def test_all_non_draft_lifecycle_states_reject(self):
        state=founded()
        for lifecycle in ("active","suspended","retired","archived","unknown"):
            role=RoleProjection(
                RoleId(f"role-{lifecycle}"),state.organization.organization_id,lifecycle,
                ("duty",),("capability",),FrozenMap(),"review",("separation",),
                lifecycle,2,ActorId("human-founder"),CommandId("created"),None,None,False,
            )
            projection=dataclasses.replace(role_seed(state),roles=role_seed(state).roles+(role,))
            handled=ActivateRoleHandler(projection).handle(HandlerContext(
                activation_command(role=str(role.role_id),revision=2),(),NOW,
                state.organization.organization_id,ActorId("human-founder"),
            ))
            with self.subTest(lifecycle=lifecycle):
                self.assertEqual(handled.reason_code,ReasonCode.LIFECYCLE_INVALID_TRANSITION)

    def test_independently_required_governance_evidence_fails_closed(self):
        class ApprovalRequired:
            def __init__(self): self.calls=0
            def evaluate(self,context):
                self.calls+=1
                return ProcessingDenied(
                    ReasonCode.APPROVAL_MISSING,"approval",
                    "controlling governance requires Approval",
                )
        evaluator=ApprovalRequired()
        kernel,store,_,_,handler,state=activation_runtime(authority=evaluator)
        position=len(store.read(state.organization.organization_id))
        result=kernel.execute(activation_command(expected_position=position))
        self.assertEqual(result.reason_code,ReasonCode.APPROVAL_MISSING)
        self.assertEqual((evaluator.calls,handler.calls),(1,0))
        self.assertFalse(any(event.event_type==ROLE_ACTIVATED_EVENT
                             for event in store.read(state.organization.organization_id)[position:]))

    def test_same_display_name_activates_only_stable_role_identity(self):
        state=founded(); store=InMemoryRuntimeEventStore()
        creator,_,_,_,_,_=role_runtime(state=state,store=store)
        creator.execute(create_command(
            role=attributes("role-a","Shared"),command_id="create-a",idempotency="a",
        ))
        creator.execute(create_command(
            role=attributes("role-b","Shared"),command_id="create-b",idempotency="b",
            expected_position=3,
        ))
        activate=activation_command(
            role="role-b",command_id="activate-b",idempotency="activate-b",
            expected_position=6,
        )
        kernel,_,_,_,_,_=activation_runtime(
            state=state,store=store,create_role=False,
            resolver=DeterministicRecordingBoundaryResolver((activation_admission_for(activate),)),
        )
        self.assertIsInstance(kernel.execute(activate),RuntimeAccepted)
        projected=replay_organization_roles(role_seed(state),store.read(state.organization.organization_id))
        self.assertEqual(projected.role(RoleId("role-a")).lifecycle_state,"draft")
        self.assertEqual(projected.role(RoleId("role-b")).lifecycle_state,"active")

    def test_activation_replay_lineage_and_mixed_history_conformance(self):
        state=founded(); store=InMemoryRuntimeEventStore()
        before=task_command(suffix="before",expected_position=0)
        self.assertIsInstance(task_runtime(before,store)[0].execute(before),RuntimeAccepted)
        creator,_,_,_,_,_=role_runtime(
            state=state,store=store,
            resolver=DeterministicRecordingBoundaryResolver(
                (activation_admission_for(create_command(expected_position=5)),)),
        )
        created=create_command(expected_position=5)
        self.assertIsInstance(creator.execute(created),RuntimeAccepted)
        rejected=task_command(suffix="rejected",expected_position=8)
        class DenyTask:
            def evaluate(self,context):
                return ProcessingDenied(ReasonCode.AUTH_INSUFFICIENT,"authority","denied")
        self.assertEqual(
            task_runtime(rejected,store,authority=DenyTask())[0].execute(rejected).reason_code,
            ReasonCode.AUTH_INSUFFICIENT,
        )
        activate=activation_command(expected_position=10)
        kernel,_,_,_,_,_=activation_runtime(
            state=state,store=store,create_role=False,
            resolver=DeterministicRecordingBoundaryResolver((activation_admission_for(activate),)),
        )
        self.assertIsInstance(kernel.execute(activate),RuntimeAccepted)
        after=task_command(suffix="after",expected_position=13)
        self.assertIsInstance(task_runtime(after,store)[0].execute(after),RuntimeAccepted)
        history=store.read(state.organization.organization_id)
        self.assertEqual(tuple(event.event_type for event in history),(
            "CommandAccepted","TaskCreated","DecisionLinked","WorkRootLinked","AuditLinked",
            "CommandAccepted","RoleCreated","AuditLinked",
            "CommandRejected","AuditLinked",
            "CommandAccepted","RoleActivated","AuditLinked",
            "CommandAccepted","TaskCreated","DecisionLinked","WorkRootLinked","AuditLinked",
        ))
        projected=replay_organization_roles(role_seed(state),history)
        role=projected.role(RoleId("role-ordinary"))
        self.assertEqual((role.lifecycle_state,role.entity_revision),("active",2))
        self.assertEqual(projected.last_organization_stream_position,18)
        corrupt=list(history)
        corrupt[11]=dataclasses.replace(
            corrupt[11],event_type="UnknownActivationFact",
            envelope=dataclasses.replace(
                corrupt[11].envelope,message_type="UnknownActivationFact"),
        )
        with self.assertRaisesRegex(ValueError,"type is unsupported"):
            replay_organization_roles(role_seed(state),tuple(corrupt))
        wrong_operation=list(history)
        wrong_operation[10]=dataclasses.replace(
            wrong_operation[10],payload=FrozenMap({
                **dict(wrong_operation[10].payload),"operation_type":"CreateRole",
            }),
        )
        with self.assertRaises(ValueError):
            replay_organization_roles(role_seed(state),tuple(wrong_operation))
        evidence=history[12].payload["admission_evidence"]
        bad_evidence=dataclasses.replace(evidence,initiating_actor_id=ActorId("actor-other"))
        mismatched_audit=list(history)
        mismatched_audit[12]=dataclasses.replace(
            mismatched_audit[12],payload=FrozenMap({
                **dict(mismatched_audit[12].payload),"admission_evidence":bad_evidence,
            }),
        )
        with self.assertRaisesRegex(ValueError,"admission evidence"):
            replay_organization_roles(role_seed(state),tuple(mismatched_audit))

    def test_protocol_version_and_organization_validation_fail_closed(self):
        valid=activation_command()
        malformed=RuntimeCommand(dataclasses.replace(
            valid.submission,lifecycle_preconditions=FrozenMap({"current_state":"active"})),3)
        kernel,store,ids,authority,handler,state=activation_runtime()
        before=store.read(state.organization.organization_id)
        self.assertEqual(kernel.execute(malformed).reason_code,ReasonCode.INPUT_MALFORMED)
        unsupported=RuntimeCommand(
            dataclasses.replace(valid.submission,operation_version=RecordTypeVersion("2.0")),3)
        self.assertEqual(kernel.execute(unsupported).reason_code,ReasonCode.VER_UNSUPPORTED)
        foreign=activation_command(organization="org-other",expected_position=0)
        self.assertEqual(kernel.execute(foreign).reason_code,ReasonCode.ORG_UNKNOWN)
        self.assertEqual((store.read(state.organization.organization_id),ids.calls,
                          authority.calls,handler.calls),(before,[],0,0))

    def test_activation_conformance_mapping_is_exact_and_executable(self):
        expected={f"LIF-{number:03d}" for number in range(16,33)}
        self.assertEqual(set(ACTIVATE_ROLE_SCENARIO_MAP),expected)
        self.assertEqual(len(ACTIVATE_ROLE_SCENARIO_MAP),17)
        for scenario,test_name in ACTIVATE_ROLE_SCENARIO_MAP.items():
            with self.subTest(scenario=scenario,test_name=test_name):
                self.assertTrue(test_name.startswith("test_"))
                self.assertTrue(hasattr(type(self),test_name))

    def test_reducer_rejects_other_non_draft_state(self):
        state=founded(); reducer=OrganizationRoleReducer(role_seed(state)); projection=reducer.initial_state()
        role=RoleProjection(RoleId("role-suspended"),state.organization.organization_id,"Suspended",
            ("duty",),("capability",),FrozenMap(),"review",("separation",),"suspended",2,
            ActorId("human-founder"),CommandId("created"),None,None,False)
        projection=dataclasses.replace(projection,roles=projection.roles+(role,))
        kernel,store,_,_,_,_=activation_runtime(state=state)
        event=kernel.execute(activation_command()).domain_events[0]
        event=dataclasses.replace(event,payload=FrozenMap({
            "role_id":role.role_id,"prior_lifecycle_state":"draft","lifecycle_state":"active",
            "prior_entity_revision":2,"entity_revision":3,
        }),entity_references=(EntityReference("Role",str(role.role_id),3),))
        with self.assertRaises(ValueError): reducer.apply(projection,event)

    def test_imports_are_side_effect_free(self):
        completed=subprocess.run(
            [sys.executable,"-c","import aios_kernel; import aios_kernel.activate_role"],
            env={**__import__("os").environ,"PYTHONDONTWRITEBYTECODE":"1","PYTHONPATH":"src"},
            cwd=pathlib.Path(__file__).parents[2],capture_output=True,text=True,check=False,
        )
        self.assertEqual((completed.returncode,completed.stdout,completed.stderr),(0,"",""))


if __name__=="__main__": unittest.main()
