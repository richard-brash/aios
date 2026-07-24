"""Immutable contracts for the pre-Organization constitutional genesis protocol.

These records describe bootstrap input, proposal, admission disposition, and
recording outcomes.  They deliberately contain no bootstrap execution logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .commands import DutyWorkRoot
from .envelope import BootstrapEnvelope
from .identifiers import (
    ActorId, AuditRecordId, AuthorityGrantId, CommandId, CorrelationId,
    DecisionId, EventId, IntegrityReference, MissionId, OrganizationId,
    PolicyId, RoleAssignmentId, RoleId, StreamId,
)
from .reason_codes import ReasonCode
from .validation import FrozenMap, require_aware, require_nonempty, require_type, require_types
from .versions import (
    PayloadVersion, ProtocolFamilyVersion, RecordTypeVersion,
    SpecificationVersion,
)


class BootstrapAdmissionBasis(str, Enum):
    CONSTITUTION_DIRECT = "constitution_direct"


class GenesisException(str, Enum):
    SOLE_PREEXISTING_AUTHORITY_EXCEPTION = "sole_preexisting_authority_exception"


class ExpectedGenesisStream(str, Enum):
    NONEXISTENT = "nonexistent"
    EMPTY = "empty"


class CompetingGenesisRule(str, Enum):
    """The specification-permitted deterministic default for material conflict."""

    REJECT_MATERIAL_CONFLICT = "reject_material_conflict"


@dataclass(frozen=True, slots=True)
class VerifiedHumanReference:
    actor_id: ActorId
    human_identity_reference: IntegrityReference
    verification_reference: IntegrityReference
    relationship_to_organization: str
    identity_kind: str = "human"

    def __post_init__(self) -> None:
        require_type(self.actor_id, ActorId, type(self).__name__, "actor_id")
        require_type(self.human_identity_reference, IntegrityReference, type(self).__name__, "human_identity_reference")
        require_type(self.verification_reference, IntegrityReference, type(self).__name__, "verification_reference")
        require_nonempty(self.relationship_to_organization, type(self).__name__, "relationship_to_organization")
        if self.identity_kind != "human":
            raise ValueError("bootstrap initiator must be a verified Human, never a model or AI Employee")


@dataclass(frozen=True, slots=True)
class OrganizationGenesisAttributes:
    organization_id: OrganizationId
    legal_or_operating_name: str
    mission_record_id: MissionId
    governing_human_actor_ids: tuple[ActorId, ...]
    jurisdiction_scope: str
    retention_policy_id: PolicyId
    constitution_policy_id: PolicyId

    def __post_init__(self) -> None:
        require_type(self.organization_id, OrganizationId, type(self).__name__, "organization_id")
        require_nonempty(self.legal_or_operating_name, type(self).__name__, "legal_or_operating_name")
        require_nonempty(self.jurisdiction_scope, type(self).__name__, "jurisdiction_scope")
        humans = require_types(self.governing_human_actor_ids, ActorId, type(self).__name__, "governing_human_actor_ids")
        if not humans:
            raise ValueError("bootstrap requires at least one governing Human")
        object.__setattr__(self, "governing_human_actor_ids", humans)


@dataclass(frozen=True, slots=True)
class ConstitutionEstablishment:
    constitution_policy_id: PolicyId
    constitutional_version: str
    source_integrity_reference: IntegrityReference
    adopting_human_actor_ids: tuple[ActorId, ...]
    founding_decision_id: DecisionId
    effective_at: datetime

    def __post_init__(self) -> None:
        require_nonempty(self.constitutional_version, type(self).__name__, "constitutional_version")
        adopters = require_types(
            self.adopting_human_actor_ids, ActorId, type(self).__name__, "adopting_human_actor_ids",
        )
        if not adopters:
            raise ValueError("Constitution establishment requires a Human adopter")
        object.__setattr__(self, "adopting_human_actor_ids", adopters)
        require_aware(self.effective_at, type(self).__name__, "effective_at")


@dataclass(frozen=True, slots=True)
class FoundingMission:
    mission_record_id: MissionId
    statement: str
    adopting_human_actor_ids: tuple[ActorId, ...]
    effective_at: datetime
    success_or_review_indicators: tuple[str, ...]
    founding_decision_id: DecisionId

    def __post_init__(self) -> None:
        require_nonempty(self.statement, type(self).__name__, "statement")
        adopters = require_types(
            self.adopting_human_actor_ids, ActorId, type(self).__name__, "adopting_human_actor_ids",
        )
        if not adopters:
            raise ValueError("founding Mission requires a Human adopter")
        object.__setattr__(self, "adopting_human_actor_ids", adopters)
        indicators = tuple(self.success_or_review_indicators)
        if not indicators:
            raise ValueError("founding Mission requires success or review indicators")
        for index, value in enumerate(indicators):
            require_nonempty(value, type(self).__name__, f"success_or_review_indicators[{index}]")
        object.__setattr__(self, "success_or_review_indicators", indicators)
        require_aware(self.effective_at, type(self).__name__, "effective_at")


@dataclass(frozen=True, slots=True)
class FoundingRetentionPolicy:
    policy_id: PolicyId
    policy_content_version: str
    title: str
    issuer_actor_id: ActorId
    rule_set: FrozenMap
    scope: str
    precedence: str
    effective_at: datetime
    review_or_expiry_condition: str
    conflict_behavior: str
    founding_decision_id: DecisionId

    def __post_init__(self) -> None:
        for name in (
            "policy_content_version", "title", "scope", "precedence",
            "review_or_expiry_condition", "conflict_behavior",
        ):
            require_nonempty(getattr(self, name), type(self).__name__, name)
        require_aware(self.effective_at, type(self).__name__, "effective_at")


@dataclass(frozen=True, slots=True)
class FoundingRole:
    role_id: RoleId
    name: str
    duties: tuple[str, ...]
    eligible_capability_references: tuple[str, ...]
    eligible_authority_scope: FrozenMap
    escalation_path: str
    separation_of_duties_constraints: tuple[str, ...]

    def __post_init__(self) -> None:
        require_nonempty(self.name, type(self).__name__, "name")
        for field_name in ("duties", "eligible_capability_references", "separation_of_duties_constraints"):
            values = tuple(getattr(self, field_name))
            if not values:
                raise ValueError(f"{field_name} must not be empty")
            for index, value in enumerate(values):
                require_nonempty(value, type(self).__name__, f"{field_name}[{index}]")
            object.__setattr__(self, field_name, values)
        require_nonempty(self.escalation_path, type(self).__name__, "escalation_path")


@dataclass(frozen=True, slots=True)
class FoundingRoleAssignment:
    role_assignment_id: RoleAssignmentId
    actor_id: ActorId
    role_id: RoleId
    assigned_by_actor_id: ActorId
    effective_at: datetime
    review_condition: str
    duty_scope: str
    lifecycle_state: str = "active"

    def __post_init__(self) -> None:
        require_aware(self.effective_at, type(self).__name__, "effective_at")
        require_nonempty(self.review_condition, type(self).__name__, "review_condition")
        require_nonempty(self.duty_scope, type(self).__name__, "duty_scope")
        if self.lifecycle_state != "active":
            raise ValueError("founding Role Assignment must become active atomically")


@dataclass(frozen=True, slots=True)
class FoundingDecision:
    decision_id: DecisionId
    decision_content_version: str
    decision_type: str
    initiating_actor_id: ActorId
    accountable_decider_actor_id: ActorId
    technical_recorder_actor_id: ActorId
    duty_reference: DutyWorkRoot
    authority_basis: str
    alternatives_considered: tuple[FrozenMap, ...]
    evidence_references: tuple[IntegrityReference, ...]
    confidence: FrozenMap
    risks: FrozenMap
    expected_benefit: FrozenMap
    expected_cost: FrozenMap
    reversibility: FrozenMap
    required_approval: FrozenMap
    outcome: str
    follow_up_review: FrozenMap
    result_metrics: FrozenMap
    lessons_learned: FrozenMap

    def __post_init__(self) -> None:
        for name in ("decision_content_version", "decision_type", "authority_basis", "outcome"):
            require_nonempty(getattr(self, name), type(self).__name__, name)
        if self.initiating_actor_id != self.accountable_decider_actor_id:
            raise ValueError("the verified founding Human must be the accountable decider")
        if not self.alternatives_considered or not self.evidence_references:
            raise ValueError("founding Decision requires alternatives and pinned evidence")
        object.__setattr__(self, "alternatives_considered", tuple(self.alternatives_considered))
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))


@dataclass(frozen=True, slots=True)
class FoundingAuthorityGrant:
    authority_grant_id: AuthorityGrantId
    issuer_actor_id: ActorId
    recipient_actor_id: ActorId
    purpose: str
    authority_level: str
    permitted_actions: tuple[str, ...]
    prohibited_actions: tuple[str, ...]
    resource_scope: FrozenMap
    limits: FrozenMap
    effective_at: datetime
    review_or_expiry_condition: str
    delegation_rights: FrozenMap
    approval_rules: FrozenMap
    risk_limits: FrozenMap

    def __post_init__(self) -> None:
        for name in ("purpose", "authority_level", "review_or_expiry_condition"):
            require_nonempty(getattr(self, name), type(self).__name__, name)
        require_aware(self.effective_at, type(self).__name__, "effective_at")
        permitted = tuple(self.permitted_actions)
        prohibited = tuple(self.prohibited_actions)
        if not permitted:
            raise ValueError("founding Authority Grant requires bounded permitted actions")
        for field_name, values in (("permitted_actions", permitted), ("prohibited_actions", prohibited)):
            for index, value in enumerate(values):
                require_nonempty(value, type(self).__name__, f"{field_name}[{index}]")
            object.__setattr__(self, field_name, values)


@dataclass(frozen=True, slots=True)
class GenesisRecordingCommand:
    command_id: CommandId
    command_type: str
    schema_version: RecordTypeVersion
    payload_version: PayloadVersion
    initiating_actor_id: ActorId
    correlation_id: CorrelationId
    proposed_organization_id: OrganizationId
    duty_reference: DutyWorkRoot
    idempotency_key: str
    reserved_genesis_classification: str

    def __post_init__(self) -> None:
        for name in ("command_type", "idempotency_key", "reserved_genesis_classification"):
            require_nonempty(getattr(self, name), type(self).__name__, name)
        if "genesis" not in self.reserved_genesis_classification.lower():
            raise ValueError("recording Command requires an explicit reserved genesis classification")


@dataclass(frozen=True, slots=True)
class FoundingEventProposal:
    proposal_key: str
    event_type: str
    event_version: RecordTypeVersion
    payload_version: PayloadVersion
    initiating_actor_id: ActorId
    causal_reference: CommandId
    reserved_genesis_classification: str
    payload: FrozenMap = field(default_factory=FrozenMap)

    def __post_init__(self) -> None:
        require_nonempty(self.proposal_key, type(self).__name__, "proposal_key")
        require_nonempty(self.event_type, type(self).__name__, "event_type")
        require_nonempty(self.reserved_genesis_classification, type(self).__name__, "reserved_genesis_classification")
        if "genesis" not in self.reserved_genesis_classification.lower():
            raise ValueError("founding Event requires an explicit reserved genesis classification")


@dataclass(frozen=True, slots=True)
class FoundingEventCoverage:
    """Proposal keys proving that every required founding fact is represented.

    Several facts may intentionally be established by one Event. The
    specifications require complete facts, but do not prescribe Event
    granularity or concrete Event type names.
    """

    organization: str
    human_actor: str
    constitution: str
    mission: str
    jurisdiction: str
    retention_policy: str
    governor_role: str
    role_assignment: str
    founding_decision: str
    authority_grants: tuple[str, ...]
    audit_record: str

    def __post_init__(self) -> None:
        for name in (
            "organization", "human_actor", "constitution", "mission", "jurisdiction",
            "retention_policy", "governor_role", "role_assignment", "founding_decision",
            "audit_record",
        ):
            require_nonempty(getattr(self, name), type(self).__name__, name)
        grants = tuple(self.authority_grants)
        if not grants:
            raise ValueError("founding Event coverage requires initial Authority Grants")
        for index, key in enumerate(grants):
            require_nonempty(key, type(self).__name__, f"authority_grants[{index}]")
        object.__setattr__(self, "authority_grants", grants)


@dataclass(frozen=True, slots=True)
class FoundingEventSet:
    ordered_events: tuple[FoundingEventProposal, ...]
    coverage: FoundingEventCoverage

    def __post_init__(self) -> None:
        events = tuple(self.ordered_events)
        if not events:
            raise ValueError("founding Event set must not be empty")
        object.__setattr__(self, "ordered_events", events)
        keys = {event.proposal_key for event in events}
        if len(keys) != len(events):
            raise ValueError("founding Event proposal keys must be distinct")
        covered = {
            self.coverage.organization, self.coverage.human_actor, self.coverage.constitution,
            self.coverage.mission, self.coverage.jurisdiction, self.coverage.retention_policy,
            self.coverage.governor_role, self.coverage.role_assignment,
            self.coverage.founding_decision, *self.coverage.authority_grants,
            self.coverage.audit_record,
        }
        if not covered <= keys:
            raise ValueError("founding Event coverage references a missing proposal")
        command_ids = {event.causal_reference for event in events}
        if len(command_ids) != 1:
            raise ValueError("all founding Events must name the same genesis recording Command")


@dataclass(frozen=True, slots=True)
class BootstrapRequest:
    envelope: BootstrapEnvelope
    protocol_family_version: ProtocolFamilyVersion
    payload_version: PayloadVersion
    specification_version: SpecificationVersion
    admission_basis: BootstrapAdmissionBasis
    genesis_exception: GenesisException
    organization: OrganizationGenesisAttributes
    verified_human: VerifiedHumanReference
    constitution: ConstitutionEstablishment
    mission: FoundingMission
    retention_policy: FoundingRetentionPolicy
    founding_role: FoundingRole
    founding_role_assignment: FoundingRoleAssignment
    founding_decision: FoundingDecision
    initial_authority_grants: tuple[FoundingAuthorityGrant, ...]
    recording_command: GenesisRecordingCommand
    proposed_founding_events: FoundingEventSet
    proposed_audit_record_id: AuditRecordId
    proposed_audit_integrity_reference: IntegrityReference
    expected_stream: ExpectedGenesisStream
    genesis_stream_id: StreamId
    idempotency_key: str
    competing_genesis_rule: CompetingGenesisRule
    request_integrity_reference: IntegrityReference

    def __post_init__(self) -> None:
        grants = tuple(self.initial_authority_grants)
        if not grants:
            raise ValueError("bootstrap requires initial Authority Grants")
        object.__setattr__(self, "initial_authority_grants", grants)
        human_id = self.verified_human.actor_id
        checks = (
            human_id in self.organization.governing_human_actor_ids,
            self.organization.constitution_policy_id == self.constitution.constitution_policy_id,
            self.organization.mission_record_id == self.mission.mission_record_id,
            self.organization.retention_policy_id == self.retention_policy.policy_id,
            human_id in self.constitution.adopting_human_actor_ids,
            human_id in self.mission.adopting_human_actor_ids,
            self.constitution.founding_decision_id == self.founding_decision.decision_id,
            self.mission.founding_decision_id == self.founding_decision.decision_id,
            self.retention_policy.founding_decision_id == self.founding_decision.decision_id,
            self.retention_policy.issuer_actor_id == human_id,
            self.founding_role_assignment.actor_id == human_id,
            self.founding_role_assignment.role_id == self.founding_role.role_id,
            self.founding_role_assignment.assigned_by_actor_id == human_id,
            self.founding_decision.initiating_actor_id == human_id,
            self.founding_decision.accountable_decider_actor_id == human_id,
            self.recording_command.initiating_actor_id == human_id,
            self.recording_command.proposed_organization_id == self.organization.organization_id,
            self.recording_command.command_id == self.proposed_founding_events.ordered_events[0].causal_reference,
            self.recording_command.idempotency_key == self.idempotency_key,
            self.envelope.idempotency_key == self.idempotency_key,
            len(grants) == len(self.proposed_founding_events.coverage.authority_grants),
        )
        if not all(checks):
            raise ValueError("bootstrap founding references are incomplete or inconsistent")


@dataclass(frozen=True, slots=True)
class BootstrapProposal:
    request: BootstrapRequest
    proposal_integrity_reference: IntegrityReference


@dataclass(frozen=True, slots=True)
class BootstrapAcceptedDecision:
    proposal: BootstrapProposal
    evaluation_time: datetime
    constitutional_basis_reference: IntegrityReference
    decision_audit_reference: IntegrityReference

    def __post_init__(self) -> None:
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")


@dataclass(frozen=True, slots=True)
class BootstrapRejectedDecision:
    request: BootstrapRequest
    evaluation_time: datetime
    reason_code: ReasonCode
    failed_requirement: str
    safe_detail: str
    audit_reference: IntegrityReference

    def __post_init__(self) -> None:
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        require_nonempty(self.failed_requirement, type(self).__name__, "failed_requirement")
        require_nonempty(self.safe_detail, type(self).__name__, "safe_detail")


@dataclass(frozen=True, slots=True)
class RecordedFoundingEvent:
    event_id: EventId
    event_type: str
    stream_position: int
    integrity_reference: IntegrityReference

    def __post_init__(self) -> None:
        require_nonempty(self.event_type, type(self).__name__, "event_type")
        if self.stream_position <= 0:
            raise ValueError("founding Event stream position must be positive")


@dataclass(frozen=True, slots=True)
class BootstrapCommitted:
    decision: BootstrapAcceptedDecision
    organization_id: OrganizationId
    verified_human_actor_id: ActorId
    governor_role_id: RoleId
    founding_role_assignment_id: RoleAssignmentId
    founding_decision_id: DecisionId
    initial_authority_grant_ids: tuple[AuthorityGrantId, ...]
    recording_command_id: CommandId
    founding_events: tuple[RecordedFoundingEvent, ...]
    audit_record_id: AuditRecordId
    evaluation_time: datetime
    outcome_integrity_reference: IntegrityReference
    genesis_exception_exhausted: bool = True

    def __post_init__(self) -> None:
        request = self.decision.proposal.request
        object.__setattr__(self, "initial_authority_grant_ids", tuple(self.initial_authority_grant_ids))
        events = tuple(self.founding_events)
        object.__setattr__(self, "founding_events", events)
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        required = (
            self.organization_id == request.organization.organization_id,
            self.verified_human_actor_id == request.verified_human.actor_id,
            self.governor_role_id == request.founding_role.role_id,
            self.founding_role_assignment_id == request.founding_role_assignment.role_assignment_id,
            self.founding_decision_id == request.founding_decision.decision_id,
            self.recording_command_id == request.recording_command.command_id,
            len(self.initial_authority_grant_ids) == len(request.initial_authority_grants),
            len(events) == len(request.proposed_founding_events.ordered_events),
            bool(events), self.genesis_exception_exhausted,
        )
        if not all(required):
            raise ValueError("committed bootstrap must be complete and match its accepted proposal")
        positions = tuple(event.stream_position for event in events)
        if positions != tuple(range(positions[0], positions[0] + len(positions))):
            raise ValueError("founding Event positions must be consecutive")
        proposed_types = tuple(event.event_type for event in request.proposed_founding_events.ordered_events)
        if tuple(event.event_type for event in events) != proposed_types:
            raise ValueError("recorded founding Events must preserve proposed semantic order")


@dataclass(frozen=True, slots=True)
class BootstrapPreviouslyAdmitted:
    request: BootstrapRequest
    original_committed: BootstrapCommitted
    original_evaluation_time: datetime
    original_outcome_integrity_reference: IntegrityReference

    def __post_init__(self) -> None:
        require_aware(self.original_evaluation_time, type(self).__name__, "original_evaluation_time")
        original_request = self.original_committed.decision.proposal.request
        if self.request != original_request:
            raise ValueError("previously admitted bootstrap must be an exact request redelivery")
        if self.original_evaluation_time != self.original_committed.evaluation_time:
            raise ValueError("previously admitted bootstrap must preserve evaluation time")


@dataclass(frozen=True, slots=True)
class BootstrapUncertain:
    request: BootstrapRequest
    evaluation_time: datetime
    reason_code: ReasonCode
    quarantine_reference: IntegrityReference
    reconciliation_reference: IntegrityReference
    retry_prohibited: bool = True

    def __post_init__(self) -> None:
        require_aware(self.evaluation_time, type(self).__name__, "evaluation_time")
        if self.reason_code not in {
            ReasonCode.APPEND_OUTCOME_UNCERTAIN,
            ReasonCode.BOOTSTRAP_IDENTITY_QUARANTINED,
        }:
            raise ValueError("uncertain bootstrap requires an uncertainty or quarantine reason")
        if not self.retry_prohibited:
            raise ValueError("uncertain bootstrap must prohibit blind retry")
