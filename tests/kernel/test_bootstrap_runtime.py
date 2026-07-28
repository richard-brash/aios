"""Behavioral tests for the one-time constitutional bootstrap runtime slice."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
import pathlib
import subprocess
import sys
import unittest

from aios_kernel.bootstrap_runtime import (
    BootstrapStructuralRejected, ConstitutionalBootstrapRuntime,
    CommittedGenesisEvidence,
    ConstitutionalEvaluationRejected, FoundedOrganizationState,
    GenesisAppendRejected, GenesisComparison, ReferenceBootstrapConstitutionalEvaluator,
    REFERENCE_GENESIS_EVENT_TYPES, compare_genesis_candidates, genesis_stream_id,
    replay_genesis,
)
from aios_kernel.reference import (
    DeterministicIdentifiers, FixedClock, GenesisFault, InMemoryGenesisStore,
)
from aios_kernel.runtime import KernelRuntime, RuntimeRejected
from aios_protocol.bootstrap import (
    BootstrapAdmissionBasis, BootstrapCommitted, BootstrapEnvelope,
    BootstrapPreviouslyAdmitted, BootstrapRejectedDecision, BootstrapRequest,
    BootstrapUncertain, CompetingGenesisRule, ConstitutionEstablishment,
    ExpectedGenesisStream, FoundingAuthorityGrant, FoundingDecision,
    FoundingEventCoverage, FoundingEventProposal, FoundingEventSet,
    FoundingMission, FoundingRetentionPolicy, FoundingRole,
    FoundingRoleAssignment, GenesisException, GenesisRecordingCommand,
    OrganizationGenesisAttributes, VerifiedHumanReference,
)
from aios_protocol.commands import DutyWorkRoot
from aios_protocol.identifiers import (
    ActorId, AuditRecordId, AuthorityGrantId, CommandId, CorrelationId,
    DecisionId, IntegrityReference, MessageId, MissionId, OrganizationId,
    PolicyId, RoleAssignmentId, RoleId,
)
from aios_protocol.presence import NOT_APPLICABLE
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import (
    PAYLOAD_V1, PROTOCOL_V1, RECORD_V1, SPEC_0_0_2, PayloadVersion,
    ProtocolFamilyVersion, RecordTypeVersion,
)


NOW = datetime(2042, 3, 4, 5, 6, 7, tzinfo=timezone.utc)


def _proposal(key, command_id, human_id, payload):
    return FoundingEventProposal(
        key, REFERENCE_GENESIS_EVENT_TYPES.get(key, f"ReferenceGenesis.{key}"),
        RECORD_V1, PAYLOAD_V1, human_id,
        command_id, "reserved_genesis", FrozenMap(payload),
    )


def bootstrap_request(*, organization="org-bootstrap", message="bootstrap-message",
                      founder="human-founder", idempotency="bootstrap/key"):
    human_id = ActorId(founder)
    organization_id = OrganizationId(organization)
    decision_id = DecisionId(f"decision-{organization}")
    command_id = CommandId(f"command-{organization}")
    duty = DutyWorkRoot(
        "constitutional_establishment", "constitution:genesis", human_id,
        f"establish {organization}", "complete atomic genesis",
    )
    human = VerifiedHumanReference(
        human_id, IntegrityReference(f"identity-{founder}"),
        IntegrityReference(f"verification-{founder}"), "constitutional_owner",
    )
    org = OrganizationGenesisAttributes(
        organization_id, "Bootstrap Organization", MissionId(f"mission-{organization}"),
        (human_id,), "jurisdiction:declared", PolicyId(f"retention-{organization}"),
        PolicyId("constitution-0.0.2"),
    )
    constitution = ConstitutionEstablishment(
        org.constitution_policy_id, "0.0.2", IntegrityReference("constitution-source"),
        (human_id,), decision_id, NOW,
    )
    mission = FoundingMission(
        org.mission_record_id, "Operate under the declared lawful mission", (human_id,), NOW,
        ("annual mission review",), decision_id,
    )
    retention = FoundingRetentionPolicy(
        org.retention_policy_id, "1", "Founding retention Policy", human_id,
        FrozenMap({"audit": "retain"}), "all founding records", "constitutional",
        NOW, "annual review", "higher precedence controls", decision_id,
    )
    role = FoundingRole(
        RoleId(f"role-{organization}"), "Constitutional Governor",
        ("govern the Organization",), ("governance",),
        FrozenMap({"scope": "initial governance"}), "constitutional review",
        ("Human accountable decider",),
    )
    assignment = FoundingRoleAssignment(
        RoleAssignmentId(f"assignment-{organization}"), human_id, role.role_id,
        human_id, NOW, "annual constitutional review", "initial governance",
    )
    decision = FoundingDecision(
        decision_id, "1", "A4.constitutional_genesis", human_id, human_id, human_id,
        duty, "direct constitutional bootstrap",
        (FrozenMap({"course": "establish"}), FrozenMap({"course": "defer"})),
        (IntegrityReference("founding-evidence"),),
        FrozenMap({"scale": "approved", "value": 1}), FrozenMap({"risk": "bounded"}),
        FrozenMap({"benefit": "valid organization"}), FrozenMap({"money": 0}),
        FrozenMap({"class": "human_reserved"}), FrozenMap({"required": False}),
        "selected", FrozenMap({"condition": "annual"}),
        FrozenMap({"status": "pending"}), FrozenMap({"status": "pending"}),
    )
    grant = FoundingAuthorityGrant(
        AuthorityGrantId(f"grant-{organization}"), human_id, human_id,
        "initial lawful governance", "constitutional", ("establish governance",),
        ("ordinary work during genesis",), FrozenMap({"scope": "governance"}),
        FrozenMap({"money": 0}), NOW, "review after genesis",
        FrozenMap({"delegate": False}), FrozenMap({"required": False}),
        FrozenMap({"maximum": "A4"}),
    )
    recording = GenesisRecordingCommand(
        command_id, "RecordConstitutionalGenesis", RECORD_V1, PAYLOAD_V1,
        human_id, CorrelationId(f"correlation-{organization}"), organization_id,
        duty, idempotency, "reserved_genesis",
    )
    audit_id = AuditRecordId(f"audit-{organization}")
    proposals = (
        _proposal("organization", command_id, human_id, {"organization": org}),
        _proposal("human", command_id, human_id, {"verified_human": human}),
        _proposal("constitution", command_id, human_id, {"constitution": constitution}),
        _proposal("mission", command_id, human_id, {"mission": mission}),
        _proposal("jurisdiction", command_id, human_id, {"jurisdiction_scope": org.jurisdiction_scope}),
        _proposal("retention", command_id, human_id, {"retention_policy": retention}),
        _proposal("role", command_id, human_id, {"founding_role": role}),
        _proposal("assignment", command_id, human_id, {"founding_role_assignment": assignment}),
        _proposal("decision", command_id, human_id, {"founding_decision": decision}),
        _proposal("grant", command_id, human_id, {"authority_grant": grant}),
        _proposal("audit", command_id, human_id, {"audit_record_id": audit_id}),
    )
    event_set = FoundingEventSet(
        proposals,
        FoundingEventCoverage(
            "organization", "human", "constitution", "mission", "jurisdiction",
            "retention", "role", "assignment", "decision", ("grant",), "audit",
        ),
    )
    return BootstrapRequest(
        BootstrapEnvelope(
            MessageId(message), "ConstitutionalBootstrap",
            CorrelationId(f"correlation-{organization}"), NOW, "reserved_genesis",
            "establish constitutional Organization", "BootstrapRequest", PAYLOAD_V1,
            idempotency, NOT_APPLICABLE, NOT_APPLICABLE,
        ),
        PROTOCOL_V1, PAYLOAD_V1, SPEC_0_0_2,
        BootstrapAdmissionBasis.CONSTITUTION_DIRECT,
        GenesisException.SOLE_PREEXISTING_AUTHORITY_EXCEPTION,
        org, human, constitution, mission, retention, role, assignment, decision,
        (grant,), recording, event_set, audit_id, IntegrityReference(f"audit-proof-{organization}"),
        ExpectedGenesisStream.NONEXISTENT, genesis_stream_id(organization_id), idempotency,
        CompetingGenesisRule.REJECT_MATERIAL_CONFLICT,
        IntegrityReference(f"request-proof-{organization}"),
    )


class CountingEvaluator(ReferenceBootstrapConstitutionalEvaluator):
    def __init__(self): self.calls = 0
    def evaluate(self, request, evaluation_time):
        self.calls += 1
        return super().evaluate(request, evaluation_time)


class RejectEvaluator:
    def __init__(self): self.calls = 0
    def evaluate(self, request, evaluation_time):
        self.calls += 1
        decision = BootstrapRejectedDecision(
            request, evaluation_time, ReasonCode.AUTH_MISSING, "authority",
            "founding authority denied", request.proposed_audit_integrity_reference,
        )
        return ConstitutionalEvaluationRejected(decision)


def runtime(*, evaluator=None, store=None):
    evaluator = evaluator or CountingEvaluator()
    store = store or InMemoryGenesisStore()
    identifiers = DeterministicIdentifiers(
        [], [], [f"bootstrap-event-{index}" for index in range(1, 100)],
    )
    kernel = ConstitutionalBootstrapRuntime(
        clock=FixedClock(NOW), identifiers=identifiers, evaluator=evaluator, store=store,
    )
    return kernel, store, identifiers, evaluator


def corrupt(record, field_name, value):
    """Test-only simulation of hostile decoded data bypassing constructor validation."""
    clone = dataclasses.replace(record)
    object.__setattr__(clone, field_name, value)
    return clone


def replace_payload_fact(history, field_name, value):
    """Replace one recorded founding fact without consulting the request."""
    changed=[]; found=False
    for event in history:
        proposal=event.payload["proposal_payload"]
        if field_name in proposal:
            proposal=FrozenMap({**dict(proposal),field_name:value})
            payload=FrozenMap({**dict(event.payload),"proposal_payload":proposal})
            event=dataclasses.replace(event,payload=payload)
            found=True
        changed.append(event)
    if not found:
        raise AssertionError(f"missing recorded fact {field_name}")
    return tuple(changed)


def replace_committed_evidence(history, **changes):
    evidence=dataclasses.replace(history[0].payload["committed_genesis_evidence"],**changes)
    return tuple(
        dataclasses.replace(event,payload=FrozenMap({
            **dict(event.payload),"committed_genesis_evidence":evidence,
        }))
        for event in history
    )


class ConstitutionalBootstrapRuntimeTests(unittest.TestCase):
    def test_valid_envelope_reaches_constitutional_evaluation(self):
        kernel, _, _, evaluator = runtime()
        self.assertIsInstance(kernel.execute(bootstrap_request()), BootstrapCommitted)
        self.assertEqual(evaluator.calls, 1)

    def test_malformed_input_rejects_before_evaluation(self):
        kernel, store, _, evaluator = runtime()
        result = kernel.execute(object())
        self.assertIsInstance(result, BootstrapStructuralRejected)
        self.assertEqual(result.reason_code, ReasonCode.INPUT_MALFORMED)
        self.assertEqual(evaluator.calls, 0)
        self.assertEqual(store.read(genesis_stream_id(OrganizationId("org-bootstrap"))), ())

    def test_ordinary_runtime_path_cannot_perform_genesis(self):
        class NeverClock:
            def evaluation_time(self): raise AssertionError("ordinary runtime should reject structure first")
        class ResolverSpy:
            def __init__(self): self.calls=0
            def resolve(self,claim): self.calls+=1; raise AssertionError("resolver must not run")
        resolver=ResolverSpy()
        ordinary = KernelRuntime(
            clock=NeverClock(), identifiers=object(), evaluator=object(), store=object(),
            resolver=resolver, handlers=(),
        )
        result = ordinary.execute(bootstrap_request())
        self.assertIsInstance(result, RuntimeRejected)
        self.assertEqual(result.reason_code, ReasonCode.INPUT_MALFORMED)
        self.assertEqual(resolver.calls,0)

    def test_missing_founding_authority_fails_closed(self):
        request = corrupt(bootstrap_request(), "initial_authority_grants", ())
        result = runtime()[0].execute(request)
        self.assertEqual(result.reason_code, ReasonCode.AUTH_MISSING)

    def test_incomplete_role_assignment_fails_closed(self):
        request = bootstrap_request()
        bad_assignment = corrupt(request.founding_role_assignment, "lifecycle_state", "proposed")
        request = corrupt(request, "founding_role_assignment", bad_assignment)
        self.assertEqual(runtime()[0].execute(request).reason_code, ReasonCode.BOOTSTRAP_INCOMPLETE)

    def test_incomplete_constitutional_duty_fails_closed(self):
        request = bootstrap_request()
        bad_duty = corrupt(request.founding_decision.duty_reference, "scope", "")
        bad_decision = corrupt(request.founding_decision, "duty_reference", bad_duty)
        request = corrupt(request, "founding_decision", bad_decision)
        self.assertEqual(runtime()[0].execute(request).reason_code, ReasonCode.WORK_ROOT_INCOMPLETE)

    def test_missing_required_organization_attribute_fails_closed(self):
        request = bootstrap_request()
        bad_org = corrupt(request.organization, "jurisdiction_scope", "")
        request = corrupt(request, "organization", bad_org)
        self.assertEqual(runtime()[0].execute(request).reason_code, ReasonCode.BOOTSTRAP_INCOMPLETE)

    def test_incomplete_event_coverage_fails_closed(self):
        request = bootstrap_request()
        proposal = request.proposed_founding_events.ordered_events[3]
        bad = corrupt(proposal, "payload", FrozenMap())
        events = corrupt(
            request.proposed_founding_events, "ordered_events",
            request.proposed_founding_events.ordered_events[:3] + (bad,) + request.proposed_founding_events.ordered_events[4:],
        )
        request = corrupt(request, "proposed_founding_events", events)
        self.assertEqual(runtime()[0].execute(request).reason_code, ReasonCode.BOOTSTRAP_INCOMPLETE)

    def test_unreferenced_or_non_genesis_event_payload_fails_closed(self):
        request = bootstrap_request()
        extra = _proposal(
            "ordinary_work", request.recording_command.command_id,
            request.verified_human.actor_id, {"ordinary_task": "forbidden"},
        )
        events = corrupt(
            request.proposed_founding_events, "ordered_events",
            request.proposed_founding_events.ordered_events + (extra,),
        )
        request = corrupt(request, "proposed_founding_events", events)
        result = runtime()[0].execute(request)
        self.assertEqual(result.reason_code, ReasonCode.BOOTSTRAP_INCOMPLETE)

    def test_complete_proposal_is_accepted_before_recording(self):
        evaluator = ReferenceBootstrapConstitutionalEvaluator()
        evaluated = evaluator.evaluate(bootstrap_request(), NOW)
        self.assertEqual(evaluated.proposal.request, bootstrap_request())
        self.assertEqual(evaluated.decision.proposal, evaluated.proposal)

    def test_competing_comparison_is_deterministic_and_symmetric(self):
        first = bootstrap_request()
        other = bootstrap_request(founder="human-other", message="other-message")
        for _ in range(5):
            self.assertIs(compare_genesis_candidates(first, other), GenesisComparison.COMPETING)
            self.assertIs(compare_genesis_candidates(other, first), GenesisComparison.COMPETING)
            self.assertIs(compare_genesis_candidates(first, first), GenesisComparison.EXACT)

    def test_approved_genesis_records_exactly_one_command_identity(self):
        kernel, store, _, _ = runtime(); request = bootstrap_request()
        result = kernel.execute(request); events = store.read(request.genesis_stream_id)
        self.assertIsInstance(result, BootstrapCommitted)
        self.assertEqual({event.envelope.recording_command_id for event in events},
                         {request.recording_command.command_id})

    def test_rejected_proposal_is_never_recorded(self):
        kernel, store, identifiers, evaluator = runtime(evaluator=RejectEvaluator())
        request = bootstrap_request(); result = kernel.execute(request)
        self.assertIsInstance(result, BootstrapRejectedDecision)
        self.assertEqual((evaluator.calls, identifiers.calls), (1, []))
        self.assertEqual(store.read(request.genesis_stream_id), ())

    def test_unavailable_constitutional_evaluator_fails_closed(self):
        class UnavailableEvaluator:
            def evaluate(self, request, evaluation_time):
                raise RuntimeError("unavailable")
        kernel, store, identifiers, _ = runtime(evaluator=UnavailableEvaluator())
        request = bootstrap_request(); result = kernel.execute(request)
        self.assertEqual(result.reason_code, ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE)
        self.assertEqual(identifiers.calls, [])
        self.assertEqual(store.read(request.genesis_stream_id), ())

    def test_complete_event_set_appends_atomically_in_order(self):
        kernel, store, _, _ = runtime(); request = bootstrap_request()
        result = kernel.execute(request); events = store.read(request.genesis_stream_id)
        self.assertEqual(len(events), len(request.proposed_founding_events.ordered_events))
        self.assertEqual(tuple(event.event_type for event in events),
                         tuple(event.event_type for event in request.proposed_founding_events.ordered_events))
        self.assertEqual(tuple(event.envelope.stream_position for event in events), tuple(range(1, 12)))
        self.assertEqual(len(result.founding_events), 11)
        evidence={event.payload["committed_genesis_evidence"] for event in events}
        self.assertEqual(len(evidence),1)
        committed_evidence=next(iter(evidence))
        self.assertIsInstance(committed_evidence,CommittedGenesisEvidence)
        self.assertEqual(committed_evidence.recording_command,request.recording_command)
        self.assertEqual(committed_evidence.coverage,request.proposed_founding_events.coverage)

    def test_append_failure_and_builder_failure_leave_stream_empty(self):
        for fault in (GenesisFault.FAIL_BEFORE_COMMIT, GenesisFault.BUILDER_FAILURE):
            with self.subTest(fault=fault):
                store = InMemoryGenesisStore(fault=fault); kernel, _, identifiers, _ = runtime(store=store)
                request = bootstrap_request(); result = kernel.execute(request)
                self.assertEqual(result.reason_code, ReasonCode.APPEND_FAILED)
                self.assertEqual(store.read(request.genesis_stream_id), ())
                self.assertEqual(identifiers.calls,[])

    def _assert_store_rejects_tampered_batch(self,tamper):
        request=bootstrap_request(); donor,donor_store,_,_=runtime()
        committed=donor.execute(request); events=donor_store.read(request.genesis_stream_id)
        store=InMemoryGenesisStore()
        result=store.append_genesis(
            request=request,evaluation_time=NOW,accepted_decision=committed.decision,
            expected_prior_position=0,build_transaction=lambda:(tamper(events),committed),
        )
        self.assertIsInstance(result,GenesisAppendRejected)
        self.assertEqual(result.reason_code,ReasonCode.INTEGRITY_VERIFICATION_FAILED)
        self.assertEqual(store.read(request.genesis_stream_id),())

    def test_atomic_store_rejects_incorrect_event_order(self):
        self._assert_store_rejects_tampered_batch(
            lambda events:(events[1],events[0],*events[2:]))

    def test_atomic_store_rejects_duplicate_event_identity(self):
        self._assert_store_rejects_tampered_batch(
            lambda events:(events[0],dataclasses.replace(events[1],event_id=events[0].event_id),*events[2:]))

    def test_atomic_store_rejects_invalid_audit_linkage(self):
        self._assert_store_rejects_tampered_batch(
            lambda events:(dataclasses.replace(events[0],audit_record_id=AuditRecordId("audit-substituted")),*events[1:]))

    def test_atomic_store_requires_replay_parity_before_publication(self):
        request=bootstrap_request()
        bad_human=corrupt(request.verified_human,"identity_kind","model")
        self._assert_store_rejects_tampered_batch(
            lambda events:replace_payload_fact(events,"verified_human",bad_human))

    def test_expected_version_and_competing_recording_prevent_double_genesis(self):
        kernel, store, _, _ = runtime(); first = bootstrap_request()
        self.assertIsInstance(kernel.execute(first), BootstrapCommitted)
        competing = bootstrap_request(founder="human-other", message="other-message")
        result = kernel.execute(competing)
        self.assertEqual(result.reason_code, ReasonCode.BOOTSTRAP_COMPETING_GENESIS)
        self.assertEqual(len(store.read(first.genesis_stream_id)), 11)
        self.assertTrue(kernel.execute(first).original_committed.genesis_exception_exhausted)

    def test_stale_nonempty_stream_without_registration_fails_closed(self):
        donor_kernel, donor_store, _, _ = runtime(); request = bootstrap_request()
        donor_kernel.execute(request)
        history = donor_store.read(request.genesis_stream_id)
        stale_store = InMemoryGenesisStore(initial_streams=((request.genesis_stream_id, history),))
        kernel, _, identifiers, _ = runtime(store=stale_store)
        result = kernel.execute(request)
        self.assertEqual(result.reason_code, ReasonCode.STREAM_CONCURRENCY_CONFLICT)
        self.assertEqual(identifiers.calls, [])
        self.assertEqual(stale_store.read(request.genesis_stream_id), history)

    def test_exact_redelivery_returns_original_without_new_events_or_ids(self):
        kernel, store, identifiers, _ = runtime(); request = bootstrap_request()
        committed = kernel.execute(request); calls = tuple(identifiers.calls)
        history = store.read(request.genesis_stream_id)
        repeated = kernel.execute(request)
        self.assertIsInstance(repeated, BootstrapPreviouslyAdmitted)
        self.assertEqual(repeated.original_committed, committed)
        self.assertEqual(tuple(identifiers.calls), calls)
        self.assertEqual(store.read(request.genesis_stream_id), history)

    def test_distinct_request_is_not_redelivery(self):
        kernel, store, _, _ = runtime(); first = bootstrap_request(); kernel.execute(first)
        result = kernel.execute(bootstrap_request(message="different-message"))
        self.assertIsInstance(result, BootstrapRejectedDecision)
        self.assertEqual(result.reason_code, ReasonCode.BOOTSTRAP_COMPETING_GENESIS)

    def test_uncertainty_quarantines_without_founding_events(self):
        store = InMemoryGenesisStore(fault=GenesisFault.UNCERTAIN_BEFORE_COMMIT)
        kernel, _, identifiers, _ = runtime(store=store); request = bootstrap_request()
        result = kernel.execute(request)
        self.assertIsInstance(result, BootstrapUncertain)
        self.assertTrue(result.retry_prohibited)
        self.assertEqual(store.read(request.genesis_stream_id), ())
        self.assertEqual(identifiers.calls, [])
        repeated = kernel.execute(request)
        self.assertIsInstance(repeated, BootstrapUncertain)
        self.assertEqual(store.read(request.genesis_stream_id), ())

    def test_replay_reconstructs_all_founding_facts_stably_without_dependencies(self):
        kernel, store, identifiers, evaluator = runtime(); request = bootstrap_request()
        kernel.execute(request); history = store.read(request.genesis_stream_id)
        calls = (tuple(identifiers.calls), evaluator.calls)
        first = replay_genesis(history); second = replay_genesis(history)
        self.assertEqual(first, second); self.assertIsInstance(first, FoundedOrganizationState)
        self.assertEqual(first.organization, request.organization)
        self.assertEqual(first.constitution, request.constitution)
        self.assertEqual(first.mission, request.mission)
        self.assertEqual(first.jurisdiction_scope, request.organization.jurisdiction_scope)
        self.assertEqual(first.retention_policy, request.retention_policy)
        self.assertEqual(first.founding_role_assignment, request.founding_role_assignment)
        self.assertEqual(first.founding_decision.duty_reference, request.founding_decision.duty_reference)
        self.assertEqual((tuple(identifiers.calls), evaluator.calls), calls)

    def test_replay_rejects_impossible_second_or_reordered_genesis(self):
        kernel, store, _, _ = runtime(); request = bootstrap_request(); kernel.execute(request)
        history = store.read(request.genesis_stream_id)
        with self.assertRaises(ValueError): replay_genesis(history + history)
        with self.assertRaises(ValueError): replay_genesis(tuple(reversed(history)))

    def test_unsupported_protocol_version_fails_closed_without_events(self):
        request = dataclasses.replace(bootstrap_request(), protocol_family_version=ProtocolFamilyVersion("99.0"))
        kernel, store, _, _ = runtime(); result = kernel.execute(request)
        self.assertEqual(result.reason_code, ReasonCode.VER_UNSUPPORTED)
        self.assertEqual(store.read(request.genesis_stream_id), ())

    def test_unsupported_bootstrap_schema_version_fails_closed(self):
        request = bootstrap_request()
        envelope = dataclasses.replace(request.envelope, schema_version=RECORD_V1.__class__("99.0"))
        request = dataclasses.replace(request, envelope=envelope)
        result = runtime()[0].execute(request)
        self.assertEqual(result.reason_code, ReasonCode.VER_UNSUPPORTED)

    def test_replay_rejects_unsupported_historical_event_version(self):
        kernel, store, _, _ = runtime(); request = bootstrap_request(); kernel.execute(request)
        history = store.read(request.genesis_stream_id)
        bad = dataclasses.replace(history[0], event_version=RECORD_V1.__class__("99.0"))
        with self.assertRaises(ValueError):
            replay_genesis((bad,) + history[1:])

    def _history(self):
        kernel,store,identifiers,evaluator=runtime(); request=bootstrap_request()
        committed=kernel.execute(request)
        return tuple(store.read(request.genesis_stream_id)),request,committed,store,identifiers,evaluator

    def assert_replay_rejects(self, history):
        with self.assertRaises(ValueError): replay_genesis(tuple(history))

    def test_history_only_replay_discards_request_decision_registration_and_runtime(self):
        history,request,committed,store,identifiers,evaluator=self._history()
        copied=tuple(dataclasses.replace(event) for event in history)
        expected=(request.organization,request.verified_human,request.founding_role)
        del request,committed,store,identifiers,evaluator
        state=replay_genesis(copied)
        self.assertEqual((state.organization,state.verified_human,state.founding_role),expected)
        self.assertEqual(replay_genesis(copied),state)

    def test_replay_mutation_founding_human_identity_fails(self):
        history,request,*_=self._history()
        human=corrupt(request.verified_human,"actor_id",ActorId("human-substituted"))
        self.assert_replay_rejects(replace_payload_fact(history,"verified_human",human))

    def test_replay_mutation_founding_human_kind_fails(self):
        history,request,*_=self._history()
        human=corrupt(request.verified_human,"identity_kind","model")
        self.assert_replay_rejects(replace_payload_fact(history,"verified_human",human))

    def test_replay_mutation_organization_identity_fails(self):
        history,request,*_=self._history()
        organization=corrupt(request.organization,"organization_id",OrganizationId("org-other"))
        self.assert_replay_rejects(replace_payload_fact(history,"organization",organization))

    def test_replay_mutation_constitution_version_or_source_fails(self):
        history,request,*_=self._history()
        constitution=corrupt(request.constitution,"constitutional_version","0.0.3")
        self.assert_replay_rejects(replace_payload_fact(history,"constitution",constitution))
        evidence=history[0].payload["committed_genesis_evidence"]
        self.assert_replay_rejects(replace_committed_evidence(
            history,constitutional_basis_reference=IntegrityReference("constitution-other")))

    def test_replay_mutation_mission_identity_or_content_fails(self):
        history,request,*_=self._history()
        mission=corrupt(request.mission,"statement","Altered mission content")
        self.assert_replay_rejects(replace_payload_fact(history,"mission",mission))

    def test_replay_mutation_jurisdiction_fails(self):
        history,*_=self._history()
        self.assert_replay_rejects(replace_payload_fact(history,"jurisdiction_scope","other"))

    def test_replay_mutation_retention_policy_fails(self):
        history,request,*_=self._history()
        policy=corrupt(request.retention_policy,"rule_set",FrozenMap({"audit":"discard"}))
        self.assert_replay_rejects(replace_payload_fact(history,"retention_policy",policy))

    def test_replay_mutation_founding_role_fails(self):
        history,request,*_=self._history()
        role=corrupt(request.founding_role,"duties",("altered duty",))
        self.assert_replay_rejects(replace_payload_fact(history,"founding_role",role))

    def test_replay_mutation_role_assignment_relationship_or_lifecycle_fails(self):
        history,request,*_=self._history()
        assignment=corrupt(request.founding_role_assignment,"actor_id",ActorId("human-other"))
        self.assert_replay_rejects(replace_payload_fact(history,"founding_role_assignment",assignment))
        assignment=corrupt(request.founding_role_assignment,"lifecycle_state","draft")
        self.assert_replay_rejects(replace_payload_fact(history,"founding_role_assignment",assignment))

    def test_replay_mutation_founding_decision_decider_or_duty_fails(self):
        history,request,*_=self._history()
        decision=corrupt(request.founding_decision,"accountable_decider_actor_id",ActorId("human-other"))
        self.assert_replay_rejects(replace_payload_fact(history,"founding_decision",decision))
        duty=corrupt(request.founding_decision.duty_reference,"scope","altered")
        decision=corrupt(request.founding_decision,"duty_reference",duty)
        self.assert_replay_rejects(replace_payload_fact(history,"founding_decision",decision))

    def test_replay_mutation_initial_grant_fails(self):
        history,request,*_=self._history()
        grant=corrupt(request.initial_authority_grants[0],"recipient_actor_id",ActorId("human-other"))
        self.assert_replay_rejects(replace_payload_fact(history,"authority_grant",grant))

    def test_replay_mutation_recording_command_fails(self):
        history,*_=self._history()
        evidence=history[0].payload["committed_genesis_evidence"]
        command=corrupt(evidence.recording_command,"command_id",CommandId("command-other"))
        self.assert_replay_rejects(replace_committed_evidence(history,recording_command=command))

    def test_replay_mutation_audit_linkage_fails(self):
        history,*_=self._history()
        bad=dataclasses.replace(history[3],audit_record_id=AuditRecordId("audit-other"))
        self.assert_replay_rejects((*history[:3],bad,*history[4:]))

    def test_replay_mutation_semantic_coverage_fails(self):
        history,*_=self._history()
        evidence=history[0].payload["committed_genesis_evidence"]
        coverage=corrupt(evidence.coverage,"organization",evidence.coverage.human_actor)
        self.assert_replay_rejects(replace_committed_evidence(history,coverage=coverage))

    def test_replay_mutation_event_organization_or_position_fails(self):
        history,*_=self._history()
        envelope=dataclasses.replace(history[2].envelope,organization_id=OrganizationId("org-other"))
        self.assert_replay_rejects((*history[:2],dataclasses.replace(history[2],envelope=envelope),*history[3:]))
        envelope=dataclasses.replace(history[2].envelope,stream_position=4)
        self.assert_replay_rejects((*history[:2],dataclasses.replace(history[2],envelope=envelope),*history[3:]))

    def test_replay_mutation_duplicate_event_identity_fails(self):
        history,*_=self._history()
        duplicate=dataclasses.replace(history[1],event_id=history[0].event_id)
        self.assert_replay_rejects((history[0],duplicate,*history[2:]))

    def test_replay_mutation_declared_or_event_version_fails(self):
        history,*_=self._history()
        bad=dataclasses.replace(history[0],event_version=RecordTypeVersion("99.0"))
        self.assert_replay_rejects((bad,*history[1:]))
        evidence=history[0].payload["committed_genesis_evidence"]
        declaration=dataclasses.replace(evidence.event_declarations[0],payload_version=PayloadVersion("99.0"))
        self.assert_replay_rejects(replace_committed_evidence(
            history,event_declarations=(declaration,*evidence.event_declarations[1:])))

    def test_replay_mutation_terminal_completion_fails(self):
        history,*_=self._history()
        payload=FrozenMap({**dict(history[-1].payload),"genesis_exception_exhausted":False})
        self.assert_replay_rejects((*history[:-1],dataclasses.replace(history[-1],payload=payload)))
        payload=FrozenMap({**dict(history[0].payload),"genesis_exception_exhausted":True})
        self.assert_replay_rejects((dataclasses.replace(history[0],payload=payload),*history[1:]))

    def test_replay_mutation_ordinary_event_or_multiple_completion_fails(self):
        history,*_=self._history()
        bad=dataclasses.replace(history[4],event_type="TaskCreated")
        self.assert_replay_rejects((*history[:4],bad,*history[5:]))

    def test_replay_has_no_effect_dependencies(self):
        history,_,_,store,identifiers,evaluator=self._history()
        before=(tuple(identifiers.calls),evaluator.calls,dict(store._streams),dict(store._registrations),store.builder_calls)
        replay_genesis(history); replay_genesis(history)
        after=(tuple(identifiers.calls),evaluator.calls,dict(store._streams),dict(store._registrations),store.builder_calls)
        self.assertEqual(after,before)

    def test_imports_are_side_effect_free_and_sources_have_no_ambient_nondeterminism(self):
        root = pathlib.Path(__file__).parents[2]
        completed = subprocess.run(
            [sys.executable, "-c", "import aios_kernel.bootstrap_runtime; import aios_kernel.reference.bootstrap_store"],
            cwd=root, env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"},
            capture_output=True, text=True, check=False,
        )
        self.assertEqual((completed.returncode, completed.stdout, completed.stderr), (0, "", ""))
        source = (root / "src/aios_kernel/bootstrap_runtime.py").read_text()
        for token in ("datetime.now(", "datetime.utcnow(", "time.time(", "random.", "uuid.", "os.environ", "getenv("):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
