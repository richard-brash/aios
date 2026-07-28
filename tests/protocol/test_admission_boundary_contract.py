"""Structural checks for the authenticated recording-boundary contract."""

from __future__ import annotations

import dataclasses
import pathlib
import re
import unittest

from aios_kernel.admission_boundary import RecordingBoundaryResolver
from aios_protocol.admission import (
    AdmissionClaim, AdmissionDenied, AdmissionEstablished, AdmissionGate,
)
from aios_protocol.commands import CommandSubmission
from aios_protocol.identifiers import (
    ActorId, CommandId, IntegrityReference, MessageId, OrganizationId,
)
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import RECORD_V1


ROOT = pathlib.Path(__file__).parents[2]


def claim() -> AdmissionClaim:
    return AdmissionClaim(
        MessageId("message-1"), CommandId("command-1"),
        OrganizationId("organization-1"), ActorId("actor-1"),
        IntegrityReference("proof-1"),
    )


def established() -> AdmissionEstablished:
    return AdmissionEstablished(
        MessageId("message-1"), CommandId("command-1"),
        OrganizationId("organization-1"), ActorId("actor-1"),
        IntegrityReference("genesis-1"), IntegrityReference("identity-1"),
        IntegrityReference("proof-1"), (IntegrityReference("authentication-1"),),
        IntegrityReference("mechanism-1"), RECORD_V1,
    )


class AdmissionBoundaryContractTests(unittest.TestCase):
    def test_claim_contains_only_typed_immutable_resolution_facts(self):
        value = claim()
        self.assertEqual(value.claimed_organization_id, OrganizationId("organization-1"))
        self.assertEqual(value.claimed_initiating_actor_id, ActorId("actor-1"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.command_id = CommandId("changed")

    def test_established_proof_exactly_binds_claim(self):
        proof = established()
        proof.validate_claim(claim())
        substituted = AdmissionClaim(
            MessageId("message-1"), CommandId("command-1"),
            OrganizationId("organization-2"), ActorId("actor-1"),
            IntegrityReference("proof-1"),
        )
        with self.assertRaises(ValueError):
            proof.validate_claim(substituted)

    def test_established_requires_authentication_evidence(self):
        with self.assertRaises(ValueError):
            AdmissionEstablished(
                MessageId("message-1"), CommandId("command-1"),
                OrganizationId("organization-1"), ActorId("actor-1"),
                IntegrityReference("genesis-1"), IntegrityReference("identity-1"),
                IntegrityReference("proof-1"), (), IntegrityReference("mechanism-1"),
                RECORD_V1,
            )

    def test_denial_is_typed_immutable_and_nonauthoritative(self):
        denial = AdmissionDenied(
            MessageId("message-1"), CommandId("command-1"),
            ReasonCode.ORG_UNKNOWN, AdmissionGate.ORGANIZATION_BOUNDARY,
            "recording boundary unavailable", FrozenMap({"diagnostic": "bounded"}),
        )
        self.assertNotIn("organization_id", denial.__dataclass_fields__)
        self.assertNotIn("disposition_id", denial.__dataclass_fields__)
        self.assertNotIn("audit_record", denial.__dataclass_fields__)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            denial.safe_detail = "changed"

    def test_authorization_reason_is_not_admission_denial(self):
        with self.assertRaises(ValueError):
            AdmissionDenied(
                MessageId("message-1"), CommandId("command-1"),
                ReasonCode.AUTH_MISSING, AdmissionGate.ATTRIBUTION_AUTHENTICATION,
                "not an authentication result",
            )

    def test_resolver_port_is_closed_and_capability_neutral(self):
        class Resolver:
            def resolve(self, value: AdmissionClaim):
                return established()

        resolver: RecordingBoundaryResolver = Resolver()
        result = resolver.resolve(claim())
        self.assertIs(type(result), AdmissionEstablished)
        self.assertEqual(set(RecordingBoundaryResolver.__dict__) & {"read", "append", "authorize"}, set())

    def test_command_requires_invocation_proof_reference(self):
        field = CommandSubmission.__dataclass_fields__["invocation_proof_reference"]
        self.assertIs(field.default, dataclasses.MISSING)
        self.assertIs(field.default_factory, dataclasses.MISSING)

    def test_conformance_catalog_has_277_unique_scenarios(self):
        text = (ROOT / "docs/specifications/KERNEL_CONFORMANCE.md").read_text()
        identifiers = re.findall(r"^\| ([A-Z]{3}-[0-9]{3}) \|", text, re.MULTILINE)
        self.assertEqual(len(identifiers), 277)
        self.assertEqual(len(set(identifiers)), 277)
        self.assertEqual(
            {f"ADB-{index:03d}" for index in range(1, 25)},
            {identifier for identifier in identifiers if identifier.startswith("ADB-")},
        )

    def test_normative_sequence_selects_model_a_and_bootstrap_separation(self):
        text = (ROOT / "docs/specifications/KERNEL_PROTOCOL.md").read_text()
        self.assertIn("support-resolution **Model A**", text)
        self.assertIn("Bootstrap remains on PF-17's reserved pre-Organization constitutional path", text)
        self.assertIn("creates and inspects no Organization idempotency entry", text)

    def test_reason_registry_contains_boundary_failure(self):
        self.assertEqual(ReasonCode.ORG_UNKNOWN.value, "ORG.UNKNOWN")


if __name__ == "__main__":
    unittest.main()
