"""Structural contract tests mapped to KERNEL_CONFORMANCE.md suites.

These tests cover fixture/determinism, command admission, Work Root, Approval,
Resource, lifecycle structure, scheduling, Tool reconciliation, event ordering,
subscription isolation, memory, bootstrap, audit, and replay/recovery suites.
They do not claim behavioral kernel conformance.
"""

from __future__ import annotations

import dataclasses
import inspect
import pathlib
import re
import unittest
from datetime import datetime, timezone

from aios_protocol.append import AppendOutcomeUncertain
from aios_protocol.approvals import ApprovalMode, ApprovalReference, RevocationState
from aios_protocol.commands import DutyWorkRoot, GoalWorkRoot, ResourceDimension
from aios_protocol.comparison import semantic_equal, stable_ordered_equal
from aios_protocol.dispositions import Accepted, PreviouslyAdmitted, Rejected
from aios_protocol.envelope import (
    AdapterObservationEnvelope, BootstrapEnvelope, CallerEnvelope, EventEnvelope,
    KernelDispositionEnvelope, LiveDeliveryEnvelope, ReplayReportEnvelope,
    TrafficMode,
)
from aios_protocol.events import EpistemicStatus, EventRecord, ProposedEvent, ToolKnowledgeStage
from aios_protocol.identifiers import *  # stable symbolic fixture constructors
from aios_protocol.presence import (
    Conflicted, INTENTIONALLY_EMPTY, Known, NOT_APPLICABLE, NOT_YET_KNOWN,
    Redacted, UNKNOWN, Withheld,
)
from aios_protocol.reason_codes import REASON_METADATA, ReasonCode
from aios_protocol.replay import ReplayReport, SideEffectCounters
from aios_protocol.resources import ResourceQuantity, ReservationRequest
from aios_protocol.schedules import ScheduleDueObservation, ScheduleInstanceMaterialization
from aios_protocol.subscriptions import (
    AcceptedSubscription, EventDelivery, SubscriptionScope,
)
from aios_protocol.tools import AuthorizedToolScope, ToolDispatchIntent, ToolExecutionAttempt, VerifiedToolOutcome
from aios_protocol.validation import FrozenMap, StructuralValidationError
from aios_protocol.versions import PayloadVersion, RecordTypeVersion, SupportedVersionRegistry, Version


T = datetime(2030, 1, 1, tzinfo=timezone.utc)
V = RecordTypeVersion("1.0")


def caller(payload=FrozenMap()):
    return CallerEnvelope(MessageId("msg-1"), "CommandSubmitted", OrganizationId("org-1"),
        ActorId("actor-1"), CorrelationId("corr-1"), T, "internal", "test",
        "operation", PayloadVersion("1.0"), payload)


def disposition_envelope():
    return KernelDispositionEnvelope(MessageId("disp-1"), "AdmissionDisposition", OrganizationId("org-1"),
        ActorId("actor-1"), CommandId("cmd-1"), CorrelationId("corr-1"), T, "internal")


def event_envelope(position=1):
    return EventEnvelope(MessageId("emsg-1"), "Event", OrganizationId("org-1"), ActorId("actor-1"),
        CommandId("cmd-1"), CorrelationId("corr-1"), T, StreamId("stream-1"), position,
        "internal", IntegrityReference("sha256:event"))


class ValueContractTests(unittest.TestCase):
    def test_01_every_identifier_rejects_empty_or_malformed(self):
        import aios_protocol.identifiers as ids
        classes = [c for _, c in inspect.getmembers(ids, inspect.isclass)
                   if issubclass(c, ids.Identifier) and c is not ids.Identifier]
        self.assertGreaterEqual(len(classes), 20)
        for cls in classes:
            with self.subTest(cls=cls.__name__), self.assertRaises((StructuralValidationError, ValueError)):
                cls("")
            with self.subTest(cls=cls.__name__), self.assertRaises((StructuralValidationError, ValueError)):
                cls("contains space")

    def test_02_identifier_classes_not_interchangeable(self):
        self.assertNotEqual(MessageId("same"), EventId("same"))
        self.assertIsNot(type(MessageId("same")), type(EventId("same")))

    def test_03_naive_timestamp_rejected(self):
        with self.assertRaises(StructuralValidationError):
            CallerEnvelope(MessageId("m"), "x", OrganizationId("o"), ActorId("a"), CorrelationId("c"),
                datetime(2030, 1, 1), "i", "p", "x", PayloadVersion("1.0"))

    def test_04_construction_requires_explicit_time(self):
        self.assertEqual(caller().issued_at, T)
        self.assertFalse(any(f.default_factory is datetime.now for f in dataclasses.fields(CallerEnvelope)))

    def test_05_presence_states_are_distinct(self):
        values = [Known("x"), UNKNOWN, NOT_YET_KNOWN, NOT_APPLICABLE, INTENTIONALLY_EMPTY,
                  Withheld("secret", IntegrityReference("ref-w")), Redacted(IntegrityReference("ref-r")),
                  Conflicted((IntegrityReference("ref-1"), IntegrityReference("ref-2")))]
        self.assertEqual(len({repr(v) for v in values}), len(values))

    def test_06_withheld_and_redacted_do_not_hold_content(self):
        self.assertNotIn("payload", repr(Withheld("secret", IntegrityReference("ref-w"))))
        self.assertNotIn("payload", repr(Redacted(IntegrityReference("ref-r"))))

    def test_07_work_root_is_exclusive_union(self):
        self.assertIsInstance(GoalWorkRoot(GoalId("goal-1")), GoalWorkRoot)
        self.assertIsInstance(DutyWorkRoot("safety", "constitution:1", ActorId("a"), "org", "closed"), DutyWorkRoot)
        self.assertFalse(hasattr(GoalWorkRoot(GoalId("g")), "duty_type"))

    def test_08_caller_has_no_authoritative_evaluation_time(self):
        self.assertNotIn("evaluation_time", CallerEnvelope.__dataclass_fields__)

    def test_09_caller_has_no_event_stream_position(self):
        self.assertNotIn("stream_position", CallerEnvelope.__dataclass_fields__)

    def test_10_payload_cannot_override_attribution(self):
        with self.assertRaises(StructuralValidationError):
            caller(FrozenMap({"initiating_actor_id": "forged"}))


class BoundaryContractTests(unittest.TestCase):
    def test_11_accepted_cannot_claim_verified_tool_success(self):
        self.assertNotIn("verified_outcome", Accepted.__dataclass_fields__)

    def test_12_rejected_cannot_authorize_dispatch(self):
        self.assertNotIn("dispatch_intent", Rejected.__dataclass_fields__)

    def test_13_duplicate_links_original_disposition(self):
        item = PreviouslyAdmitted(disposition_envelope(), MessageId("disp-original"), (EventId("event-1"),))
        self.assertEqual(item.original_disposition_id, MessageId("disp-original"))

    def test_14_event_confidence_contract(self):
        ProposedEvent(EventId("e1"), "Changed", V, ActorId("a"), (), None, EpistemicStatus.DETERMINISTIC)
        with self.assertRaises(ValueError):
            ProposedEvent(EventId("e2"), "Predicted", V, ActorId("a"), (), None, EpistemicStatus.PREDICTED)
        ProposedEvent(EventId("e3"), "Predicted", V, ActorId("a"), (), None,
                      EpistemicStatus.PREDICTED, Known(.7))

    def test_15_event_self_references_rejected(self):
        base = dict(envelope=event_envelope(), event_id=EventId("e1"), event_type="Changed", event_version=V,
            participant_actor_ids=(), causal_reference=None, occurred_at=T, entity_references=(),
            epistemic_status=EpistemicStatus.DETERMINISTIC, confidence=NOT_APPLICABLE, work_root=None,
            projection_effects=FrozenMap(), resource_effects=FrozenMap(), approval_use_effects=FrozenMap(),
            audit_record_id=AuditRecordId("audit-1"), integrity_reference=IntegrityReference("hash-1"))
        for field in ("corrects_event_id", "supersedes_event_id", "tombstones_event_id"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                EventRecord(**base, **{field: EventId("e1")})

    def test_16_append_uncertainty_has_no_position_claim(self):
        self.assertNotIn("new_stream_position", AppendOutcomeUncertain.__dataclass_fields__)
        self.assertNotIn("unchanged_stream_position", AppendOutcomeUncertain.__dataclass_fields__)

    def test_17_tool_attempt_distinct_from_verified_outcome(self):
        self.assertIsNot(ToolExecutionAttempt, VerifiedToolOutcome)
        self.assertNotIn("verified_result", ToolExecutionAttempt.__dataclass_fields__)

    def test_18_adapter_cannot_grant_authority(self):
        from aios_protocol.tools import AdapterInterpretation
        self.assertNotIn("authority_granted", AdapterInterpretation.__dataclass_fields__)

    def test_19_replay_dispatch_is_rejected(self):
        scope = AuthorizedToolScope(ToolId("tool-1"), "send", V, FrozenMap(), FrozenMap())
        with self.assertRaises(ValueError):
            ToolDispatchIntent(CommandId("c"), OperationId("o"), DispatchId("d"), ActorId("adapter"), scope,
                GoalWorkRoot(GoalId("g")), IntegrityReference("req"), (), (), AuditRecordId("audit"), TrafficMode.REPLAY)

    def test_20_replay_report_requires_zero_effect_evidence(self):
        with self.assertRaises(ValueError):
            SideEffectCounters(tool_calls=1)
        self.assertIn("zero_effect_evidence_reference", ReplayReport.__dataclass_fields__)


class GovernanceStructureTests(unittest.TestCase):
    def test_21_delivery_preserves_event_identity(self):
        env = LiveDeliveryEnvelope(MessageId("m"), "delivery", OrganizationId("o"), "internal", T)
        d = EventDelivery(env, DeliveryId("d"), SubscriptionId("s"), EventId("e"), 1, V, IntegrityReference("p"))
        self.assertEqual(d.event_id, EventId("e"))

    def test_22_filter_cannot_expand_scope(self):
        narrow = SubscriptionScope(frozenset({"A"}), "internal", "audit", "exact", V)
        accepted = AcceptedSubscription(MessageId("m"), SubscriptionId("s"), OrganizationId("o"), ActorId("a"), narrow, 0)
        broad = SubscriptionScope(frozenset({"A", "B"}), "internal", "audit", "exact", V)
        with self.assertRaises(ValueError): accepted.validate_delivery_scope(broad)

    def test_23_single_use_maximum_is_one(self):
        base = dict(approval_id=ApprovalId("ap"), decision_id=DecisionId("dec"),
                    permitted_scope=FrozenMap(), effective_at=T,
                    expires_at=datetime(2031, 1, 1, tzinfo=timezone.utc),
                    revocation_state=RevocationState.ACTIVE, current_usage=0,
                    conditions=(), revocation_triggers=(), review_schedule=None)
        ApprovalReference(mode=ApprovalMode.SINGLE_USE, maximum_usage=1, **base)
        with self.assertRaises(ValueError): ApprovalReference(mode=ApprovalMode.SINGLE_USE, maximum_usage=2, **base)

    def test_24_bounded_repeat_requires_greater_than_one(self):
        with self.assertRaises(ValueError):
            ApprovalReference(ApprovalId("ap"), DecisionId("dec"), ApprovalMode.BOUNDED_REPEAT,
                FrozenMap(), T, datetime(2031, 1, 1, tzinfo=timezone.utc),
                RevocationState.ACTIVE, 0, 1, (), (), None)

    def test_25_approval_does_not_grant_authority(self):
        self.assertFalse(any("authority" in name.lower() for name in ApprovalReference.__dataclass_fields__))

    def test_26_reservation_is_not_consumption(self):
        self.assertNotIn("consumed_amount", ReservationRequest.__dataclass_fields__)

    def test_27_resource_dimensions_are_independent(self):
        self.assertEqual(len(ResourceDimension), 8)
        self.assertNotEqual(ResourceDimension.MONEY, ResourceDimension.COMPUTE)

    def test_28_due_observation_is_not_command(self):
        self.assertNotIn("command_id", ScheduleDueObservation.__dataclass_fields__)

    def test_29_schedule_instance_has_distinct_identities(self):
        fields = ScheduleInstanceMaterialization.__dataclass_fields__
        self.assertIn("schedule_instance_id", fields); self.assertIn("command_id", fields)

    def test_30_bootstrap_acceptance_cannot_be_partial(self):
        from aios_protocol.bootstrap import BootstrapCommitted
        self.assertIn("founding_events", BootstrapCommitted.__dataclass_fields__)
        self.assertIn("initial_authority_grant_ids", BootstrapCommitted.__dataclass_fields__)
        self.assertIn("genesis_exception_exhausted", BootstrapCommitted.__dataclass_fields__)

    def test_31_bootstrap_human_cannot_be_model(self):
        from aios_protocol.bootstrap import VerifiedHumanReference
        with self.assertRaises(ValueError):
            VerifiedHumanReference(
                ActorId("model-1"), IntegrityReference("human-id"),
                IntegrityReference("verify"), "owner", "model",
            )


class DeterminismAndSafetyTests(unittest.TestCase):
    def test_32_historical_record_versions_are_explicit(self):
        self.assertIn("event_version", EventRecord.__dataclass_fields__)
        self.assertIn("payload_version", CallerEnvelope.__dataclass_fields__)

    def test_33_unknown_versions_not_silently_coerced(self):
        unknown = Version("99.0")
        registry = SupportedVersionRegistry((("Thing", (RecordTypeVersion("1.0"),)),))
        self.assertEqual(unknown.major, 99)
        with self.assertRaises(StructuralValidationError): registry.validate("Thing", RecordTypeVersion("99.0"))

    def test_34_reason_registry_complete_and_unique(self):
        self.assertEqual(set(REASON_METADATA), set(ReasonCode))
        self.assertEqual(len({code.value for code in ReasonCode}), len(ReasonCode))
        specification = pathlib.Path(__file__).parents[2] / "docs" / "specifications" / "KERNEL_PROTOCOL.md"
        normative = set(re.findall(r"^\| `([A-Z][A-Z_]+\.[A-Z][A-Z_]+)` \|", specification.read_text(), re.MULTILINE))
        self.assertEqual(normative, {code.value for code in ReasonCode})

    def test_35_human_detail_not_machine_key(self):
        self.assertTrue(all(code.value not in meta.meaning for code, meta in REASON_METADATA.items()))

    def test_36_comparison_preserves_order(self):
        self.assertTrue(stable_ordered_equal((EventId("a"), EventId("b")), (EventId("a"), EventId("b"))))
        self.assertFalse(stable_ordered_equal((EventId("a"), EventId("b")), (EventId("b"), EventId("a"))))

    def test_37_symbolic_bindings_do_not_hide_other_differences(self):
        self.assertTrue(semantic_equal(EventId("symbol"), EventId("actual"),
            symbolic_bindings={EventId("symbol"): EventId("actual")}))
        self.assertFalse(semantic_equal((EventId("symbol"), "x"), (EventId("actual"), "y"),
            symbolic_bindings={EventId("symbol"): EventId("actual")}))

    def test_38_mutable_inputs_cannot_mutate_records(self):
        raw = {"nested": [1, 2]}; frozen = FrozenMap(raw); raw["nested"].append(3)
        self.assertEqual(frozen["nested"], (1, 2))

    def test_39_validation_errors_do_not_leak_values(self):
        secret = "INVOCATION-PROOF-SECRET"
        try: caller(FrozenMap({"stream_position": secret}))
        except StructuralValidationError as error:
            self.assertNotIn(secret, str(error)); self.assertTrue(error.field_path)
        else: self.fail("trusted override was not rejected")

    def test_40_import_sources_have_no_side_effect_calls(self):
        package = pathlib.Path(__file__).parents[2] / "src" / "aios_protocol"
        forbidden = ("datetime.now(", "datetime.utcnow(", "time.time(", "random.", "os.environ", "getenv(", "open(", "socket.")
        source = "\n".join(p.read_text() for p in package.glob("*.py"))
        for token in forbidden:
            with self.subTest(token=token): self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
