"""Minimal deterministic kernel runtime contracts and orchestration.

This module is capability-neutral. Handlers propose domain Events; the runtime
owns validation order, authoritative metadata, append, and fail-closed results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Generic, Protocol, TypeVar

from aios_protocol.admission import (
    AdmissionClaim, AdmissionDenied, AdmissionEstablished, AdmissionGate,
)
from aios_protocol.commands import CommandSubmission, EntityReference, WorkRoot
from aios_protocol.envelope import EventEnvelope, TRUSTED_ENVELOPE_KEYS, TrafficMode
from aios_protocol.events import EpistemicStatus, EventRecord
from aios_protocol.identifiers import (
    ActorId, AuditRecordId, CommandId, EventId, IntegrityReference, MessageId, OrganizationId,
    StreamId,
)
from aios_protocol.presence import NOT_APPLICABLE
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap, ensure_no_keys
from aios_protocol.versions import RecordTypeVersion, RECORD_V1

from .clock import Clock
from .admission_boundary import RecordingBoundaryResolver
from .idempotency import (
    IdempotencyInspection, IdempotencyScope, IdempotencyState,
    semantic_logical_fingerprint,
)
from .ids import IdentifierAllocator


@dataclass(frozen=True, slots=True)
class RuntimeCommand:
    """Canonical protocol Command plus its asserted stream precondition."""

    submission: CommandSubmission
    expected_stream_position: int

    def __post_init__(self) -> None:
        if type(self.submission) is not CommandSubmission:
            raise TypeError("submission must be CommandSubmission")
        if type(self.expected_stream_position) is not int or self.expected_stream_position < 0:
            raise ValueError("expected_stream_position cannot be negative")


@dataclass(frozen=True, slots=True)
class DomainEventProposal:
    """A handler's immutable semantic proposal without authoritative metadata."""

    event_type: str
    event_version: RecordTypeVersion
    payload: FrozenMap = field(default_factory=FrozenMap)
    projection_effects: FrozenMap = field(default_factory=FrozenMap)
    entity_references: tuple[EntityReference, ...] = ()
    work_root: WorkRoot | None = None
    causal_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.event_type:
            raise ValueError("event_type must be nonempty")
        if type(self.event_version) is not RecordTypeVersion:
            raise TypeError("event_version must be RecordTypeVersion")
        object.__setattr__(self,"payload",FrozenMap(self.payload))
        object.__setattr__(self,"projection_effects",FrozenMap(self.projection_effects))
        object.__setattr__(self, "entity_references", tuple(self.entity_references))
        ensure_no_keys(self.payload,TRUSTED_ENVELOPE_KEYS | {"event_id","event_type"},type(self).__name__)


@dataclass(frozen=True, slots=True)
class HandlerAccepted:
    events: tuple[DomainEventProposal, ...]
    audit_facts: FrozenMap = field(default_factory=FrozenMap)

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))
        if not self.events:
            raise ValueError("accepted handling requires at least one domain Event")
        if any(type(event) is not DomainEventProposal for event in self.events):
            raise TypeError("handler Events must be DomainEventProposal values")
        object.__setattr__(self,"audit_facts",FrozenMap(self.audit_facts))


@dataclass(frozen=True, slots=True)
class HandlerRejected:
    reason_code: ReasonCode
    safe_detail: str
    audit_facts: FrozenMap = field(default_factory=FrozenMap)

    def __post_init__(self) -> None:
        object.__setattr__(self,"audit_facts",FrozenMap(self.audit_facts))


HandlerResult = HandlerAccepted | HandlerRejected


@dataclass(frozen=True, slots=True)
class HandlerContext:
    command: RuntimeCommand
    prior_events: tuple[EventRecord, ...]
    evaluation_time: datetime
    organization_id: OrganizationId
    initiating_actor_id: ActorId

    def __post_init__(self) -> None:
        object.__setattr__(self,"prior_events",tuple(self.prior_events))


class CommandHandler(Protocol):
    operation_type: str
    operation_version: RecordTypeVersion

    def validate(self, command: RuntimeCommand) -> HandlerRejected | None: ...
    def handle(self, context: HandlerContext) -> HandlerResult: ...


@dataclass(frozen=True, slots=True)
class ProcessingAllowed:
    audit_facts: FrozenMap = field(default_factory=FrozenMap)

    def __post_init__(self) -> None:
        object.__setattr__(self,"audit_facts",FrozenMap(self.audit_facts))


@dataclass(frozen=True, slots=True)
class ProcessingDenied:
    reason_code: ReasonCode
    failed_gate: str
    safe_detail: str
    audit_facts: FrozenMap = field(default_factory=FrozenMap)

    def __post_init__(self) -> None:
        object.__setattr__(self,"audit_facts",FrozenMap(self.audit_facts))


ProcessingEvaluation = ProcessingAllowed | ProcessingDenied


class ProcessingEvaluator(Protocol):
    """Boundary for the complete required governance evaluation."""

    def evaluate(self, context: "AdmittedCommandContext") -> ProcessingEvaluation: ...


@dataclass(frozen=True, slots=True)
class AdmittedCommandContext:
    """Trusted attribution context consumed by governance, never by handlers."""

    command: RuntimeCommand
    admission: AdmissionEstablished
    prior_events: tuple[EventRecord, ...]
    evaluation_time: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "prior_events", tuple(self.prior_events))


@dataclass(frozen=True, slots=True)
class AdmissionEvidenceSnapshot:
    """Immutable admission proof retained by authoritative ordinary audit."""

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
    schema_version: RecordTypeVersion

    def __post_init__(self) -> None:
        for name, expected in (
            ("claim_message_id",MessageId),("command_id",CommandId),
            ("organization_id",OrganizationId),("initiating_actor_id",ActorId),
            ("organization_genesis_reference",IntegrityReference),
            ("actor_identity_reference",IntegrityReference),
            ("invocation_proof_reference",IntegrityReference),
            ("admission_mechanism_reference",IntegrityReference),
            ("admission_mechanism_version",RecordTypeVersion),
            ("schema_version",RecordTypeVersion),
        ):
            if type(getattr(self,name)) is not expected:
                raise TypeError(f"{name} must be {expected.__name__}")
        evidence=tuple(self.authentication_evidence_references)
        if not evidence or any(type(reference) is not IntegrityReference for reference in evidence):
            raise ValueError("authentication evidence must contain immutable references")
        object.__setattr__(
            self,"authentication_evidence_references",evidence,
        )

    @classmethod
    def from_established(cls, admission: AdmissionEstablished) -> "AdmissionEvidenceSnapshot":
        if type(admission) is not AdmissionEstablished:
            raise TypeError("audit admission evidence requires AdmissionEstablished")
        return cls(
            admission.claim_message_id,admission.command_id,
            admission.organization_id,admission.initiating_actor_id,
            admission.organization_genesis_reference,admission.actor_identity_reference,
            admission.invocation_proof_reference,
            admission.authentication_evidence_references,
            admission.admission_mechanism_reference,
            admission.admission_mechanism_version,admission.schema_version,
        )


@dataclass(frozen=True, slots=True)
class RuntimeAuditRecord:
    audit_record_id: AuditRecordId
    organization_id: OrganizationId
    recording_command_id: CommandId
    evaluation_time: datetime
    outcome: str
    admission_evidence: AdmissionEvidenceSnapshot
    facts: FrozenMap

    def __post_init__(self) -> None:
        if type(self.admission_evidence) is not AdmissionEvidenceSnapshot:
            raise TypeError("admission_evidence must be AdmissionEvidenceSnapshot")
        object.__setattr__(self,"facts",FrozenMap(self.facts))


@dataclass(frozen=True, slots=True)
class RuntimeAccepted:
    disposition_id: MessageId
    evaluation_time: datetime
    domain_events: tuple[EventRecord, ...]
    recorded_events: tuple[EventRecord, ...]
    audit_record: RuntimeAuditRecord

    def __post_init__(self) -> None:
        object.__setattr__(self,"domain_events",tuple(self.domain_events))
        object.__setattr__(self,"recorded_events",tuple(self.recorded_events))


@dataclass(frozen=True, slots=True)
class RuntimeRejected:
    reason_code: ReasonCode
    failed_gate: str
    safe_detail: str
    evaluation_time: datetime | None
    disposition_id: MessageId | None = None
    domain_events: tuple[EventRecord, ...] = ()
    recorded_events: tuple[EventRecord, ...] = ()
    audit_record: RuntimeAuditRecord | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self,"domain_events",tuple(self.domain_events))
        object.__setattr__(self,"recorded_events",tuple(self.recorded_events))
        if self.domain_events:
            raise ValueError("rejected Commands cannot emit domain Events")


KernelRuntimeResult = RuntimeAccepted | RuntimeRejected


@dataclass(frozen=True, slots=True)
class AppendConfirmed:
    first_position: int
    last_position: int
    events: tuple[EventRecord, ...]
    result: RuntimeAccepted | RuntimeRejected

    def __post_init__(self) -> None:
        object.__setattr__(self,"events",tuple(self.events))


@dataclass(frozen=True, slots=True)
class AppendConflict:
    expected_position: int
    current_position: int


@dataclass(frozen=True, slots=True)
class AppendRejected:
    reason_code: ReasonCode
    safe_detail: str


@dataclass(frozen=True, slots=True)
class AppendPreviouslyRecorded:
    original_result: RuntimeAccepted | RuntimeRejected


@dataclass(frozen=True, slots=True)
class AppendIdempotencyConflict:
    pass


@dataclass(frozen=True, slots=True)
class RuntimeAppendBatch:
    events: tuple[EventRecord, ...]
    result: RuntimeAccepted | RuntimeRejected

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))


RuntimeAppendResult = (
    AppendConfirmed | AppendConflict | AppendRejected |
    AppendPreviouslyRecorded | AppendIdempotencyConflict
)


class RuntimeEventStore(Protocol):
    def read(self, organization_id: OrganizationId) -> tuple[EventRecord, ...]: ...

    def inspect_idempotency(self, scope: IdempotencyScope,
                            fingerprint: str) -> IdempotencyInspection: ...

    def append_if_current(self, organization_id: OrganizationId,
                          expected_prior_position: int,
                          scope: IdempotencyScope, fingerprint: str,
                          build_batch: Callable[[], RuntimeAppendBatch]) -> RuntimeAppendResult: ...


class KernelRuntime:
    """Thin, explicit orchestration of one deterministic Command attempt."""

    def __init__(self, *, clock: Clock, identifiers: IdentifierAllocator,
                 evaluator: ProcessingEvaluator, store: RuntimeEventStore,
                 resolver: RecordingBoundaryResolver,
                 handlers: tuple[CommandHandler, ...]) -> None:
        registry: dict[tuple[str, RecordTypeVersion], CommandHandler] = {}
        for handler in handlers:
            key=(handler.operation_type,handler.operation_version)
            if key in registry:
                raise ValueError("duplicate command handler registration")
            registry[key]=handler
        self._clock=clock
        self._identifiers=identifiers
        self._evaluator=evaluator
        self._store=store
        self._resolver=resolver
        self._handlers=registry

    def execute(self, command: object) -> KernelRuntimeResult:
        # Stage 1: effect-free structure, traffic, schema, and support validation.
        if not isinstance(command,RuntimeCommand):
            return self._reject_pre_boundary(
                ReasonCode.INPUT_MALFORMED,"structure","Command structure is invalid",None)
        submission=command.submission
        if submission.envelope.traffic_mode is not TrafficMode.LIVE:
            return self._reject_pre_boundary(
                ReasonCode.INPUT_MALFORMED,"structure","Command must use live traffic",None)

        evaluation_time=self._clock.evaluation_time()
        if (not isinstance(evaluation_time,datetime) or evaluation_time.tzinfo is None or
            evaluation_time.utcoffset() is None):
            return self._reject_pre_boundary(
                ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,"evaluation_time",
                "authoritative time is unavailable",None)

        if submission.envelope.schema_version != RECORD_V1:
            return self._reject_pre_boundary(
                ReasonCode.VER_UNSUPPORTED,"supported_schema",
                "Command schema is unsupported",evaluation_time)
        handler=self._handlers.get((submission.operation_type,submission.operation_version))
        if handler is None:
            return self._reject_pre_boundary(
                ReasonCode.VER_UNSUPPORTED,"supported_operation",
                "operation or version is unsupported",evaluation_time)
        structural=handler.validate(command)
        if structural is not None:
            if type(structural) is not HandlerRejected:
                return self._reject_pre_boundary(
                    ReasonCode.INTEGRITY_VERIFICATION_FAILED,"structure",
                    "handler validation returned an invalid result",evaluation_time)
            return self._reject_pre_boundary(
                structural.reason_code,"structure",structural.safe_detail,evaluation_time)

        # Stage 2: trusted Organization and initiating-attribution resolution.
        claim=AdmissionClaim(
            submission.envelope.message_id,submission.command_id,
            submission.envelope.organization_id,submission.envelope.initiating_actor_id,
            submission.invocation_proof_reference,
        )
        try:
            admission=self._resolver.resolve(claim)
        except Exception:
            return self._reject_pre_boundary(
                ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
                AdmissionGate.ADMISSION_DEPENDENCY.value,
                "recording-boundary resolution is unavailable",evaluation_time)
        if type(admission) is AdmissionDenied:
            if (admission.claim_message_id!=claim.message_id or
                admission.command_id!=claim.command_id):
                return self._reject_pre_boundary(
                    ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
                    AdmissionGate.ADMISSION_DEPENDENCY.value,
                    "recording-boundary denial is inconsistent",evaluation_time)
            return self._reject_pre_boundary(
                admission.reason_code,admission.failed_gate.value,
                admission.safe_detail,evaluation_time)
        if type(admission) is not AdmissionEstablished:
            return self._reject_pre_boundary(
                ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
                AdmissionGate.ADMISSION_DEPENDENCY.value,
                "recording-boundary resolver returned an invalid result",evaluation_time)
        try:
            admission.validate_claim(claim)
        except (TypeError,ValueError):
            return self._reject_pre_boundary(
                ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
                AdmissionGate.ADMISSION_DEPENDENCY.value,
                "recording-boundary proof is inconsistent",evaluation_time)

        # Stage 3: bind canonical Organization history and scoped idempotency.
        organization_id=admission.organization_id
        prior=self._store.read(organization_id)
        scope=IdempotencyScope(
            organization_id,admission.initiating_actor_id,
            submission.operation_type,submission.idempotency_key,
        )
        fingerprint=semantic_runtime_command_fingerprint(command)
        inspection=self._store.inspect_idempotency(scope,fingerprint)
        if inspection.state is IdempotencyState.EXACT:
            original=inspection.original_disposition
            if type(original) in (RuntimeAccepted,RuntimeRejected):
                return original
            return RuntimeRejected(
                ReasonCode.INTEGRITY_VERIFICATION_FAILED,"idempotency",
                "recorded disposition is invalid",evaluation_time)
        if inspection.state is not IdempotencyState.NEW:
            reason=(ReasonCode.IDEMPOTENCY_CONFLICT
                    if inspection.state is IdempotencyState.CONFLICT
                    else ReasonCode.RECONCILIATION_REQUIRED)
            return RuntimeRejected(reason,"idempotency",
                "idempotency state does not permit processing",evaluation_time)
        if len(prior) != command.expected_stream_position:
            return RuntimeRejected(ReasonCode.STREAM_CONCURRENCY_CONFLICT,"concurrency",
                                   "expected stream position is stale",evaluation_time)

        # Stage 4: authorization governance, then deterministic domain handling.
        admitted_context=AdmittedCommandContext(command,admission,prior,evaluation_time)
        evaluation=self._evaluator.evaluate(admitted_context)
        if type(evaluation) is ProcessingDenied:
            return self._record_attributable_rejection(
                admitted_context,scope,fingerprint,evaluation.reason_code,
                evaluation.failed_gate,evaluation.safe_detail,evaluation.audit_facts)
        if type(evaluation) is not ProcessingAllowed:
            return self._record_attributable_rejection(
                admitted_context,scope,fingerprint,
                ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
                "governance","governance evaluation is unavailable",FrozenMap())

        handler_context=HandlerContext(
            command,prior,evaluation_time,organization_id,admission.initiating_actor_id)
        handled=handler.handle(handler_context)
        if type(handled) is HandlerRejected:
            return self._record_attributable_rejection(
                admitted_context,scope,fingerprint,handled.reason_code,
                "handler",handled.safe_detail,handled.audit_facts)
        if type(handled) is not HandlerAccepted:
            return self._record_attributable_rejection(
                admitted_context,scope,fingerprint,
                ReasonCode.INTEGRITY_VERIFICATION_FAILED,
                "handler","handler returned an invalid result",FrozenMap())

        facts=FrozenMap({"governance":evaluation.audit_facts,"handler":handled.audit_facts})
        # Stage 5: atomic attributable acceptance/domain/audit recording.
        return self._record_acceptance(admitted_context,scope,fingerprint,handled.events,facts)

    @staticmethod
    def _reject_pre_boundary(reason: ReasonCode, gate: str, detail: str,
                             evaluation_time: datetime | None) -> RuntimeRejected:
        return RuntimeRejected(reason,gate,detail,evaluation_time)

    def _record_acceptance(self, context: AdmittedCommandContext,
                           scope: IdempotencyScope, fingerprint: str,
                           proposals: tuple[DomainEventProposal, ...],
                           facts: FrozenMap) -> KernelRuntimeResult:
        organization_id=context.admission.organization_id
        admission_evidence=AdmissionEvidenceSnapshot.from_established(context.admission)
        def build_batch():
            disposition_id=self._identifiers.disposition_id()
            audit_id=self._identifiers.audit_id()
            audit=RuntimeAuditRecord(audit_id,organization_id,
                context.command.submission.command_id,context.evaluation_time,"accepted",
                admission_evidence,facts)
            all_proposals=(
                DomainEventProposal("CommandAccepted",RECORD_V1,
                    FrozenMap({"operation_type":context.command.submission.operation_type,
                               "operation_version":context.command.submission.operation_version,
                               "disposition_id":str(disposition_id)}),
                    entity_references=context.command.submission.target_references),
                *proposals,
                DomainEventProposal("AuditLinked",RECORD_V1,
                    FrozenMap({"audit_record_id":str(audit_id),"outcome":audit.outcome,
                               "admission_evidence":audit.admission_evidence,
                               "facts":audit.facts})),
            )
            events=self._materialize(context,audit_id,all_proposals)
            result=RuntimeAccepted(
                disposition_id,context.evaluation_time,events[1:-1],events,audit)
            return RuntimeAppendBatch(events,result)
        appended=self._store.append_if_current(organization_id,
            context.command.expected_stream_position,scope,fingerprint,build_batch)
        if type(appended) is AppendPreviouslyRecorded:
            return appended.original_result
        if type(appended) is AppendIdempotencyConflict:
            return RuntimeRejected(ReasonCode.IDEMPOTENCY_CONFLICT,"idempotency",
                "idempotency key conflicts with recorded semantics",context.evaluation_time)
        if type(appended) is AppendConflict:
            return RuntimeRejected(ReasonCode.STREAM_CONCURRENCY_CONFLICT,"append",
                "stream changed before append",context.evaluation_time)
        if type(appended) is not AppendConfirmed:
            return RuntimeRejected(ReasonCode.APPEND_FAILED,"append",
                "authoritative Event append failed",context.evaluation_time)
        return appended.result

    def _record_attributable_rejection(
            self, context: AdmittedCommandContext, scope: IdempotencyScope,
            fingerprint: str, reason: ReasonCode, gate: str, detail: str,
            facts: FrozenMap) -> KernelRuntimeResult:
        command=context.command
        evaluation_time=context.evaluation_time
        organization_id=context.admission.organization_id
        admission_evidence=AdmissionEvidenceSnapshot.from_established(context.admission)
        def build_batch():
            disposition_id=self._identifiers.disposition_id()
            audit_id=self._identifiers.audit_id()
            audit=RuntimeAuditRecord(audit_id,organization_id,
                command.submission.command_id,evaluation_time,"rejected",
                admission_evidence,facts)
            proposals=(
                DomainEventProposal("CommandRejected",RECORD_V1,
                    FrozenMap({"failed_gate":gate,"reason_code":reason.value,
                               "disposition_id":str(disposition_id)})),
                DomainEventProposal("AuditLinked",RECORD_V1,
                    FrozenMap({"audit_record_id":str(audit_id),"outcome":audit.outcome,
                               "admission_evidence":audit.admission_evidence,
                               "facts":audit.facts})),
            )
            events=self._materialize(context,audit_id,proposals)
            audit=RuntimeAuditRecord(audit_id,organization_id,
                command.submission.command_id,evaluation_time,"rejected",
                admission_evidence,facts)
            result=RuntimeRejected(reason,gate,detail,evaluation_time,
                disposition_id,(),events,audit)
            return RuntimeAppendBatch(events,result)
        appended=self._store.append_if_current(organization_id,
            command.expected_stream_position,scope,fingerprint,build_batch)
        if type(appended) is AppendPreviouslyRecorded:
            return appended.original_result
        if type(appended) is AppendIdempotencyConflict:
            return RuntimeRejected(ReasonCode.IDEMPOTENCY_CONFLICT,"idempotency",
                "idempotency key conflicts with recorded semantics",evaluation_time)
        if type(appended) is AppendConflict:
            return RuntimeRejected(ReasonCode.STREAM_CONCURRENCY_CONFLICT,"append",
                "stream changed before rejection append",evaluation_time)
        if type(appended) is not AppendConfirmed:
            return RuntimeRejected(ReasonCode.APPEND_FAILED,"append",
                "rejection Event append failed",evaluation_time)
        return appended.result

    def _materialize(self, context: AdmittedCommandContext, audit_id: AuditRecordId,
                     proposals: tuple[DomainEventProposal, ...]) -> tuple[EventRecord, ...]:
        submission=context.command.submission
        organization_id=context.admission.organization_id
        stream_id=StreamId(f"organization:{organization_id}")
        records=[]
        for offset,proposal in enumerate(proposals,1):
            event_id=self._identifiers.event_id()
            position=context.command.expected_stream_position+offset
            envelope=EventEnvelope(MessageId(f"event-message:{event_id}"),proposal.event_type,
                organization_id,context.admission.initiating_actor_id,submission.command_id,
                submission.envelope.correlation_id,context.evaluation_time,stream_id,position,
                submission.envelope.classification,IntegrityReference(f"integrity:{event_id}"))
            records.append(EventRecord(envelope,event_id,proposal.event_type,proposal.event_version,
                (),proposal.causal_reference,None,proposal.entity_references,
                EpistemicStatus.DETERMINISTIC,NOT_APPLICABLE,
                proposal.work_root if proposal.work_root is not None else submission.work_root,
                proposal.projection_effects,FrozenMap(),FrozenMap(),audit_id,
                IntegrityReference(f"integrity:{event_id}"),result="recorded",payload=proposal.payload))
        return tuple(records)


def semantic_runtime_command_identity(command: RuntimeCommand) -> tuple[object, ...]:
    """Material ordinary Command identity; delivery message identity is nonsemantic."""
    submission=command.submission
    envelope=submission.envelope
    return (
        "RuntimeCommandSemanticIdentity",
        ("envelope",(
            envelope.message_type,envelope.organization_id,envelope.initiating_actor_id,
            envelope.correlation_id,envelope.issued_at,envelope.classification,envelope.purpose,
            envelope.payload_type,envelope.payload_version,envelope.payload,
            envelope.schema_version,envelope.traffic_mode,
        )),
        ("submission",tuple(
            (name,getattr(submission,name))
            for name in submission.__dataclass_fields__ if name != "envelope"
        )),
        ("command",tuple(
            (name,getattr(command,name))
            for name in command.__dataclass_fields__
            if name != "submission"
        )),
    )


def semantic_runtime_command_fingerprint(command: RuntimeCommand) -> str:
    return semantic_logical_fingerprint(semantic_runtime_command_identity(command))


StateT=TypeVar("StateT")


class ProjectionReducer(Protocol, Generic[StateT]):
    def initial_state(self) -> StateT: ...
    def apply(self, state: StateT, event: EventRecord) -> StateT: ...


def replay(events: tuple[EventRecord, ...], reducer: ProjectionReducer[StateT]) -> StateT:
    """Pure ordered replay. It cannot execute Commands or reach effect boundaries."""
    state=reducer.initial_state()
    organization_id=None
    stream_id=None
    event_ids=set()
    for expected_position,event in enumerate(tuple(events),1):
        if type(event) is not EventRecord:
            raise ValueError("replay input contains a non-Event record")
        if event.envelope.stream_position != expected_position:
            raise ValueError("Event stream position is missing or reordered")
        if organization_id is None:
            organization_id=event.envelope.organization_id
            stream_id=event.envelope.stream_id
        elif event.envelope.organization_id != organization_id:
            raise ValueError("replay stream crosses Organization boundary")
        if event.envelope.stream_id != stream_id:
            raise ValueError("replay input contains conflicting stream identity")
        if event.event_id in event_ids:
            raise ValueError("replay input contains duplicate Event identity")
        event_ids.add(event.event_id)
        state=reducer.apply(state,event)
    return state
