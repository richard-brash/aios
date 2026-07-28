"""Deterministic constitutional bootstrap orchestration and replay.

This module is deliberately separate from the Organization-scoped runtime. It
implements only the one-time pre-Organization genesis capability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Protocol

from aios_protocol.bootstrap import (
    BootstrapAcceptedDecision, BootstrapAdmissionBasis, BootstrapCommitted,
    BootstrapPreviouslyAdmitted, BootstrapProposal, BootstrapRejectedDecision,
    BootstrapRequest, BootstrapUncertain, CompetingGenesisRule,
    ConstitutionEstablishment, ExpectedGenesisStream, FoundingAuthorityGrant,
    FoundingDecision, FoundingEventCoverage, FoundingMission,
    FoundingRetentionPolicy, FoundingRole, FoundingRoleAssignment,
    GenesisException, GenesisRecordingCommand, OrganizationGenesisAttributes,
    RecordedFoundingEvent, VerifiedHumanReference,
)
from aios_protocol.commands import EntityReference
from aios_protocol.envelope import EventEnvelope, TrafficMode
from aios_protocol.events import EpistemicStatus, EventRecord
from aios_protocol.identifiers import (
    ActorId, AuditRecordId, CommandId, CorrelationId, EventId,
    IntegrityReference, MessageId, OrganizationId, StreamId,
)
from aios_protocol.presence import NOT_APPLICABLE
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import (
    PAYLOAD_V1, PROTOCOL_V1, RECORD_V1, SPEC_0_0_2, PayloadVersion,
    ProtocolFamilyVersion, RecordTypeVersion, SpecificationVersion,
)

from .clock import Clock
from .idempotency import semantic_logical_fingerprint
from .ids import IdentifierAllocator


REFERENCE_GENESIS_EVENT_TYPES = FrozenMap({
    "organization": "ReferenceGenesis.OrganizationEstablished",
    "human": "ReferenceGenesis.HumanEstablished",
    "constitution": "ReferenceGenesis.ConstitutionEstablished",
    "mission": "ReferenceGenesis.MissionEstablished",
    "jurisdiction": "ReferenceGenesis.JurisdictionEstablished",
    "retention": "ReferenceGenesis.RetentionPolicyEstablished",
    "role": "ReferenceGenesis.GovernorRoleEstablished",
    "assignment": "ReferenceGenesis.RoleAssignmentEstablished",
    "decision": "ReferenceGenesis.FoundingDecisionRecorded",
    "grant": "ReferenceGenesis.AuthorityGrantEstablished",
    "audit": "ReferenceGenesis.AuditRecordEstablished",
})


def genesis_stream_id(organization_id: OrganizationId) -> StreamId:
    """Return the reference stable stream identity; performs no allocation."""
    return StreamId(f"genesis:{organization_id}")


class GenesisComparison(str, Enum):
    NONE = "no_prior_candidate"
    EXACT = "exact_redelivery"
    COMPETING = "competing_candidate"
    COMPLETED = "genesis_completed"
    UNCERTAIN = "outcome_uncertain"


def compare_genesis_candidates(left: BootstrapRequest, right: BootstrapRequest) -> GenesisComparison:
    """Symmetric comparison under the declared reject-material-conflict rule."""
    if left.competing_genesis_rule is not CompetingGenesisRule.REJECT_MATERIAL_CONFLICT:
        return GenesisComparison.COMPETING
    if right.competing_genesis_rule is not left.competing_genesis_rule:
        return GenesisComparison.COMPETING
    return GenesisComparison.EXACT if left == right else GenesisComparison.COMPETING


@dataclass(frozen=True, slots=True)
class BootstrapStructuralRejected:
    reason_code: ReasonCode
    failed_requirement: str
    safe_detail: str


@dataclass(frozen=True, slots=True)
class ConstitutionalEvaluationAccepted:
    proposal: BootstrapProposal
    decision: BootstrapAcceptedDecision
    audit_facts: FrozenMap


@dataclass(frozen=True, slots=True)
class ConstitutionalEvaluationRejected:
    decision: BootstrapRejectedDecision
    audit_facts: FrozenMap = field(default_factory=FrozenMap)

    def __post_init__(self) -> None:
        object.__setattr__(self, "audit_facts", FrozenMap(self.audit_facts))


ConstitutionalEvaluation = ConstitutionalEvaluationAccepted | ConstitutionalEvaluationRejected


class BootstrapConstitutionalEvaluator(Protocol):
    def evaluate(self, request: BootstrapRequest, evaluation_time: datetime) -> ConstitutionalEvaluation: ...


_COVERAGE_PAYLOAD_FIELDS = {
    "organization": "organization",
    "human_actor": "verified_human",
    "constitution": "constitution",
    "mission": "mission",
    "jurisdiction": "jurisdiction_scope",
    "retention_policy": "retention_policy",
    "governor_role": "founding_role",
    "role_assignment": "founding_role_assignment",
    "founding_decision": "founding_decision",
    "audit_record": "audit_record_id",
}


class ReferenceBootstrapConstitutionalEvaluator:
    """Pure fail-closed evaluator for only the specified genesis invariants."""

    def evaluate(self, request: BootstrapRequest, evaluation_time: datetime) -> ConstitutionalEvaluation:
        rejection = self._first_rejection(request)
        if rejection is not None:
            reason, requirement, detail = rejection
            decision = BootstrapRejectedDecision(
                request, evaluation_time, reason, requirement, detail,
                request.proposed_audit_integrity_reference,
            )
            return ConstitutionalEvaluationRejected(
                decision, FrozenMap({"failed_requirement": requirement}),
            )
        proposal = BootstrapProposal(request, request.request_integrity_reference)
        decision = BootstrapAcceptedDecision(
            proposal, evaluation_time, request.constitution.source_integrity_reference,
            request.proposed_audit_integrity_reference,
        )
        return ConstitutionalEvaluationAccepted(
            proposal, decision,
            FrozenMap({
                "admission_basis": request.admission_basis.value,
                "accountable_decider": request.verified_human.actor_id,
                "duty": request.founding_decision.duty_reference,
                "coverage_keys": tuple(event.proposal_key for event in request.proposed_founding_events.ordered_events),
            }),
        )

    def _first_rejection(self, request: BootstrapRequest):
        envelope = request.envelope
        if (
            envelope.traffic_mode is not TrafficMode.PRE_ORGANIZATION
            or envelope.schema_version != RECORD_V1
            or request.protocol_family_version != PROTOCOL_V1
            or request.payload_version != PAYLOAD_V1
            or request.specification_version != SPEC_0_0_2
            or request.recording_command.schema_version != RECORD_V1
            or request.recording_command.payload_version != PAYLOAD_V1
        ):
            return ReasonCode.VER_UNSUPPORTED, "protocol_version", "bootstrap version is unsupported"
        if envelope.payload_type != "BootstrapRequest" or "genesis" not in envelope.classification.lower():
            return ReasonCode.BOOTSTRAP_GENESIS_TYPE_INVALID, "genesis_type", "bootstrap type is not reserved genesis"
        if (
            request.admission_basis is not BootstrapAdmissionBasis.CONSTITUTION_DIRECT
            or request.genesis_exception is not GenesisException.SOLE_PREEXISTING_AUTHORITY_EXCEPTION
        ):
            return ReasonCode.AUTH_MISSING, "founding_authority", "direct constitutional founding basis is missing"
        if request.expected_stream not in {ExpectedGenesisStream.NONEXISTENT, ExpectedGenesisStream.EMPTY}:
            return ReasonCode.STREAM_CONCURRENCY_CONFLICT, "expected_stream", "genesis requires a nonexistent or empty stream"
        if request.genesis_stream_id != genesis_stream_id(request.organization.organization_id):
            return ReasonCode.ORG_BOUNDARY_VIOLATION, "genesis_stream", "genesis stream identity is inconsistent"
        human_id = request.verified_human.actor_id
        if (
            request.verified_human.identity_kind != "human"
            or not request.verified_human.verification_reference
            or request.founding_decision.accountable_decider_actor_id != human_id
        ):
            return ReasonCode.DECISION_ACCOUNTABLE_DECIDER_INVALID, "verified_human", "eligible founding Human is not proven"
        assignment = request.founding_role_assignment
        if (
            assignment.actor_id != human_id
            or assignment.role_id != request.founding_role.role_id
            or assignment.assigned_by_actor_id != human_id
            or assignment.lifecycle_state != "active"
        ):
            return ReasonCode.BOOTSTRAP_INCOMPLETE, "founding_role_assignment", "founding Role Assignment is incomplete"
        duty = request.founding_decision.duty_reference
        if (
            duty.accountable_actor_id != human_id
            or duty != request.recording_command.duty_reference
            or not all((duty.duty_type, duty.governing_mandate_reference, duty.scope,
                        duty.review_or_completion_condition))
        ):
            return ReasonCode.WORK_ROOT_INCOMPLETE, "constitutional_duty", "constitutional duty reference is incomplete"
        org = request.organization
        if (
            not org.legal_or_operating_name or not org.jurisdiction_scope
            or org.mission_record_id != request.mission.mission_record_id
            or org.retention_policy_id != request.retention_policy.policy_id
            or org.constitution_policy_id != request.constitution.constitution_policy_id
        ):
            return ReasonCode.BOOTSTRAP_INCOMPLETE, "organization_attributes", "required founding attributes are incomplete"
        if not request.initial_authority_grants or any(
            grant.issuer_actor_id != human_id or grant.recipient_actor_id != human_id
            for grant in request.initial_authority_grants
        ):
            return ReasonCode.AUTH_MISSING, "initial_authority_grants", "founding authority evidence is incomplete"
        coverage_error = self._validate_coverage(request)
        if coverage_error is not None:
            return ReasonCode.BOOTSTRAP_INCOMPLETE, "founding_event_coverage", coverage_error
        return None

    @staticmethod
    def _validate_coverage(request: BootstrapRequest) -> str | None:
        event_by_key = {event.proposal_key: event for event in request.proposed_founding_events.ordered_events}
        coverage = request.proposed_founding_events.coverage
        expected = {
            "organization": request.organization,
            "human_actor": request.verified_human,
            "constitution": request.constitution,
            "mission": request.mission,
            "jurisdiction": request.organization.jurisdiction_scope,
            "retention_policy": request.retention_policy,
            "governor_role": request.founding_role,
            "role_assignment": request.founding_role_assignment,
            "founding_decision": request.founding_decision,
            "audit_record": request.proposed_audit_record_id,
        }
        covered_keys = {
            *(getattr(coverage, name) for name in _COVERAGE_PAYLOAD_FIELDS),
            *coverage.authority_grants,
        }
        if set(event_by_key) != covered_keys:
            return "founding proposal contains an unreferenced or missing Event"
        allowed_payload_fields = set(_COVERAGE_PAYLOAD_FIELDS.values()) | {"authority_grant"}
        if any(set(proposal.payload) - allowed_payload_fields for proposal in event_by_key.values()):
            return "founding proposal contains a non-genesis payload field"
        for coverage_name, payload_field in _COVERAGE_PAYLOAD_FIELDS.items():
            proposal = event_by_key.get(getattr(coverage, coverage_name))
            if proposal is None or proposal.payload.get(payload_field) != expected[coverage_name]:
                return f"founding Event does not establish {coverage_name}"
        if len(coverage.authority_grants) != len(request.initial_authority_grants):
            return "founding Authority Grant Event coverage is incomplete"
        for key, grant in zip(coverage.authority_grants, request.initial_authority_grants):
            proposal = event_by_key.get(key)
            if proposal is None or proposal.payload.get("authority_grant") != grant:
                return "founding Authority Grant Event is incomplete"
        command_ids = {event.causal_reference for event in event_by_key.values()}
        if command_ids != {request.recording_command.command_id}:
            return "founding Event causation is inconsistent"
        return None


@dataclass(frozen=True, slots=True)
class CommittedFoundingEventEvidence:
    """History-owned declaration of one semantically covered founding Event."""

    proposal_key: str
    event_type: str
    event_version: RecordTypeVersion
    payload_version: PayloadVersion
    initiating_actor_id: ActorId
    causal_reference: CommandId
    reserved_genesis_classification: str
    proposal_payload_fingerprint: str


@dataclass(frozen=True, slots=True)
class CommittedGenesisEvidence:
    """Minimum immutable evidence needed to validate genesis from history alone."""

    protocol_family_version: ProtocolFamilyVersion
    payload_version: PayloadVersion
    specification_version: SpecificationVersion
    admission_basis: BootstrapAdmissionBasis
    genesis_exception: GenesisException
    bootstrap_message_id: MessageId
    request_integrity_reference: IntegrityReference
    proposal_integrity_reference: IntegrityReference
    constitutional_basis_reference: IntegrityReference
    decision_audit_reference: IntegrityReference
    proposed_audit_integrity_reference: IntegrityReference
    recording_command: GenesisRecordingCommand
    coverage: FoundingEventCoverage
    event_declarations: tuple[CommittedFoundingEventEvidence, ...]
    evaluation_time: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_declarations", tuple(self.event_declarations))

    @classmethod
    def from_commit(
        cls, request: BootstrapRequest, decision: BootstrapAcceptedDecision,
        evaluation_time: datetime,
    ) -> "CommittedGenesisEvidence":
        return cls(
            request.protocol_family_version, request.payload_version,
            request.specification_version, request.admission_basis,
            request.genesis_exception, request.envelope.message_id,
            request.request_integrity_reference,
            decision.proposal.proposal_integrity_reference,
            decision.constitutional_basis_reference,
            decision.decision_audit_reference,
            request.proposed_audit_integrity_reference,
            request.recording_command, request.proposed_founding_events.coverage,
            tuple(
                CommittedFoundingEventEvidence(
                    proposal.proposal_key, proposal.event_type,
                    proposal.event_version, proposal.payload_version,
                    proposal.initiating_actor_id, proposal.causal_reference,
                    proposal.reserved_genesis_classification,
                    semantic_logical_fingerprint(proposal.payload),
                )
                for proposal in request.proposed_founding_events.ordered_events
            ),
            evaluation_time,
        )


@dataclass(frozen=True, slots=True)
class GenesisAppendCommitted:
    outcome: BootstrapCommitted
    events: tuple[EventRecord, ...]


@dataclass(frozen=True, slots=True)
class GenesisAppendPreviouslyAdmitted:
    outcome: BootstrapPreviouslyAdmitted


@dataclass(frozen=True, slots=True)
class GenesisAppendRejected:
    reason_code: ReasonCode
    failed_requirement: str
    safe_detail: str


@dataclass(frozen=True, slots=True)
class GenesisAppendUncertain:
    outcome: BootstrapUncertain


GenesisAppendResult = (
    GenesisAppendCommitted | GenesisAppendPreviouslyAdmitted
    | GenesisAppendRejected | GenesisAppendUncertain
)


GenesisTransactionBuilder = Callable[[], tuple[tuple[EventRecord, ...], BootstrapCommitted]]


class GenesisStore(Protocol):
    def append_genesis(
        self, *, request: BootstrapRequest, evaluation_time: datetime,
        accepted_decision: BootstrapAcceptedDecision, expected_prior_position: int,
        build_transaction: GenesisTransactionBuilder,
    ) -> GenesisAppendResult: ...

    def read(self, stream_id: StreamId) -> tuple[EventRecord, ...]: ...


BootstrapRuntimeResult = (
    BootstrapStructuralRejected | BootstrapRejectedDecision | BootstrapCommitted
    | BootstrapPreviouslyAdmitted | BootstrapUncertain
)


class ConstitutionalBootstrapRuntime:
    def __init__(self, *, clock: Clock, identifiers: IdentifierAllocator,
                 evaluator: BootstrapConstitutionalEvaluator, store: GenesisStore) -> None:
        self._clock = clock
        self._identifiers = identifiers
        self._evaluator = evaluator
        self._store = store

    def execute(self, submission: object) -> BootstrapRuntimeResult:
        if type(submission) is not BootstrapRequest:
            return BootstrapStructuralRejected(
                ReasonCode.INPUT_MALFORMED, "structure", "bootstrap structure is invalid",
            )
        try:
            evaluation_time = self._clock.evaluation_time()
        except Exception:
            return BootstrapStructuralRejected(
                ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE, "evaluation_time",
                "authoritative evaluation time is unavailable",
            )
        if (
            not isinstance(evaluation_time, datetime) or evaluation_time.tzinfo is None
            or evaluation_time.utcoffset() is None
        ):
            return BootstrapStructuralRejected(
                ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE, "evaluation_time",
                "authoritative evaluation time is unavailable",
            )
        try:
            evaluated = self._evaluator.evaluate(submission, evaluation_time)
        except Exception:
            return BootstrapRejectedDecision(
                submission, evaluation_time, ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
                "constitutional_evaluation", "constitutional evaluation is unavailable",
                submission.proposed_audit_integrity_reference,
            )
        if type(evaluated) is ConstitutionalEvaluationRejected:
            return evaluated.decision
        if type(evaluated) is not ConstitutionalEvaluationAccepted:
            return BootstrapRejectedDecision(
                submission, evaluation_time, ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
                "constitutional_evaluation", "constitutional evaluation is unavailable",
                submission.proposed_audit_integrity_reference,
            )

        def build_transaction() -> tuple[tuple[EventRecord, ...], BootstrapCommitted]:
            events = self._materialize_events(submission, evaluated.decision, evaluation_time)
            recorded = tuple(
                RecordedFoundingEvent(
                    event.event_id, event.event_type, event.envelope.stream_position,
                    event.integrity_reference,
                )
                for event in events
            )
            outcome = BootstrapCommitted(
                evaluated.decision, submission.organization.organization_id,
                submission.verified_human.actor_id, submission.founding_role.role_id,
                submission.founding_role_assignment.role_assignment_id,
                submission.founding_decision.decision_id,
                tuple(grant.authority_grant_id for grant in submission.initial_authority_grants),
                submission.recording_command.command_id, recorded,
                submission.proposed_audit_record_id, evaluation_time,
                IntegrityReference(f"genesis-outcome:{submission.request_integrity_reference}"),
            )
            return events, outcome

        try:
            appended = self._store.append_genesis(
                request=submission, evaluation_time=evaluation_time,
                accepted_decision=evaluated.decision,
                expected_prior_position=0, build_transaction=build_transaction,
            )
        except Exception:
            return BootstrapRejectedDecision(
                submission, evaluation_time, ReasonCode.APPEND_FAILED, "append",
                "genesis append is unavailable",
                submission.proposed_audit_integrity_reference,
            )
        if type(appended) is GenesisAppendCommitted:
            return appended.outcome
        if type(appended) is GenesisAppendPreviouslyAdmitted:
            return appended.outcome
        if type(appended) is GenesisAppendUncertain:
            return appended.outcome
        if type(appended) is GenesisAppendRejected:
            return BootstrapRejectedDecision(
                submission, evaluation_time, appended.reason_code,
                appended.failed_requirement, appended.safe_detail,
                submission.proposed_audit_integrity_reference,
            )
        return BootstrapRejectedDecision(
            submission, evaluation_time, ReasonCode.APPEND_FAILED, "append",
            "genesis append returned an invalid result",
            submission.proposed_audit_integrity_reference,
        )

    def _materialize_events(
        self, request: BootstrapRequest, decision: BootstrapAcceptedDecision,
        evaluation_time: datetime,
    ) -> tuple[EventRecord, ...]:
        records = []
        committed_evidence = CommittedGenesisEvidence.from_commit(
            request, decision, evaluation_time)
        for position, proposal in enumerate(request.proposed_founding_events.ordered_events, 1):
            event_id = self._identifiers.event_id()
            integrity = IntegrityReference(f"genesis-event:{event_id}")
            envelope = EventEnvelope(
                MessageId(f"genesis-message:{event_id}"), proposal.event_type,
                request.organization.organization_id, request.verified_human.actor_id,
                request.recording_command.command_id, request.envelope.correlation_id,
                evaluation_time, request.genesis_stream_id, position,
                request.envelope.classification, integrity,
            )
            payload = FrozenMap({
                "proposal_key": proposal.proposal_key,
                "proposal_payload": proposal.payload,
                "bootstrap_request_integrity": request.request_integrity_reference,
                "bootstrap_message_id": request.envelope.message_id,
                "committed_genesis_evidence": committed_evidence,
                "genesis_exception_exhausted": position == len(request.proposed_founding_events.ordered_events),
            })
            records.append(EventRecord(
                envelope, event_id, proposal.event_type, proposal.event_version, (),
                f"command:{request.recording_command.command_id}", evaluation_time,
                (EntityReference("Organization", str(request.organization.organization_id), 0),),
                EpistemicStatus.DETERMINISTIC, NOT_APPLICABLE,
                request.founding_decision.duty_reference, FrozenMap(), FrozenMap(), FrozenMap(),
                request.proposed_audit_record_id, integrity, result="recorded", payload=payload,
            ))
        return tuple(records)


@dataclass(frozen=True, slots=True)
class UnfoundedGenesisState:
    genesis_occurred: bool = False


@dataclass(frozen=True, slots=True)
class FoundedOrganizationState:
    organization: OrganizationGenesisAttributes
    verified_human: VerifiedHumanReference
    constitution: ConstitutionEstablishment
    mission: FoundingMission
    jurisdiction_scope: str
    retention_policy: FoundingRetentionPolicy
    founding_role: FoundingRole
    founding_role_assignment: FoundingRoleAssignment
    founding_decision: FoundingDecision
    initial_authority_grants: tuple[FoundingAuthorityGrant, ...]
    audit_record_id: AuditRecordId
    recording_command_id: CommandId
    bootstrap_request_integrity: IntegrityReference
    founding_event_ids: tuple[EventId, ...]
    genesis_completed: bool = True


GenesisState = UnfoundedGenesisState | FoundedOrganizationState


def replay_genesis(events: tuple[EventRecord, ...]) -> GenesisState:
    """Reconstruct founded state from recorded Events only, without effects."""
    ordered = tuple(events)
    if not ordered:
        return UnfoundedGenesisState()
    if type(ordered[0]) is not EventRecord:
        raise ValueError("genesis replay contains a non-Event record")
    organization_id = ordered[0].envelope.organization_id
    stream_id = genesis_stream_id(organization_id)
    facts: dict[str, object] = {}
    fact_proposal_keys: dict[str, str] = {}
    grants: list[FoundingAuthorityGrant] = []
    grant_proposal_keys: list[str] = []
    event_ids: list[EventId] = []
    audit_id = ordered[0].audit_record_id
    recording_command_id = ordered[0].envelope.recording_command_id
    request_integrity = ordered[0].payload.get("bootstrap_request_integrity")
    committed_evidence = ordered[0].payload.get("committed_genesis_evidence")
    if type(committed_evidence) is not CommittedGenesisEvidence:
        raise ValueError("genesis history lacks committed constitutional evidence")
    declarations = committed_evidence.event_declarations
    if len(declarations) != len(ordered):
        raise ValueError("genesis history does not match declared semantic coverage")
    completed_markers = 0
    seen_proposal_keys = set()
    for expected_position, (event, declaration) in enumerate(zip(ordered, declarations), 1):
        if type(event) is not EventRecord:
            raise ValueError("genesis replay contains a non-Event record")
        if (
            event.envelope.organization_id != organization_id
            or event.envelope.stream_id != stream_id
            or event.envelope.stream_position != expected_position
            or event.envelope.schema_version != RECORD_V1
            or event.envelope.traffic_mode is not TrafficMode.LIVE
            or event.envelope.message_type != event.event_type
            or event.event_version != RECORD_V1
            or "genesis" not in event.envelope.classification.lower()
            or event.audit_record_id != audit_id
            or event.envelope.recording_command_id != recording_command_id
            or event.payload.get("bootstrap_request_integrity") != request_integrity
            or event.payload.get("bootstrap_message_id") != committed_evidence.bootstrap_message_id
            or event.payload.get("committed_genesis_evidence") != committed_evidence
            or event.envelope.evaluation_time != committed_evidence.evaluation_time
            or event.occurred_at != committed_evidence.evaluation_time
            or event.envelope.correlation_id != committed_evidence.recording_command.correlation_id
            or event.envelope.initiating_actor_id != declaration.initiating_actor_id
            or event.envelope.classification != declaration.reserved_genesis_classification
            or event.event_type != declaration.event_type
            or event.event_version != declaration.event_version
            or declaration.payload_version != PAYLOAD_V1
            or event.envelope.recording_command_id != declaration.causal_reference
            or event.causal_reference != f"command:{declaration.causal_reference}"
            or event.envelope.integrity_reference != event.integrity_reference
            or event.epistemic_status is not EpistemicStatus.DETERMINISTIC
            or event.result != "recorded"
            or event.entity_references != (
                EntityReference("Organization", str(organization_id), 0),)
        ):
            raise ValueError("genesis history violates stream, ordering, or audit invariants")
        if event.event_id in event_ids:
            raise ValueError("genesis history repeats Event identity")
        event_ids.append(event.event_id)
        proposal_key = event.payload.get("proposal_key")
        if proposal_key != declaration.proposal_key or proposal_key in seen_proposal_keys:
            raise ValueError("genesis history violates declared semantic ordering")
        seen_proposal_keys.add(proposal_key)
        proposal_payload = event.payload.get("proposal_payload")
        if not isinstance(proposal_payload, FrozenMap):
            raise ValueError("genesis Event lacks immutable proposal payload")
        if semantic_logical_fingerprint(proposal_payload) != declaration.proposal_payload_fingerprint:
            raise ValueError("genesis Event founding facts do not match committed evidence")
        allowed_payload_fields = set(_COVERAGE_PAYLOAD_FIELDS.values()) | {"authority_grant"}
        if not proposal_payload or set(proposal_payload) - allowed_payload_fields:
            raise ValueError("genesis Event contains unsupported founding facts")
        for name in (
            "organization", "verified_human", "constitution", "mission", "jurisdiction_scope",
            "retention_policy", "founding_role", "founding_role_assignment", "founding_decision",
            "audit_record_id",
        ):
            if name in proposal_payload:
                if name in facts:
                    raise ValueError(f"genesis history establishes {name} more than once")
                facts[name] = proposal_payload[name]
                fact_proposal_keys[name] = proposal_key
        if "authority_grant" in proposal_payload:
            grants.append(proposal_payload["authority_grant"])
            grant_proposal_keys.append(proposal_key)
        if event.payload.get("genesis_exception_exhausted") is True:
            completed_markers += 1
            if expected_position != len(ordered):
                raise ValueError("genesis completion marker is not terminal")
    required = {
        "organization", "verified_human", "constitution", "mission", "jurisdiction_scope",
        "retention_policy", "founding_role", "founding_role_assignment", "founding_decision",
        "audit_record_id",
    }
    if set(facts) != required or not grants or completed_markers != 1:
        raise ValueError("genesis history is incomplete or structurally impossible")
    if (
        not isinstance(request_integrity, IntegrityReference)
        or request_integrity != committed_evidence.request_integrity_reference
    ):
        raise ValueError("genesis history lacks request integrity")
    organization = facts["organization"]
    if not isinstance(organization, OrganizationGenesisAttributes) or organization.organization_id != organization_id:
        raise ValueError("genesis Organization identity is inconsistent")
    typed = (
        (facts["verified_human"], VerifiedHumanReference),
        (facts["constitution"], ConstitutionEstablishment),
        (facts["mission"], FoundingMission),
        (facts["retention_policy"], FoundingRetentionPolicy),
        (facts["founding_role"], FoundingRole),
        (facts["founding_role_assignment"], FoundingRoleAssignment),
        (facts["founding_decision"], FoundingDecision),
    )
    if any(not isinstance(value, expected_type) for value, expected_type in typed):
        raise ValueError("genesis history contains an invalid founding fact type")
    if any(not isinstance(grant, FoundingAuthorityGrant) for grant in grants):
        raise ValueError("genesis history contains an invalid Authority Grant")
    _validate_committed_genesis(
        committed_evidence, organization_id, audit_id, facts, tuple(grants),
        seen_proposal_keys, fact_proposal_keys, tuple(grant_proposal_keys),
    )
    return FoundedOrganizationState(
        organization, facts["verified_human"], facts["constitution"], facts["mission"],
        facts["jurisdiction_scope"], facts["retention_policy"], facts["founding_role"],
        facts["founding_role_assignment"], facts["founding_decision"], tuple(grants),
        facts["audit_record_id"], recording_command_id, request_integrity, tuple(event_ids), True,
    )


def _validate_committed_genesis(
    evidence: CommittedGenesisEvidence, organization_id: OrganizationId,
    audit_id: AuditRecordId, facts: dict[str, object],
    grants: tuple[FoundingAuthorityGrant, ...], seen_proposal_keys: set[str],
    fact_proposal_keys: dict[str, str], grant_proposal_keys: tuple[str, ...],
) -> None:
    """Validate the same constitutional relationships using history-owned facts."""
    if (
        evidence.protocol_family_version != PROTOCOL_V1
        or evidence.payload_version != PAYLOAD_V1
        or evidence.specification_version != SPEC_0_0_2
        or evidence.admission_basis is not BootstrapAdmissionBasis.CONSTITUTION_DIRECT
        or evidence.genesis_exception is not GenesisException.SOLE_PREEXISTING_AUTHORITY_EXCEPTION
        or not isinstance(evidence.proposal_integrity_reference, IntegrityReference)
        or not isinstance(evidence.constitutional_basis_reference, IntegrityReference)
        or not isinstance(evidence.decision_audit_reference, IntegrityReference)
        or not isinstance(evidence.proposed_audit_integrity_reference, IntegrityReference)
        or evidence.proposal_integrity_reference != evidence.request_integrity_reference
        or evidence.decision_audit_reference != evidence.proposed_audit_integrity_reference
    ):
        raise ValueError("genesis history lacks supported constitutional admission evidence")
    command = evidence.recording_command
    if (
        type(command) is not GenesisRecordingCommand
        or command.command_type != "RecordConstitutionalGenesis"
        or command.schema_version != RECORD_V1
        or command.payload_version != PAYLOAD_V1
        or {declaration.causal_reference for declaration in evidence.event_declarations} != {command.command_id}
        or command.proposed_organization_id != organization_id
        or "genesis" not in command.reserved_genesis_classification.lower()
    ):
        raise ValueError("genesis recording Command evidence is inconsistent")
    coverage = evidence.coverage
    covered_keys = {
        *(getattr(coverage, name) for name in _COVERAGE_PAYLOAD_FIELDS),
        *coverage.authority_grants,
    }
    if covered_keys != seen_proposal_keys or len(covered_keys) != len(evidence.event_declarations):
        raise ValueError("genesis semantic coverage is incomplete or duplicated")
    for coverage_name, payload_field in _COVERAGE_PAYLOAD_FIELDS.items():
        if fact_proposal_keys.get(payload_field) != getattr(coverage, coverage_name):
            raise ValueError("genesis semantic coverage does not bind its founding fact")
    if grant_proposal_keys != coverage.authority_grants:
        raise ValueError("genesis Authority Grant coverage ordering is inconsistent")

    organization = facts["organization"]
    human = facts["verified_human"]
    constitution = facts["constitution"]
    mission = facts["mission"]
    retention = facts["retention_policy"]
    role = facts["founding_role"]
    assignment = facts["founding_role_assignment"]
    decision = facts["founding_decision"]
    if (
        type(human) is not VerifiedHumanReference
        or human.identity_kind != "human"
        or not human.relationship_to_organization
        or not isinstance(human.human_identity_reference, IntegrityReference)
        or not isinstance(human.verification_reference, IntegrityReference)
        or human.actor_id not in organization.governing_human_actor_ids
        or command.initiating_actor_id != human.actor_id
    ):
        raise ValueError("genesis founding Human evidence is inconsistent")
    if (
        not organization.legal_or_operating_name
        or facts["jurisdiction_scope"] != organization.jurisdiction_scope
        or organization.constitution_policy_id != constitution.constitution_policy_id
        or organization.mission_record_id != mission.mission_record_id
        or organization.retention_policy_id != retention.policy_id
    ):
        raise ValueError("genesis Organization attributes are inconsistent")
    if (
        human.actor_id not in constitution.adopting_human_actor_ids
        or constitution.founding_decision_id != decision.decision_id
        or evidence.constitutional_basis_reference != constitution.source_integrity_reference
        or not constitution.constitutional_version
        or constitution.effective_at.tzinfo is None
        or human.actor_id not in mission.adopting_human_actor_ids
        or mission.founding_decision_id != decision.decision_id
        or not mission.statement or not mission.success_or_review_indicators
        or mission.effective_at.tzinfo is None
        or retention.issuer_actor_id != human.actor_id
        or retention.founding_decision_id != decision.decision_id
        or not retention.rule_set
        or retention.effective_at.tzinfo is None
    ):
        raise ValueError("genesis Constitution, Mission, or Policy evidence is inconsistent")
    if (
        assignment.actor_id != human.actor_id
        or assignment.assigned_by_actor_id != human.actor_id
        or assignment.role_id != role.role_id
        or assignment.lifecycle_state != "active"
        or not role.duties or not role.eligible_capability_references
        or not role.eligible_authority_scope
        or not role.name or not role.escalation_path
    ):
        raise ValueError("genesis founding Role evidence is inconsistent")
    duty = decision.duty_reference
    if (
        decision.initiating_actor_id != human.actor_id
        or decision.accountable_decider_actor_id != human.actor_id
        or decision.technical_recorder_actor_id != human.actor_id
        or command.duty_reference != duty
        or duty.accountable_actor_id != human.actor_id
        or not all((duty.duty_type, duty.governing_mandate_reference, duty.scope,
                    duty.review_or_completion_condition))
        or not decision.authority_basis or not decision.evidence_references
        or not decision.outcome or not decision.follow_up_review
        or not decision.alternatives_considered
    ):
        raise ValueError("genesis founding Decision evidence is inconsistent")
    if (
        not grants
        or len(grants) != len(coverage.authority_grants)
        or any(
            grant.issuer_actor_id != human.actor_id
            or grant.recipient_actor_id != human.actor_id
            or not grant.permitted_actions
            or not grant.purpose
            or not grant.authority_level
            or not grant.resource_scope
            or grant.effective_at.tzinfo is None
            or not grant.review_or_expiry_condition
            for grant in grants
        )
    ):
        raise ValueError("genesis initial Authority Grant evidence is inconsistent")
    if facts["audit_record_id"] != audit_id:
        raise ValueError("genesis audit evidence is inconsistent")
