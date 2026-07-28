"""Behavioral coverage for KERNEL_CONFORMANCE ADB-001 through ADB-024."""
from __future__ import annotations

import dataclasses
import unittest

from admission_conformance_map import ADB_RUNTIME_MAP
from test_runtime_skeleton import (
    ORG, VERSION, AllowEvaluator, DenyEvaluator, FixtureHandler, FixtureReducer,
    admission_for, fixture_command, runtime,
)

from aios_kernel.reference import (
    DeterministicRecordingBoundaryResolver, InMemoryRuntimeEventStore,
)
from aios_kernel.runtime import (
    AdmissionEvidenceSnapshot, HandlerRejected, RuntimeAccepted, RuntimeRejected, replay,
)
from aios_protocol.admission import AdmissionEstablished
from aios_protocol.envelope import BootstrapEnvelope, TrafficMode
from aios_protocol.identifiers import ActorId, IntegrityReference, OrganizationId
from aios_protocol.presence import NOT_APPLICABLE
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.versions import PayloadVersion, RecordTypeVersion


class RejectingHandler(FixtureHandler):
    def handle(self,context):
        self.calls+=1
        return HandlerRejected(ReasonCode.LIFECYCLE_INVALID_TRANSITION,"fixture rejected")


def replace_submission(command,**changes):
    return dataclasses.replace(
        command,submission=dataclasses.replace(command.submission,**changes))


class AuthenticatedAdmissionRuntimeTests(unittest.TestCase):
    def assert_persisted_admission(self,result,admission):
        expected=AdmissionEvidenceSnapshot.from_established(admission)
        self.assertEqual(result.audit_record.admission_evidence,expected)
        audit_link=result.recorded_events[-1]
        self.assertEqual(audit_link.event_type,"AuditLinked")
        self.assertEqual(audit_link.payload["admission_evidence"],expected)
        self.assertEqual(expected.organization_id,admission.organization_id)
        self.assertEqual(expected.initiating_actor_id,admission.initiating_actor_id)

    def assert_no_authoritative_effect(self,store,ids,evaluator,handler):
        self.assertEqual(store._streams,{})
        self.assertEqual(store._idempotency,{})
        self.assertEqual(store.append_calls,0)
        self.assertEqual(ids.calls,[])
        self.assertEqual(evaluator.calls,0)
        self.assertEqual(handler.calls,0)

    def denied_runtime(self,command=None,resolver=None):
        command=command or fixture_command()
        resolver=resolver or DeterministicRecordingBoundaryResolver(())
        kernel,store,ids,evaluator,handler=runtime(command=command,resolver=resolver)
        return command,resolver,kernel,store,ids,evaluator,handler

    def test_adb_001_malformed_is_nonrecording(self):
        command,resolver,kernel,store,ids,evaluator,handler=self.denied_runtime()
        result=kernel.execute(object())
        self.assertEqual(result.reason_code,ReasonCode.INPUT_MALFORMED)
        self.assertEqual(resolver.calls,[])
        self.assert_no_authoritative_effect(store,ids,evaluator,handler)

    def test_adb_002_unsupported_support_is_effect_free(self):
        for command in (
            dataclasses.replace(fixture_command(),submission=dataclasses.replace(
                fixture_command().submission,envelope=dataclasses.replace(
                    fixture_command().submission.envelope,
                    schema_version=RecordTypeVersion("2.0")))),
            fixture_command(operation_type="Unsupported"),
            fixture_command(operation_version=RecordTypeVersion("2.0")),
        ):
            with self.subTest(command=command.submission.operation_type):
                command,resolver,kernel,store,ids,evaluator,handler=self.denied_runtime(command)
                result=kernel.execute(command)
                self.assertEqual(result.reason_code,ReasonCode.VER_UNSUPPORTED)
                self.assertEqual(resolver.calls,[])
                self.assertEqual((store.read_calls,store.idempotency_calls),(0,0))
                self.assert_no_authoritative_effect(store,ids,evaluator,handler)

    def test_adb_003_unknown_organization_is_nonrecording(self):
        command,resolver,kernel,store,ids,evaluator,handler=self.denied_runtime()
        result=kernel.execute(command)
        self.assertEqual(result.reason_code,ReasonCode.ORG_UNKNOWN)
        self.assertEqual(len(resolver.calls),1)
        self.assert_no_authoritative_effect(store,ids,evaluator,handler)

    def test_adb_004_identifier_syntax_does_not_create_boundary(self):
        command=fixture_command()
        command,resolver,kernel,store,ids,evaluator,handler=self.denied_runtime(command)
        self.assertIsInstance(command.submission.envelope.organization_id,OrganizationId)
        kernel.execute(command)
        self.assert_no_authoritative_effect(store,ids,evaluator,handler)

    def test_adb_005_unknown_or_forged_actor_is_nonrecording(self):
        known=fixture_command()
        resolver=DeterministicRecordingBoundaryResolver((admission_for(known),))
        unknown=dataclasses.replace(known,submission=dataclasses.replace(
            known.submission,envelope=dataclasses.replace(
                known.submission.envelope,initiating_actor_id=ActorId("actor-unknown"))))
        kernel,store,ids,evaluator,handler=runtime(command=known,resolver=resolver)
        result=kernel.execute(unknown)
        self.assertEqual(result.reason_code,ReasonCode.IDENTITY_UNKNOWN)
        self.assert_no_authoritative_effect(store,ids,evaluator,handler)
        forged=replace_submission(known,invocation_proof_reference=IntegrityReference("proof-forged"))
        result=kernel.execute(forged)
        self.assertEqual(result.reason_code,ReasonCode.IDENTITY_FORGED)
        self.assert_no_authoritative_effect(store,ids,evaluator,handler)

    def test_adb_006_cross_organization_actor_is_nonrecording(self):
        alpha=fixture_command()
        beta=dataclasses.replace(alpha,submission=dataclasses.replace(
            alpha.submission,envelope=dataclasses.replace(
                alpha.submission.envelope,organization_id=OrganizationId("org-beta"))))
        resolver=DeterministicRecordingBoundaryResolver((admission_for(alpha),))
        kernel,store,ids,evaluator,handler=runtime(command=alpha,resolver=resolver)
        result=kernel.execute(beta)
        self.assertEqual(result.reason_code,ReasonCode.ORG_UNKNOWN)
        self.assert_no_authoritative_effect(store,ids,evaluator,handler)

    def test_adb_007_denial_reads_no_stream(self):
        command,_,kernel,store,_,_,_=self.denied_runtime()
        kernel.execute(command)
        self.assertEqual(store.read_calls,0)

    def test_adb_008_denial_appends_no_event_or_audit(self):
        command,_,kernel,store,_,_,_=self.denied_runtime()
        result=kernel.execute(command)
        self.assertEqual((result.recorded_events,result.audit_record),((),None))
        self.assertEqual(store.append_calls,0)

    def test_adb_009_denial_allocates_no_authoritative_ids(self):
        command,_,kernel,_,ids,_,_=self.denied_runtime()
        kernel.execute(command)
        self.assertEqual(ids.calls,[])

    def test_adb_010_denial_invokes_no_governance(self):
        command,_,kernel,_,_,evaluator,_=self.denied_runtime()
        kernel.execute(command)
        self.assertEqual(evaluator.calls,0)

    def test_adb_011_denial_invokes_no_handler(self):
        command,_,kernel,_,_,_,handler=self.denied_runtime()
        kernel.execute(command)
        self.assertEqual(handler.calls,0)

    def test_adb_012_denial_uses_no_idempotency(self):
        command,_,kernel,store,_,_,_=self.denied_runtime()
        kernel.execute(command)
        self.assertEqual((store.idempotency_calls,store._idempotency),(0,{}))

    def test_adb_013_repeated_denial_remains_nonrecording(self):
        command,resolver,kernel,store,ids,evaluator,handler=self.denied_runtime()
        first=kernel.execute(command); second=kernel.execute(command)
        self.assertEqual((first.reason_code,second.reason_code),(ReasonCode.ORG_UNKNOWN,)*2)
        self.assertEqual(len(resolver.calls),2)
        self.assert_no_authoritative_effect(store,ids,evaluator,handler)

    def test_adb_014_exact_canonical_organization_is_bound(self):
        command=fixture_command(); evaluator=AllowEvaluator()
        kernel,store,_,_,_=runtime(command=command,evaluator=evaluator)
        result=kernel.execute(command)
        self.assertIsInstance(result,RuntimeAccepted)
        self.assertEqual(evaluator.last_context.admission.organization_id,ORG)
        self.assertEqual(set(store._streams),{ORG})

    def test_adb_015_exact_canonical_actor_and_proof_are_bound(self):
        command=fixture_command(); evaluator=AllowEvaluator()
        kernel,_,_,_,_=runtime(command=command,evaluator=evaluator)
        kernel.execute(command)
        admission=evaluator.last_context.admission
        self.assertEqual(admission.initiating_actor_id,ActorId("actor-runtime"))
        self.assertEqual(admission.invocation_proof_reference,IntegrityReference("proof-runtime"))
        self.assertEqual(admission.authentication_evidence_references,
                         (IntegrityReference("authentication-runtime"),))

    def test_adb_016_admission_does_not_grant_authority(self):
        command=fixture_command(); evaluator=DenyEvaluator()
        kernel,store,_,_,handler=runtime(command=command,evaluator=evaluator)
        result=kernel.execute(command)
        self.assertEqual(result.reason_code,ReasonCode.AUTH_MISSING)
        self.assertEqual(handler.calls,0)
        self.assertEqual(tuple(event.event_type for event in store._streams[ORG]),
                         ("CommandRejected","AuditLinked"))

    def test_adb_017_governance_denial_is_attributably_recorded(self):
        command=fixture_command(); admission=admission_for(command)
        kernel,store,_,_,_=runtime(command=command,evaluator=DenyEvaluator())
        result=kernel.execute(command)
        self.assertEqual(tuple(event.event_type for event in result.recorded_events),
                         ("CommandRejected","AuditLinked"))
        self.assertTrue(all(event.envelope.organization_id==ORG for event in result.recorded_events))
        self.assertTrue(all(event.envelope.initiating_actor_id==ActorId("actor-runtime")
                            for event in result.recorded_events))
        self.assertEqual(store.append_calls,1)
        self.assert_persisted_admission(result,admission)

    def test_adb_018_handler_denial_is_attributably_recorded(self):
        command=fixture_command(); admission=admission_for(command); handler=RejectingHandler()
        kernel,_,_,evaluator,_=runtime(command=command,handler=handler)
        result=kernel.execute(command)
        self.assertEqual(result.reason_code,ReasonCode.LIFECYCLE_INVALID_TRANSITION)
        self.assertEqual((evaluator.calls,handler.calls),(1,1))
        self.assertEqual(tuple(event.event_type for event in result.recorded_events),
                         ("CommandRejected","AuditLinked"))
        self.assert_persisted_admission(result,admission)

    def test_accepted_audit_persists_validated_admission_evidence(self):
        command=fixture_command(); admission=admission_for(command)
        kernel,_,_,_,_=runtime(command=command)
        result=kernel.execute(command)
        self.assertIsInstance(result,RuntimeAccepted)
        self.assert_persisted_admission(result,admission)
        evidence=result.audit_record.admission_evidence
        self.assertEqual(evidence.organization_genesis_reference,
                         IntegrityReference("genesis-runtime"))
        self.assertEqual(evidence.actor_identity_reference,
                         IntegrityReference("identity-runtime"))
        self.assertEqual(evidence.invocation_proof_reference,
                         IntegrityReference("proof-runtime"))
        self.assertEqual(evidence.authentication_evidence_references,
                         (IntegrityReference("authentication-runtime"),))
        self.assertEqual(evidence.admission_mechanism_reference,
                         IntegrityReference("fixture-resolver"))
        self.assertEqual(evidence.admission_mechanism_version,VERSION)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            evidence.admission_mechanism_reference=IntegrityReference("changed")

    def test_adb_019_recorded_rejection_redelivery_is_exact(self):
        command=fixture_command(); evaluator=DenyEvaluator()
        kernel,store,ids,_,_=runtime(command=command,evaluator=evaluator)
        original=kernel.execute(command); allocations=tuple(ids.calls)
        duplicate=kernel.execute(command)
        self.assertIs(duplicate,original)
        self.assertEqual(tuple(ids.calls),allocations)
        self.assertEqual(store.append_calls,1)
        self.assertEqual(evaluator.calls,1)
        self.assertIs(duplicate.audit_record.admission_evidence,
                      original.audit_record.admission_evidence)

    def test_exact_redelivery_cannot_replace_recorded_admission_evidence(self):
        command=fixture_command()
        original_admission=admission_for(command)
        later_admission=dataclasses.replace(
            original_admission,
            authentication_evidence_references=(IntegrityReference("authentication-later"),),
            admission_mechanism_reference=IntegrityReference("resolver-later"),
        )
        class ChangingResolver:
            def __init__(self): self.calls=0
            def resolve(self,claim):
                self.calls+=1
                return original_admission if self.calls == 1 else later_admission
        resolver=ChangingResolver()
        kernel,store,ids,_,_=runtime(command=command,resolver=resolver)
        original=kernel.execute(command); allocations=tuple(ids.calls)
        duplicate=kernel.execute(command)
        self.assertIs(duplicate,original)
        self.assertEqual(duplicate.audit_record.admission_evidence,
                         AdmissionEvidenceSnapshot.from_established(original_admission))
        self.assertNotEqual(duplicate.audit_record.admission_evidence,
                            AdmissionEvidenceSnapshot.from_established(later_admission))
        self.assertEqual((resolver.calls,store.append_calls),(2,1))
        self.assertEqual(tuple(ids.calls),allocations)

    def test_adb_020_hostile_claim_creates_no_stream(self):
        command,_,kernel,store,_,_,_=self.denied_runtime()
        kernel.execute(command)
        self.assertNotIn(command.submission.envelope.organization_id,store._streams)

    def test_adb_021_unrelated_history_is_unchanged(self):
        valid=fixture_command(); kernel,store,_,_,_=runtime(command=valid)
        kernel.execute(valid); before=store._streams[ORG]
        hostile=dataclasses.replace(valid,submission=dataclasses.replace(
            valid.submission,envelope=dataclasses.replace(
                valid.submission.envelope,organization_id=OrganizationId("org-hostile"))))
        kernel.execute(hostile)
        self.assertEqual(store._streams,{ORG:before})

    def test_adb_022_bootstrap_cannot_enter_ordinary_runtime(self):
        command,resolver,kernel,store,ids,evaluator,handler=self.denied_runtime()
        bootstrap=BootstrapEnvelope(
            command.submission.envelope.message_id,"Bootstrap",
            command.submission.envelope.correlation_id,
            command.submission.envelope.issued_at,"restricted",
            "constitutional genesis","BootstrapRequest",PayloadVersion("1.0"),
            "bootstrap/runtime-isolation",NOT_APPLICABLE,NOT_APPLICABLE)
        result=kernel.execute(bootstrap)
        self.assertEqual(result.reason_code,ReasonCode.INPUT_MALFORMED)
        self.assertEqual(resolver.calls,[])
        self.assert_no_authoritative_effect(store,ids,evaluator,handler)

    def test_adb_023_ordinary_command_cannot_claim_bootstrap_traffic(self):
        command=fixture_command()
        with self.assertRaises(ValueError):
            dataclasses.replace(
                command.submission.envelope,traffic_mode=TrafficMode.PRE_ORGANIZATION)

    def test_adb_024_replay_does_not_resolve_admission(self):
        command=fixture_command(); resolver=DeterministicRecordingBoundaryResolver((admission_for(command),))
        kernel,store,_,_,_=runtime(command=command,resolver=resolver)
        kernel.execute(command); calls=len(resolver.calls)
        self.assertEqual(replay(store._streams[ORG],FixtureReducer()),("alpha",))
        self.assertEqual(len(resolver.calls),calls)

    def test_conformance_mapping_is_complete_unique_and_real(self):
        self.assertEqual(set(ADB_RUNTIME_MAP),{f"ADB-{index:03d}" for index in range(1,25)})
        self.assertEqual(len(set(ADB_RUNTIME_MAP.values())),24)
        methods=set(dir(type(self)))
        self.assertTrue(set(ADB_RUNTIME_MAP.values()) <= methods)

    def test_exact_redelivery_after_stream_advancement_returns_original(self):
        first=fixture_command(); kernel,store,_,_,_=runtime(command=first)
        original=kernel.execute(first)
        second=fixture_command(command_id="command-second",expected_position=3)
        self.assertIsInstance(kernel.execute(second),RuntimeAccepted)
        duplicate=kernel.execute(first)
        self.assertIs(duplicate,original)
        self.assertEqual(len(store._streams[ORG]),6)

    def test_changed_invocation_proof_conflicts_after_admission(self):
        first=fixture_command(); changed=replace_submission(
            first,invocation_proof_reference=IntegrityReference("proof-changed"))
        proofs=(admission_for(first),dataclasses.replace(
            admission_for(first),invocation_proof_reference=IntegrityReference("proof-changed")))
        resolver=DeterministicRecordingBoundaryResolver(proofs)
        kernel,store,_,_,_=runtime(command=first,resolver=resolver)
        original=kernel.execute(first)
        original_evidence=original.audit_record.admission_evidence
        result=kernel.execute(changed)
        self.assertEqual(result.reason_code,ReasonCode.IDEMPOTENCY_CONFLICT)
        self.assertEqual(len(store._streams[ORG]),3)
        self.assertEqual(original.audit_record.admission_evidence,original_evidence)
        self.assertEqual(store._streams[ORG][-1].payload["admission_evidence"],
                         original_evidence)

    def test_malformed_resolver_output_fails_closed(self):
        class MalformedResolver:
            calls=0
            def resolve(self,claim): self.calls+=1; return object()
        command=fixture_command(); resolver=MalformedResolver()
        kernel,store,ids,evaluator,handler=runtime(command=command,resolver=resolver)
        result=kernel.execute(command)
        self.assertEqual(result.reason_code,ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE)
        self.assertIsNone(result.audit_record)
        self.assert_no_authoritative_effect(store,ids,evaluator,handler)

    def test_substituted_admission_proof_fails_before_canonical_read(self):
        command=fixture_command()
        wrong=dataclasses.replace(
            admission_for(command),organization_id=OrganizationId("org-substituted"))
        class SubstitutingResolver:
            def resolve(self,claim): return wrong
        kernel,store,ids,evaluator,handler=runtime(
            command=command,resolver=SubstitutingResolver())
        result=kernel.execute(command)
        self.assertEqual(result.reason_code,ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE)
        self.assertEqual(store.read_calls,0)
        self.assert_no_authoritative_effect(store,ids,evaluator,handler)


if __name__=="__main__":
    unittest.main()
