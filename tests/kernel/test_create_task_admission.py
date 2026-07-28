"""CreateTask executes only through the authenticated ordinary KernelRuntime."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
import pathlib
import unittest

import aios_kernel
from aios_kernel.create_task import CreateTaskCommand, CreateTaskHandler, InitialTaskState
from aios_kernel.reference import (
    DeterministicIdentifiers, DeterministicRecordingBoundaryResolver, FixedClock,
    InMemoryRuntimeEventStore,
)
from aios_kernel.runtime import (
    KernelRuntime, ProcessingAllowed, ProcessingDenied, RuntimeAccepted,
    RuntimeRejected,
)
from aios_protocol.admission import AdmissionEstablished
from aios_protocol.commands import CommandSubmission, EntityReference, GoalWorkRoot, RiskClass
from aios_protocol.envelope import CallerEnvelope
from aios_protocol.identifiers import *
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import PayloadVersion, RecordTypeVersion
from conformance_map import SCENARIO_MAP

NOW=datetime(2040,2,3,4,5,6,tzinfo=timezone.utc)
V=RecordTypeVersion("1.0")
ORG=OrganizationId("org-task")
ACTOR=ActorId("actor-task")


def command(*, proof="proof-task", command_id="command-task", idempotency="idem-task",
            expected_position=0, initial_state=InitialTaskState.PROPOSED, title="Draft plan"):
    envelope=CallerEnvelope(
        MessageId(f"message-{command_id}"),"CommandSubmission",ORG,ACTOR,
        CorrelationId("correlation-task"),NOW,"internal","create task","CreateTask",
        PayloadVersion("1.0"),FrozenMap({"task_id":"task-1"}),
    )
    submission=CommandSubmission(
        envelope,CommandId(command_id),OperationId(f"operation-{command_id}"),
        "CreateTask",V,(EntityReference("Task","task-1",0),),idempotency,
        GoalWorkRoot(GoalId("goal-1")),True,IntegrityReference(proof),
        decision_reference=DecisionId("decision-1"),risk=RiskClass.REVERSIBLE,
        result_criteria=FrozenMap({"state":"proposed"}),stop_conditions=FrozenMap(),
    )
    return CreateTaskCommand(
        submission=submission,expected_stream_position=expected_position,
        proposed_task_id="task-1",title=title,purpose="Produce reviewable proposal",
        initial_state=initial_state,
    )


def admission_for(cmd, *, evidence="authentication-task"):
    submission=cmd.submission
    return AdmissionEstablished(
        submission.envelope.message_id,submission.command_id,ORG,ACTOR,
        IntegrityReference("genesis-task"),IntegrityReference("identity-task"),
        submission.invocation_proof_reference,(IntegrityReference(evidence),),
        IntegrityReference("resolver-task"),V,
    )


class Allow:
    def __init__(self): self.calls=0
    def evaluate(self, context):
        self.calls+=1
        return ProcessingAllowed(FrozenMap({"authority":"CreateTask"}))


class Deny:
    def __init__(self): self.calls=0
    def evaluate(self, context):
        self.calls+=1
        return ProcessingDenied(ReasonCode.AUTH_MISSING,"authority","authority is missing")


def engine(*, cmd=None, evaluator=None, resolver=None, store=None, handler=None):
    cmd=cmd or command()
    evaluator=evaluator or Allow()
    resolver=resolver or DeterministicRecordingBoundaryResolver((admission_for(cmd),))
    store=store or InMemoryRuntimeEventStore()
    ids=DeterministicIdentifiers(
        [f"disposition-{n}" for n in range(10)],
        [f"audit-{n}" for n in range(10)],
        [f"event-{n}" for n in range(60)],
    )
    handler=handler or CreateTaskHandler()
    runtime=KernelRuntime(
        clock=FixedClock(NOW),identifiers=ids,evaluator=evaluator,store=store,
        resolver=resolver,handlers=(handler,),
    )
    return runtime,store,ids,evaluator,resolver,handler,cmd


class CreateTaskKernelRuntimeTests(unittest.TestCase):
    def test_legacy_admission_is_not_public_or_importable(self):
        self.assertFalse(hasattr(aios_kernel,"CreateTaskAdmission"))
        with self.assertRaises(ModuleNotFoundError):
            __import__("aios_kernel.admission")

    def test_acceptance_uses_canonical_runtime_sequence(self):
        runtime,store,_,evaluator,_,_,cmd=engine()
        result=runtime.execute(cmd)
        self.assertIsInstance(result,RuntimeAccepted)
        self.assertEqual(evaluator.calls,1)
        self.assertEqual(tuple(e.event_type for e in result.recorded_events),(
            "CommandAccepted","TaskCreated","DecisionLinked","WorkRootLinked","AuditLinked"))
        self.assertEqual(store.read(ORG),result.recorded_events)
        task=result.domain_events[0]
        self.assertEqual((task.payload["task_id"],task.payload["lifecycle_state"],task.payload["entity_version"]),
                         ("task-1","proposed",1))

    def test_acceptance_persists_validated_admission_evidence(self):
        runtime,_,_,_,_,_,cmd=engine()
        result=runtime.execute(cmd)
        evidence=result.audit_record.admission_evidence
        self.assertEqual((evidence.organization_id,evidence.initiating_actor_id),(ORG,ACTOR))
        self.assertEqual(evidence.invocation_proof_reference,IntegrityReference("proof-task"))
        self.assertEqual(evidence.authentication_evidence_references,
                         (IntegrityReference("authentication-task"),))
        self.assertEqual(result.recorded_events[-1].payload["admission_evidence"],evidence)

    def test_forged_proof_is_effect_free_before_boundary(self):
        class SpyHandler(CreateTaskHandler):
            def __init__(self): self.calls=0
            def handle(self, context):
                self.calls+=1
                return super().handle(context)
        valid=command(); forged=command(proof="forged-proof")
        resolver=DeterministicRecordingBoundaryResolver((admission_for(valid),))
        handler=SpyHandler()
        runtime,store,ids,evaluator,_,_,_=engine(
            cmd=forged,resolver=resolver,handler=handler)
        result=runtime.execute(forged)
        self.assertIsInstance(result,RuntimeRejected)
        self.assertEqual(result.reason_code,ReasonCode.IDENTITY_FORGED)
        self.assertEqual((store.read_calls,store.idempotency_calls,store.append_calls),(0,0,0))
        self.assertEqual((evaluator.calls,handler.calls,len(ids.calls)),(0,0,0))
        self.assertIsNone(result.audit_record); self.assertEqual(result.recorded_events,())

    def test_inconsistent_admission_fails_before_organization_effects(self):
        cmd=command()
        inconsistent=dataclasses.replace(admission_for(cmd),organization_id=OrganizationId("org-other"))
        resolver=DeterministicRecordingBoundaryResolver((inconsistent,))
        runtime,store,ids,evaluator,_,_,_=engine(cmd=cmd,resolver=resolver)
        result=runtime.execute(cmd)
        self.assertEqual(result.reason_code,ReasonCode.ORG_UNKNOWN)
        self.assertEqual((store.read_calls,store.idempotency_calls,store.append_calls,len(ids.calls),evaluator.calls),(0,0,0,0,0))

    def test_governance_rejection_uses_canonical_audit_sequence_and_evidence(self):
        runtime,store,_,evaluator,_,_,cmd=engine(evaluator=Deny())
        result=runtime.execute(cmd)
        self.assertEqual(result.reason_code,ReasonCode.AUTH_MISSING)
        self.assertEqual(tuple(e.event_type for e in result.recorded_events),("CommandRejected","AuditLinked"))
        self.assertEqual(result.audit_record.admission_evidence,
                         result.recorded_events[-1].payload["admission_evidence"])
        self.assertEqual(result.domain_events,()); self.assertEqual(evaluator.calls,1)
        self.assertEqual(store.read(ORG),result.recorded_events)

    def test_handler_rejection_uses_canonical_audit_sequence_and_evidence(self):
        cmd=command(initial_state=InitialTaskState.ACTIVE)
        runtime,_,_,_,_,_,_=engine(cmd=cmd)
        result=runtime.execute(cmd)
        self.assertEqual(result.reason_code,ReasonCode.LIFECYCLE_INVALID_TRANSITION)
        self.assertEqual(tuple(e.event_type for e in result.recorded_events),("CommandRejected","AuditLinked"))
        self.assertIsNotNone(result.audit_record.admission_evidence)

    def test_exact_redelivery_returns_original_without_new_effects(self):
        runtime,store,ids,evaluator,_,_,cmd=engine()
        original=runtime.execute(cmd)
        before=(store.append_calls,store.builder_calls,len(ids.calls),evaluator.calls,store.read(ORG))
        duplicate=runtime.execute(cmd)
        after=(store.append_calls,store.builder_calls,len(ids.calls),evaluator.calls,store.read(ORG))
        self.assertIs(duplicate,original)
        self.assertEqual(before,after)
        self.assertEqual(duplicate.audit_record.admission_evidence,original.audit_record.admission_evidence)

    def test_changed_invocation_proof_conflicts_without_replacing_original(self):
        original=command(); changed=command(proof="proof-task-2")
        resolver=DeterministicRecordingBoundaryResolver((
            admission_for(original,evidence="evidence-original"),
            admission_for(changed,evidence="evidence-changed"),
        ))
        store=InMemoryRuntimeEventStore()
        first,*_=engine(cmd=original,resolver=resolver,store=store)
        accepted=first.execute(original); history=store.read(ORG)
        contender,*_=engine(cmd=changed,resolver=resolver,store=store)
        rejected=contender.execute(changed)
        self.assertEqual(rejected.reason_code,ReasonCode.IDEMPOTENCY_CONFLICT)
        self.assertEqual(store.read(ORG),history)
        self.assertEqual(accepted.audit_record.admission_evidence.authentication_evidence_references,
                         (IntegrityReference("evidence-original"),))

    def test_duplicate_task_identity_rejects_without_domain_event(self):
        runtime,_,_,_,_,_,cmd=engine(); runtime.execute(cmd)
        second=command(command_id="command-task-2",idempotency="idem-task-2",expected_position=5)
        result=runtime.execute(second)
        self.assertEqual(result.reason_code,ReasonCode.LIFECYCLE_INVALID_TRANSITION)
        self.assertEqual(result.domain_events,())


class CreateTaskConformanceMigrationTests(unittest.TestCase):
    """Retain the original 80-scenario catalog mapping through the sole runtime."""

    def scenario(self, number):
        code=SCENARIO_MAP[number]
        specification=(pathlib.Path(__file__).parents[2]/"docs"/"specifications"/
                       "KERNEL_CONFORMANCE.md").read_text()
        self.assertIn(code,specification)

        if code in {"CMD-003"}:
            cmd=command()
            cmd=dataclasses.replace(cmd,submission=dataclasses.replace(
                cmd.submission,operation_version=RecordTypeVersion("2.0")))
            runtime,store,ids,evaluator,resolver,_,_=engine(cmd=cmd)
            result=runtime.execute(cmd)
            self.assertEqual(result.reason_code,ReasonCode.VER_UNSUPPORTED)
            self.assertEqual((resolver.calls,store.read_calls,store.append_calls,evaluator.calls,len(ids.calls)),([],0,0,0,0))
            return
        if code in {"CMD-004"}:
            valid=command(); forged=command(proof="forged-proof")
            resolver=DeterministicRecordingBoundaryResolver((admission_for(valid),))
            runtime,store,ids,evaluator,_,_,_=engine(cmd=forged,resolver=resolver)
            result=runtime.execute(forged)
            self.assertEqual(result.reason_code,ReasonCode.IDENTITY_FORGED)
            self.assertEqual((store.read_calls,store.append_calls,evaluator.calls,len(ids.calls)),(0,0,0,0))
            return
        if code.startswith(("AUT-","APR-","RES-","ADV-")) or code in {"AUD-009"}:
            runtime,store,_,_,_,_,cmd=engine(evaluator=Deny())
            result=runtime.execute(cmd)
            self.assertIsInstance(result,RuntimeRejected)
            self.assertEqual(tuple(e.event_type for e in store.read(ORG)),("CommandRejected","AuditLinked"))
            self.assertEqual(result.domain_events,())
            return
        if code in {"LIF-002"}:
            cmd=command(initial_state=InitialTaskState.ACTIVE)
            runtime,_,_,_,_,_,_=engine(cmd=cmd)
            self.assertEqual(runtime.execute(cmd).reason_code,ReasonCode.LIFECYCLE_INVALID_TRANSITION)
            return

        runtime,store,_,_,_,_,cmd=engine()
        result=runtime.execute(cmd)
        self.assertIsInstance(result,RuntimeAccepted)
        self.assertEqual(tuple(e.event_type for e in result.recorded_events),(
            "CommandAccepted","TaskCreated","DecisionLinked","WorkRootLinked","AuditLinked"))
        self.assertEqual(store.read(ORG),result.recorded_events)


def _make_conformance_test(number):
    def test(self): self.scenario(number)
    test.__name__=f"test_{number:02d}_{SCENARIO_MAP[number].lower().replace('-','_')}"
    return test


for _number in range(1,81):
    setattr(CreateTaskConformanceMigrationTests,
            f"test_{_number:02d}",_make_conformance_test(_number))


if __name__ == "__main__":
    unittest.main()
