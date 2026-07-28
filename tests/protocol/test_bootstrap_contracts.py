"""Executable bootstrap contracts mapped to KERNEL_CONFORMANCE BST-001..012."""

from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timezone

from aios_protocol.bootstrap import (
    BootstrapAcceptedDecision, BootstrapAdmissionBasis, BootstrapCommitted,
    BootstrapEnvelope, BootstrapProposal, BootstrapRejectedDecision,
    BootstrapRequest, BootstrapUncertain, CompetingGenesisRule, ConstitutionEstablishment,
    ExpectedGenesisStream, FoundingAuthorityGrant, FoundingDecision,
    FoundingEventCoverage, FoundingEventProposal, FoundingEventSet, FoundingRole,
    FoundingMission, FoundingRetentionPolicy, FoundingRoleAssignment,
    GenesisException, GenesisRecordingCommand,
    OrganizationGenesisAttributes, RecordedFoundingEvent,
    VerifiedHumanReference,
)
from aios_protocol.commands import CommandSubmission, DutyWorkRoot
from aios_protocol.comparison import semantic_equal
from aios_protocol.identifiers import (
    ActorId, AuditRecordId, AuthorityGrantId, CommandId, CorrelationId,
    DecisionId, EventId, IntegrityReference, MessageId, MissionId,
    OrganizationId, PolicyId, RoleAssignmentId, RoleId, StreamId,
)
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.presence import NOT_APPLICABLE
from aios_protocol.validation import FrozenMap, StructuralValidationError
from aios_protocol.versions import (
    PAYLOAD_V1, PROTOCOL_V1, RECORD_V1, SPEC_0_0_2,
    RecordTypeVersion, SupportedVersionRegistry,
)


T = datetime(2030, 1, 1, tzinfo=timezone.utc)


def _event(key: str, command_id: CommandId, human_id: ActorId) -> FoundingEventProposal:
    return FoundingEventProposal(
        key, f"Genesis.{key}", RECORD_V1, PAYLOAD_V1, human_id, command_id,
        "reserved_genesis", FrozenMap({"subject": key}),
    )


def complete_request(*, identity_kind: str = "human") -> BootstrapRequest:
    human_id = ActorId("human-founder")
    organization_id = OrganizationId("org-alpha")
    command_id = CommandId("cmd-genesis-alpha")
    duty = DutyWorkRoot(
        "constitutional_establishment", "constitution:bootstrap", human_id,
        "establish org-alpha and its initial governance", "genesis completes atomically",
    )
    human = VerifiedHumanReference(
        human_id, IntegrityReference("human-identity"), IntegrityReference("human-verification"),
        "constitutional_owner", identity_kind,
    )
    organization = OrganizationGenesisAttributes(
        organization_id, "Alpha Organization", MissionId("mission-alpha"), (human_id,),
        "jurisdiction:alpha", PolicyId("policy-retention-alpha"), PolicyId("constitution-0.0.2"),
    )
    constitution = ConstitutionEstablishment(
        organization.constitution_policy_id, "0.0.2", IntegrityReference("constitution-source"),
        (human_id,), DecisionId("decision-founding"), T,
    )
    mission = FoundingMission(
        organization.mission_record_id, "Advance the declared lawful purpose", (human_id,), T,
        ("review mission annually",), DecisionId("decision-founding"),
    )
    retention_policy = FoundingRetentionPolicy(
        organization.retention_policy_id, "1", "Initial retention policy", human_id,
        FrozenMap({"retain_audit": True}), "organization records", "constitutional",
        T, "annual review", "higher precedence controls", DecisionId("decision-founding"),
    )
    role = FoundingRole(
        RoleId("role-governor"), "Constitutional Governor", ("govern organization",),
        ("governance",), FrozenMap({"scope": "initial_governance"}),
        "constitutional review", ("human accountable decider required",),
    )
    assignment = FoundingRoleAssignment(
        RoleAssignmentId("role-assignment-founder"), human_id, role.role_id, human_id,
        T, "review under Constitution", "initial constitutional governance",
    )
    decision = FoundingDecision(
        DecisionId("decision-founding"), "1", "A4.constitutional_genesis", human_id,
        human_id, human_id, duty, "direct constitutional bootstrap",
        (FrozenMap({"course": "establish"}), FrozenMap({"course": "defer"})),
        (IntegrityReference("evidence-identity"),), FrozenMap({"scale": "approved", "value": 1}),
        FrozenMap({"residual": "bounded"}), FrozenMap({"outcome": "valid organization"}),
        FrozenMap({"money": 0}), FrozenMap({"classification": "human_reserved"}),
        FrozenMap({"required": False}), "selected",
        FrozenMap({"condition": "annual review"}), FrozenMap({"status": "pending"}),
        FrozenMap({"status": "pending"}),
    )
    grant = FoundingAuthorityGrant(
        AuthorityGrantId("grant-founder"), human_id, human_id, "initial lawful governance",
        "constitutional", ("establish initial governance",), ("ordinary operational work",),
        FrozenMap({"scope": "governance"}), FrozenMap({"money": 0}), T,
        "review after genesis", FrozenMap({"may_delegate": False}),
        FrozenMap({"approval_required": False}), FrozenMap({"maximum": "A4"}),
    )
    recording = GenesisRecordingCommand(
        command_id, "RecordConstitutionalGenesis", RECORD_V1, PAYLOAD_V1, human_id,
        CorrelationId("corr-genesis-alpha"), organization_id, duty, "bootstrap/alpha",
        "reserved_genesis",
    )
    ordered_events = (
        _event("organization_established", command_id, human_id),
        _event("human_actor_established", command_id, human_id),
        _event("constitution_established", command_id, human_id),
        _event("mission_established", command_id, human_id),
        _event("jurisdiction_established", command_id, human_id),
        _event("retention_policy_established", command_id, human_id),
        _event("governor_role_established", command_id, human_id),
        _event("role_assignment_established", command_id, human_id),
        _event("founding_decision_recorded", command_id, human_id),
        _event("authority_grant_established", command_id, human_id),
        _event("audit_record_established", command_id, human_id),
    )
    events = FoundingEventSet(
        ordered_events,
        FoundingEventCoverage(
            "organization_established", "human_actor_established", "constitution_established",
            "mission_established", "jurisdiction_established", "retention_policy_established",
            "governor_role_established", "role_assignment_established",
            "founding_decision_recorded", ("authority_grant_established",),
            "audit_record_established",
        ),
    )
    return BootstrapRequest(
        BootstrapEnvelope(
            MessageId("bootstrap-alpha"), "ConstitutionalBootstrap", CorrelationId("corr-genesis-alpha"),
            T, "reserved_genesis", "establish initial constitutional governance",
            "BootstrapRequest", PAYLOAD_V1, "bootstrap/alpha", NOT_APPLICABLE, NOT_APPLICABLE,
        ),
        PROTOCOL_V1, PAYLOAD_V1, SPEC_0_0_2,
        BootstrapAdmissionBasis.CONSTITUTION_DIRECT,
        GenesisException.SOLE_PREEXISTING_AUTHORITY_EXCEPTION,
        organization, human, constitution, mission, retention_policy,
        role, assignment, decision, (grant,), recording, events,
        AuditRecordId("audit-genesis-alpha"), IntegrityReference("audit-integrity"),
        ExpectedGenesisStream.NONEXISTENT, StreamId("org-alpha-genesis"),
        "bootstrap/alpha", CompetingGenesisRule.REJECT_MATERIAL_CONFLICT,
        IntegrityReference("request-integrity"),
    )


class BootstrapContractTests(unittest.TestCase):
    def test_complete_pre_organization_envelope_and_request(self):
        request = complete_request()
        self.assertEqual(request.envelope.traffic_mode.value, "pre_organization")
        self.assertNotIn("organization_id", BootstrapEnvelope.__dataclass_fields__)
        self.assertIs(request.admission_basis, BootstrapAdmissionBasis.CONSTITUTION_DIRECT)

    def test_ordinary_command_remains_organization_scoped(self):
        self.assertIn("organization_id", __import__("aios_protocol.envelope", fromlist=["CallerEnvelope"]).CallerEnvelope.__dataclass_fields__)

    def test_required_founding_inputs_have_no_defaults(self):
        optional = {field.name for field in dataclasses.fields(BootstrapRequest)
                    if field.default is not dataclasses.MISSING or field.default_factory is not dataclasses.MISSING}
        self.assertEqual(optional, set())

    def test_role_assignment_and_duty_are_complete(self):
        request = complete_request()
        assignment = request.founding_role_assignment
        self.assertEqual(assignment.actor_id, request.verified_human.actor_id)
        self.assertEqual(assignment.lifecycle_state, "active")
        duty = request.founding_decision.duty_reference
        self.assertTrue(all((duty.duty_type, duty.governing_mandate_reference,
                            duty.scope, duty.review_or_completion_condition)))

    def test_required_organization_attributes_are_explicit(self):
        fields = OrganizationGenesisAttributes.__dataclass_fields__
        for name in ("organization_id", "legal_or_operating_name", "mission_record_id",
                     "governing_human_actor_ids", "jurisdiction_scope", "retention_policy_id",
                     "constitution_policy_id"):
            self.assertIn(name, fields)
        request = complete_request()
        self.assertEqual(request.mission.mission_record_id, request.organization.mission_record_id)
        self.assertEqual(request.retention_policy.policy_id, request.organization.retention_policy_id)
        self.assertEqual(request.constitution.constitution_policy_id,
                         request.organization.constitution_policy_id)

    def test_founding_event_set_has_deterministic_complete_order(self):
        events = complete_request().proposed_founding_events.ordered_events
        self.assertEqual(events[0].proposal_key, "organization_established")
        self.assertEqual(events[-1].proposal_key, "audit_record_established")
        self.assertEqual(len(events), 11)

    def test_incomplete_founding_event_set_cannot_be_constructed(self):
        fields = dataclasses.fields(FoundingEventSet)
        self.assertTrue(all(field.default is dataclasses.MISSING for field in fields))
        with self.assertRaises(TypeError):
            FoundingEventSet()  # type: ignore[call-arg]
        request = complete_request()
        bad_coverage = dataclasses.replace(request.proposed_founding_events.coverage, mission="missing")
        with self.assertRaises(ValueError):
            FoundingEventSet(request.proposed_founding_events.ordered_events, bad_coverage)

    def test_recording_command_is_distinct_from_request(self):
        request = complete_request()
        self.assertIsInstance(request.recording_command, GenesisRecordingCommand)
        self.assertNotIsInstance(request.recording_command, CommandSubmission)

    def test_accepted_and_rejected_decisions_are_distinct(self):
        request = complete_request()
        proposal = BootstrapProposal(request, IntegrityReference("proposal-integrity"))
        accepted = BootstrapAcceptedDecision(
            proposal, T, IntegrityReference("constitution-basis"), IntegrityReference("decision-audit"),
        )
        rejected = BootstrapRejectedDecision(
            request, T, ReasonCode.BOOTSTRAP_COMPETING_GENESIS, "genesis identity",
            "materially different founding claim", IntegrityReference("rejection-audit"),
        )
        self.assertIsNot(type(accepted), type(rejected))
        self.assertIsInstance(rejected.reason_code, ReasonCode)

    def test_competing_genesis_inputs_are_explicit(self):
        request = complete_request()
        self.assertEqual(request.idempotency_key, request.recording_command.idempotency_key)
        self.assertIs(request.competing_genesis_rule, CompetingGenesisRule.REJECT_MATERIAL_CONFLICT)
        self.assertIsInstance(request.request_integrity_reference, IntegrityReference)

    def test_unsupported_versions_fail_when_checked(self):
        request = complete_request()
        registry = SupportedVersionRegistry((("BootstrapRequest", (RecordTypeVersion("2.0"),)),))
        with self.assertRaises(StructuralValidationError):
            registry.validate("BootstrapRequest", request.envelope.schema_version)

    def test_bootstrap_records_are_immutable_and_inputs_are_frozen(self):
        request = complete_request()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.idempotency_key = "changed"  # type: ignore[misc]
        self.assertIsInstance(request.initial_authority_grants, tuple)

    def test_logical_round_trip_preserves_constitutional_fields(self):
        request = complete_request()
        logical_fields = {field.name: getattr(request, field.name) for field in dataclasses.fields(request)}
        restored = BootstrapRequest(**logical_fields)
        self.assertTrue(semantic_equal(request, restored))
        self.assertEqual(restored.founding_decision.duty_reference, request.founding_decision.duty_reference)
        self.assertEqual(restored.proposed_founding_events.ordered_events,
                         request.proposed_founding_events.ordered_events)

    def test_model_cannot_be_founding_human(self):
        with self.assertRaises(ValueError):
            complete_request(identity_kind="model")

    def test_committed_outcome_requires_complete_consecutive_recording(self):
        request = complete_request()
        proposal = BootstrapProposal(request, IntegrityReference("proposal-integrity"))
        decision = BootstrapAcceptedDecision(
            proposal, T, IntegrityReference("constitution-basis"), IntegrityReference("decision-audit"),
        )
        recorded = tuple(
            RecordedFoundingEvent(EventId(f"event-{index}"), proposed.event_type, index,
                                  IntegrityReference(f"event-integrity-{index}"))
            for index, proposed in enumerate(request.proposed_founding_events.ordered_events, 1)
        )
        outcome = BootstrapCommitted(
            decision, request.organization.organization_id, request.verified_human.actor_id,
            request.founding_role.role_id, request.founding_role_assignment.role_assignment_id,
            request.founding_decision.decision_id,
            tuple(grant.authority_grant_id for grant in request.initial_authority_grants),
            request.recording_command.command_id, recorded, request.proposed_audit_record_id,
            T, IntegrityReference("outcome-integrity"),
        )
        self.assertTrue(outcome.genesis_exception_exhausted)
        self.assertEqual(len(outcome.founding_events), len(request.proposed_founding_events.ordered_events))

    def test_uncertain_outcome_quarantines_and_prohibits_retry(self):
        uncertain = BootstrapUncertain(
            complete_request(), T, ReasonCode.BOOTSTRAP_IDENTITY_QUARANTINED,
            IntegrityReference("quarantine"), IntegrityReference("reconcile"),
        )
        self.assertTrue(uncertain.retry_prohibited)


if __name__ == "__main__":
    unittest.main()
