"""Focused tests for the capability-neutral deterministic runtime skeleton."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
import pathlib
import subprocess
import sys
import unittest

from aios_kernel.reference import (
    DeterministicIdentifiers, DeterministicRecordingBoundaryResolver,
    FixedClock, InMemoryRuntimeEventStore,
)
from aios_kernel.runtime import (
    DomainEventProposal, HandlerAccepted, HandlerContext, KernelRuntime,
    ProcessingAllowed, ProcessingDenied, RuntimeAccepted, RuntimeCommand,
    RuntimeRejected, replay,
)
from aios_protocol.admission import AdmissionEstablished
from aios_protocol.commands import CommandSubmission, EntityReference, RiskClass
from aios_protocol.envelope import CallerEnvelope
from aios_protocol.identifiers import (
    ActorId, CommandId, CorrelationId, IntegrityReference, MessageId, OperationId,
    OrganizationId,
)
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import PayloadVersion, RecordTypeVersion


NOW=datetime(2040,2,3,4,5,6,tzinfo=timezone.utc)
VERSION=RecordTypeVersion("1.0")
ORG=OrganizationId("org-runtime")


def fixture_command(*, operation_type="FixtureRecord", operation_version=VERSION,
                    expected_position=0, command_id="command-runtime"):
    envelope=CallerEnvelope(MessageId(f"message-{command_id}"),"CommandSubmission",ORG,
        ActorId("actor-runtime"),CorrelationId("correlation-runtime"),NOW,"internal",
        "exercise neutral runtime","FixtureRecord",PayloadVersion("1.0"),
        FrozenMap({"fixture_value":"alpha"}))
    submission=CommandSubmission(envelope,CommandId(command_id),OperationId(f"operation-{command_id}"),
        operation_type,operation_version,(EntityReference("Fixture","fixture-1",expected_position),),
        f"idempotency-{command_id}",None,False,IntegrityReference("proof-runtime"),
        risk=RiskClass.OBSERVE,
        result_criteria=FrozenMap({"recorded":True}),stop_conditions=FrozenMap())
    return RuntimeCommand(submission,expected_position)


class AllowEvaluator:
    def __init__(self): self.calls=0; self.last_context=None
    def evaluate(self, context):
        self.calls+=1; self.last_context=context
        return ProcessingAllowed(FrozenMap({"fixture_governance":"passed"}))


class DenyEvaluator:
    def __init__(self): self.calls=0; self.last_context=None
    def evaluate(self, context):
        self.calls+=1; self.last_context=context
        return ProcessingDenied(ReasonCode.AUTH_MISSING,"authority","fixture lacks authority")


class FixtureHandler:
    operation_type="FixtureRecord"
    operation_version=VERSION
    def __init__(self): self.calls=0
    def validate(self, command): return None
    def handle(self, context: HandlerContext):
        self.calls+=1
        value=context.command.submission.envelope.payload["fixture_value"]
        return HandlerAccepted((DomainEventProposal("FixtureRecorded",VERSION,
            FrozenMap({"value":value}),FrozenMap({"fixture_value":value})),),
            FrozenMap({"fixture_handler":"completed"}))


class FixtureReducer:
    def initial_state(self): return ()
    def apply(self,state,event):
        if event.event_type=="FixtureRecorded": return state+(event.payload["value"],)
        return state


def admission_for(command):
    submission=command.submission
    return AdmissionEstablished(
        submission.envelope.message_id,submission.command_id,
        submission.envelope.organization_id,submission.envelope.initiating_actor_id,
        IntegrityReference("genesis-runtime"),IntegrityReference("identity-runtime"),
        submission.invocation_proof_reference,(IntegrityReference("authentication-runtime"),),
        IntegrityReference("fixture-resolver"),VERSION,
    )


def runtime(*, evaluator=None, handler=None, store=None, command=None, resolver=None):
    ids=DeterministicIdentifiers(["disposition-1","disposition-2"],
        ["audit-1","audit-2"],[f"event-{index}" for index in range(1,20)])
    evaluator=evaluator or AllowEvaluator(); handler=handler or FixtureHandler()
    store=store or InMemoryRuntimeEventStore()
    command=command or fixture_command()
    resolver=resolver or DeterministicRecordingBoundaryResolver((admission_for(command),))
    kernel=KernelRuntime(clock=FixedClock(NOW),identifiers=ids,evaluator=evaluator,
        store=store,resolver=resolver,handlers=(handler,))
    return kernel,store,ids,evaluator,handler


class KernelRuntimeSkeletonTests(unittest.TestCase):
    def test_identical_inputs_and_dependencies_are_deterministic(self):
        first,_,_,_,_=runtime(); second,_,_,_,_=runtime()
        self.assertEqual(first.execute(fixture_command()),second.execute(fixture_command()))

    def test_malformed_input_rejects_before_evaluation_or_handling(self):
        kernel,store,_,evaluator,handler=runtime()
        result=kernel.execute(object())
        self.assertIsInstance(result,RuntimeRejected)
        self.assertEqual(result.reason_code,ReasonCode.INPUT_MALFORMED)
        self.assertEqual((evaluator.calls,handler.calls),(0,0))
        self.assertEqual(store.read(ORG),())

    def test_unknown_operation_fails_closed_before_business_handling(self):
        handler=FixtureHandler(); command=fixture_command(operation_type="UnknownOperation")
        resolver=DeterministicRecordingBoundaryResolver(())
        kernel,store,_,evaluator,_=runtime(handler=handler,command=command,resolver=resolver)
        result=kernel.execute(command)
        self.assertIsInstance(result,RuntimeRejected)
        self.assertEqual(result.reason_code,ReasonCode.VER_UNSUPPORTED)
        self.assertEqual((evaluator.calls,handler.calls),(0,0))
        self.assertEqual(result.domain_events,())
        self.assertEqual(tuple(event.event_type for event in store.read(ORG)),())
        self.assertEqual(resolver.calls,[])

    def test_governance_rejection_emits_no_domain_events(self):
        evaluator=DenyEvaluator(); kernel,store,_,_,handler=runtime(evaluator=evaluator)
        result=kernel.execute(fixture_command())
        self.assertEqual(result.reason_code,ReasonCode.AUTH_MISSING)
        self.assertEqual(result.domain_events,())
        self.assertEqual(handler.calls,0)
        self.assertEqual(tuple(event.event_type for event in store.read(ORG)),("CommandRejected","AuditLinked"))
        self.assertEqual(store.read(ORG)[1].payload["facts"],result.audit_record.facts)

    def test_governance_rejection_uses_the_bound_prior_stream(self):
        store=InMemoryRuntimeEventStore()
        kernel,_,_,_,_=runtime(evaluator=DenyEvaluator(),store=store)
        kernel.execute(fixture_command())
        self.assertEqual(store.read_calls,1)

    def test_accepted_handling_appends_immutable_ordered_events(self):
        kernel,store,_,_,handler=runtime(); result=kernel.execute(fixture_command())
        self.assertIsInstance(result,RuntimeAccepted); self.assertEqual(handler.calls,1)
        self.assertEqual(tuple(event.event_type for event in result.recorded_events),
            ("CommandAccepted","FixtureRecorded","AuditLinked"))
        self.assertEqual(result.domain_events,(result.recorded_events[1],))
        self.assertEqual(store.read(ORG),result.recorded_events)
        self.assertEqual(tuple(event.envelope.stream_position for event in result.recorded_events),(1,2,3))
        self.assertEqual(result.recorded_events[-1].payload["facts"],result.audit_record.facts)
        self.assertEqual(result.recorded_events[-1].payload["admission_evidence"],
                         result.audit_record.admission_evidence)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.recorded_events[1].event_type="Changed"
        with self.assertRaises(TypeError):
            result.recorded_events[1].payload["value"]="changed"

    def test_replay_is_stable_and_does_not_execute_handler(self):
        handler=FixtureHandler(); kernel,store,ids,evaluator,_=runtime(handler=handler)
        kernel.execute(fixture_command()); calls=handler.calls; events=store.read(ORG)
        dependency_calls=(len(ids.calls),evaluator.calls,handler.calls)
        self.assertEqual(replay(events,FixtureReducer()),("alpha",))
        self.assertEqual(replay(events,FixtureReducer()),("alpha",))
        self.assertEqual((len(ids.calls),evaluator.calls,handler.calls),dependency_calls)
        self.assertEqual(handler.calls,calls); self.assertEqual(store.read(ORG),events)

    def test_replay_rejects_reordered_history(self):
        kernel,store,_,_,_=runtime(); kernel.execute(fixture_command())
        with self.assertRaises(ValueError): replay(tuple(reversed(store.read(ORG))),FixtureReducer())

    def test_replay_rejects_duplicate_event_identity(self):
        kernel,store,_,_,_=runtime(); kernel.execute(fixture_command())
        events=store.read(ORG)
        duplicate=dataclasses.replace(events[1],event_id=events[0].event_id)
        with self.assertRaises(ValueError): replay((events[0],duplicate,events[2]),FixtureReducer())

    def test_stale_stream_position_rejects_without_handling_or_append(self):
        kernel,store,_,_,handler=runtime(); kernel.execute(fixture_command())
        prior=store.read(ORG); calls=handler.calls
        result=kernel.execute(fixture_command(command_id="command-stale",expected_position=0))
        self.assertEqual(result.reason_code,ReasonCode.STREAM_CONCURRENCY_CONFLICT)
        self.assertEqual(handler.calls,calls); self.assertEqual(store.read(ORG),prior)
        self.assertEqual(tuple(event.event_id for event in store.read(ORG)),
                         tuple(event.event_id for event in prior))

    def test_append_race_does_not_build_events_or_overwrite_history(self):
        donor,donor_store,_,_,_=runtime(); donor.execute(fixture_command())
        authoritative=donor_store.read(ORG)
        class RaceStore(InMemoryRuntimeEventStore):
            def append_if_current(self,organization_id,expected_prior_position,
                                  scope,fingerprint,build_batch):
                self._streams[organization_id]=authoritative
                return super().append_if_current(
                    organization_id,expected_prior_position,scope,fingerprint,build_batch)
        store=RaceStore(); kernel,_,ids,_,handler=runtime(store=store)
        result=kernel.execute(fixture_command(command_id="command-race"))
        self.assertEqual(result.reason_code,ReasonCode.STREAM_CONCURRENCY_CONFLICT)
        self.assertEqual(ids.calls,[]); self.assertEqual(handler.calls,1)
        self.assertEqual(store.read(ORG),authoritative)

    def test_runtime_source_has_no_ambient_clock_or_randomness(self):
        source=(pathlib.Path(__file__).parents[2]/"src"/"aios_kernel"/"runtime.py").read_text()
        for token in ("datetime.now(","datetime.utcnow(","time.time(","random.","uuid.","os.environ","getenv("):
            self.assertNotIn(token,source)

    def test_reference_store_is_separate_and_imports_are_quiet(self):
        import aios_kernel.reference.runtime_store as fixture_module
        import aios_kernel.runtime as contract_module
        self.assertTrue(fixture_module.__name__.startswith("aios_kernel.reference."))
        self.assertNotIn("aios_kernel.reference",pathlib.Path(contract_module.__file__).read_text())
        completed=subprocess.run(
            [sys.executable,"-c","import aios_kernel; import aios_kernel.runtime; import aios_kernel.reference"],
            env={**__import__("os").environ,"PYTHONDONTWRITEBYTECODE":"1","PYTHONPATH":"src"},
            cwd=pathlib.Path(__file__).parents[2],capture_output=True,text=True,check=False,
        )
        self.assertEqual((completed.returncode,completed.stdout,completed.stderr),(0,"",""))


if __name__=="__main__":
    unittest.main()
