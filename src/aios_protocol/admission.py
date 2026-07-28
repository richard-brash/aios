"""Authenticated Organization recording-boundary logical contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identifiers import (
    ActorId, CommandId, IntegrityReference, MessageId, OrganizationId,
)
from .reason_codes import ReasonCode
from .validation import FrozenMap, require_nonempty, require_type
from .versions import RECORD_V1, RecordTypeVersion


class AdmissionGate(str, Enum):
    ORGANIZATION_BOUNDARY = "organization_boundary"
    ATTRIBUTION_AUTHENTICATION = "attribution_authentication"
    ADMISSION_DEPENDENCY = "admission_dependency"


@dataclass(frozen=True, slots=True)
class AdmissionClaim:
    """Effect-free claim supplied to the trusted recording-boundary resolver."""

    message_id: MessageId
    command_id: CommandId
    claimed_organization_id: OrganizationId
    claimed_initiating_actor_id: ActorId
    invocation_proof_reference: IntegrityReference
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.message_id, MessageId, type(self).__name__, "message_id")
        require_type(self.command_id, CommandId, type(self).__name__, "command_id")
        require_type(
            self.claimed_organization_id, OrganizationId,
            type(self).__name__, "claimed_organization_id",
        )
        require_type(
            self.claimed_initiating_actor_id, ActorId,
            type(self).__name__, "claimed_initiating_actor_id",
        )
        require_type(
            self.invocation_proof_reference, IntegrityReference,
            type(self).__name__, "invocation_proof_reference",
        )
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")


@dataclass(frozen=True, slots=True)
class AdmissionEstablished:
    """Trusted proof that authoritative Organization attribution is established."""

    claim_message_id: MessageId
    command_id: CommandId
    organization_id: OrganizationId
    initiating_actor_id: ActorId
    organization_genesis_reference: IntegrityReference
    actor_identity_reference: IntegrityReference
    invocation_proof_reference: IntegrityReference
    authentication_evidence_references: tuple[IntegrityReference, ...]
    admission_mechanism_reference: IntegrityReference
    admission_mechanism_version: RecordTypeVersion
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        for name, expected in (
            ("claim_message_id", MessageId), ("command_id", CommandId),
            ("organization_id", OrganizationId), ("initiating_actor_id", ActorId),
            ("organization_genesis_reference", IntegrityReference),
            ("actor_identity_reference", IntegrityReference),
            ("invocation_proof_reference", IntegrityReference),
            ("admission_mechanism_reference", IntegrityReference),
            ("admission_mechanism_version", RecordTypeVersion),
            ("schema_version", RecordTypeVersion),
        ):
            require_type(getattr(self, name), expected, type(self).__name__, name)
        evidence=tuple(self.authentication_evidence_references)
        if not evidence:
            raise ValueError("authenticated admission requires evidence references")
        for index, reference in enumerate(evidence):
            require_type(
                reference, IntegrityReference, type(self).__name__,
                f"authentication_evidence_references[{index}]",
            )
        object.__setattr__(self, "authentication_evidence_references", evidence)

    def validate_claim(self, claim: AdmissionClaim) -> None:
        require_type(claim, AdmissionClaim, type(self).__name__, "claim")
        if (
            self.claim_message_id != claim.message_id
            or self.command_id != claim.command_id
            or self.organization_id != claim.claimed_organization_id
            or self.initiating_actor_id != claim.claimed_initiating_actor_id
            or self.invocation_proof_reference != claim.invocation_proof_reference
        ):
            raise ValueError("admission proof does not exactly bind the submitted claim")


_ADMISSION_DENIAL_CODES = frozenset({
    ReasonCode.ORG_UNKNOWN,
    ReasonCode.ORG_BOUNDARY_VIOLATION,
    ReasonCode.IDENTITY_UNKNOWN,
    ReasonCode.IDENTITY_FORGED,
    ReasonCode.IDENTITY_SUSPENDED,
    ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
})


@dataclass(frozen=True, slots=True)
class AdmissionDenied:
    """Non-authoritative denial; it establishes no Organization boundary."""

    claim_message_id: MessageId
    command_id: CommandId
    reason_code: ReasonCode
    failed_gate: AdmissionGate
    safe_detail: str
    diagnostic_facts: FrozenMap = field(default_factory=FrozenMap)
    schema_version: RecordTypeVersion = RECORD_V1

    def __post_init__(self) -> None:
        require_type(self.claim_message_id, MessageId, type(self).__name__, "claim_message_id")
        require_type(self.command_id, CommandId, type(self).__name__, "command_id")
        require_type(self.reason_code, ReasonCode, type(self).__name__, "reason_code")
        require_type(self.failed_gate, AdmissionGate, type(self).__name__, "failed_gate")
        require_nonempty(self.safe_detail, type(self).__name__, "safe_detail")
        require_type(self.schema_version, RecordTypeVersion, type(self).__name__, "schema_version")
        if self.reason_code not in _ADMISSION_DENIAL_CODES:
            raise ValueError("reason code is not valid for admission-boundary denial")
        object.__setattr__(self, "diagnostic_facts", FrozenMap(self.diagnostic_facts))


AdmissionResolution = AdmissionEstablished | AdmissionDenied
