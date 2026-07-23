"""Atomic pre-Organization bootstrap request and outcome contracts."""

from __future__ import annotations

from dataclasses import dataclass

from .envelope import BootstrapEnvelope
from .identifiers import (
    ActorId, AuditRecordId, AuthorityGrantId, DecisionId, EventId,
    IntegrityReference, OrganizationId, RoleAssignmentId, RoleId,
)
from .reason_codes import ReasonCode
from .validation import require_nonempty


@dataclass(frozen=True, slots=True)
class VerifiedHumanReference:
    actor_id: ActorId
    verification_reference: IntegrityReference
    identity_kind: str = "human"

    def __post_init__(self) -> None:
        if self.identity_kind != "human":
            raise ValueError("bootstrap initiator must be a verified Human, never a model")


@dataclass(frozen=True, slots=True)
class BootstrapRequest:
    envelope: BootstrapEnvelope
    proposed_organization_id: OrganizationId
    organization_name: str
    verified_human: VerifiedHumanReference
    governor_role_id: RoleId
    founding_decision_id: DecisionId
    proposed_authority_grant_ids: tuple[AuthorityGrantId, ...]
    founding_audit_reference: IntegrityReference

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposed_authority_grant_ids", tuple(self.proposed_authority_grant_ids))
        require_nonempty(self.organization_name, type(self).__name__, "organization_name")
        if not self.proposed_authority_grant_ids:
            raise ValueError("bootstrap requires initial Authority Grants")


@dataclass(frozen=True, slots=True)
class BootstrapAccepted:
    request: BootstrapRequest
    organization_id: OrganizationId
    verified_human_actor_id: ActorId
    governor_role_id: RoleId
    founding_role_assignment_id: RoleAssignmentId
    founding_decision_id: DecisionId
    initial_authority_grant_ids: tuple[AuthorityGrantId, ...]
    founding_event_ids: tuple[EventId, ...]
    audit_record_id: AuditRecordId

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial_authority_grant_ids", tuple(self.initial_authority_grant_ids))
        object.__setattr__(self, "founding_event_ids", tuple(self.founding_event_ids))
        required = (
            self.organization_id == self.request.proposed_organization_id,
            self.verified_human_actor_id == self.request.verified_human.actor_id,
            self.governor_role_id == self.request.governor_role_id,
            self.founding_decision_id == self.request.founding_decision_id,
            bool(self.initial_authority_grant_ids), bool(self.founding_event_ids),
        )
        if not all(required):
            raise ValueError("accepted bootstrap must be complete and match its request")


@dataclass(frozen=True, slots=True)
class BootstrapRejected:
    request: BootstrapRequest
    reason_code: ReasonCode
    safe_detail: str


@dataclass(frozen=True, slots=True)
class BootstrapPreviouslyAdmitted:
    request: BootstrapRequest
    original_outcome_reference: IntegrityReference
    original_organization_id: OrganizationId


@dataclass(frozen=True, slots=True)
class BootstrapOutcomeUncertain:
    request: BootstrapRequest
    reconciliation_reference: IntegrityReference
    reason_code: ReasonCode = ReasonCode.APPEND_OUTCOME_UNCERTAIN
