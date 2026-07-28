"""Deterministic recording-boundary resolver for tests; never an identity system."""
from __future__ import annotations

from dataclasses import replace

from aios_protocol.admission import (
    AdmissionClaim, AdmissionDenied, AdmissionEstablished, AdmissionGate,
)
from aios_protocol.reason_codes import ReasonCode


class DeterministicRecordingBoundaryResolver:
    """Resolve only preconfigured completed-genesis attribution proofs."""

    def __init__(self, established: tuple[AdmissionEstablished, ...]) -> None:
        self._established=tuple(established)
        self.calls=[]

    def resolve(self,claim: AdmissionClaim):
        self.calls.append(claim)
        organizations={item.organization_id for item in self._established}
        if claim.claimed_organization_id not in organizations:
            return AdmissionDenied(
                claim.message_id,claim.command_id,ReasonCode.ORG_UNKNOWN,
                AdmissionGate.ORGANIZATION_BOUNDARY,"recording boundary unavailable")
        actors={
            item.initiating_actor_id for item in self._established
            if item.organization_id==claim.claimed_organization_id
        }
        if claim.claimed_initiating_actor_id not in actors:
            return AdmissionDenied(
                claim.message_id,claim.command_id,ReasonCode.IDENTITY_UNKNOWN,
                AdmissionGate.ATTRIBUTION_AUTHENTICATION,"initiating attribution unavailable")
        for item in self._established:
            if (item.organization_id==claim.claimed_organization_id and
                item.initiating_actor_id==claim.claimed_initiating_actor_id and
                item.invocation_proof_reference==claim.invocation_proof_reference):
                result=replace(
                    item,claim_message_id=claim.message_id,command_id=claim.command_id)
                result.validate_claim(claim)
                return result
        return AdmissionDenied(
            claim.message_id,claim.command_id,ReasonCode.IDENTITY_FORGED,
            AdmissionGate.ATTRIBUTION_AUTHENTICATION,"initiating attribution unavailable")
