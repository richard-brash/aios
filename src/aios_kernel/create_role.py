"""Deterministic ordinary creation of one draft Role on an Organization stream."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from aios_protocol.commands import EntityReference
from aios_protocol.envelope import EventEnvelope, TrafficMode
from aios_protocol.events import EpistemicStatus, EventRecord
from aios_protocol.identifiers import (
    ActorId, AuditRecordId, CommandId, CorrelationId, EventId, IntegrityReference,
    MessageId, OrganizationId, RoleId, StreamId,
)
from aios_protocol.presence import NOT_APPLICABLE
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap, require_nonempty, require_type
from aios_protocol.versions import RECORD_V1, RecordTypeVersion

from .runtime import (
    AdmissionEvidenceSnapshot, DomainEventProposal, HandlerAccepted, HandlerContext, HandlerRejected,
    ProcessingAllowed, ProcessingDenied, ProcessingEvaluation, ProcessingEvaluator,
    RuntimeCommand,
)


CREATE_ROLE_OPERATION = "CreateRole"
CREATE_ROLE_VERSION = RECORD_V1
ROLE_CREATED_EVENT = "RoleCreated"
ROLE_CREATED_VERSION = RECORD_V1
ROLE_ACTIVATED_EVENT = "RoleActivated"
ROLE_ACTIVATED_VERSION = RECORD_V1
_SUPPORTED_ORGANIZATION_HISTORY_EVENTS = frozenset({
    "CommandAccepted", "CommandRejected", "AuditLinked",
    "TaskCreated", "DecisionLinked", "WorkRootLinked",
    ROLE_CREATED_EVENT, ROLE_ACTIVATED_EVENT,
})
_ACCEPTED_DOMAIN_SEQUENCES = FrozenMap({
    "CreateTask": ("TaskCreated", "DecisionLinked", "WorkRootLinked"),
    CREATE_ROLE_OPERATION: (ROLE_CREATED_EVENT,),
    "ActivateRole": (ROLE_ACTIVATED_EVENT,),
})


@dataclass(frozen=True, slots=True)
class RoleCreationAttributes:
    role_id: RoleId
    name: str
    duties: tuple[str, ...]
    eligible_capability_references: tuple[str, ...]
    eligible_authority_scope: FrozenMap
    escalation_path: str
    separation_of_duties_constraints: tuple[str, ...]

    def __post_init__(self) -> None:
        require_type(self.role_id,RoleId,type(self).__name__,"role_id")
        require_nonempty(self.name,type(self).__name__,"name")
        require_nonempty(self.escalation_path,type(self).__name__,"escalation_path")
        for field_name in ("duties","eligible_capability_references","separation_of_duties_constraints"):
            values=tuple(getattr(self,field_name))
            if not values:
                raise ValueError(f"{field_name} must not be empty")
            for index,value in enumerate(values):
                require_nonempty(value,type(self).__name__,f"{field_name}[{index}]")
            object.__setattr__(self,field_name,values)
        object.__setattr__(self,"eligible_authority_scope",FrozenMap(self.eligible_authority_scope))


@dataclass(frozen=True, slots=True)
class CreateRoleCommand(RuntimeCommand):
    role: RoleCreationAttributes

    def __post_init__(self) -> None:
        super(CreateRoleCommand,self).__post_init__()
        require_type(self.role,RoleCreationAttributes,type(self).__name__,"role")
        submission=self.submission
        if submission.operation_type != CREATE_ROLE_OPERATION or submission.operation_version != CREATE_ROLE_VERSION:
            raise ValueError("CreateRole operation type or version is invalid")
        if submission.envelope.payload != FrozenMap({"role":self.role}):
            raise ValueError("CreateRole payload must contain exactly the typed Role attributes")


@dataclass(frozen=True, slots=True)
class RoleProjection:
    role_id: RoleId
    organization_id: OrganizationId
    name: str
    duties: tuple[str, ...]
    eligible_capability_references: tuple[str, ...]
    eligible_authority_scope: FrozenMap
    escalation_path: str
    separation_of_duties_constraints: tuple[str, ...]
    lifecycle_state: str
    entity_revision: int
    created_by_actor_id: ActorId
    creation_command_id: CommandId
    creation_event_id: EventId | None
    created_at: datetime | None
    is_founding_role: bool

    def __post_init__(self) -> None:
        object.__setattr__(self,"duties",tuple(self.duties))
        object.__setattr__(self,"eligible_capability_references",tuple(self.eligible_capability_references))
        object.__setattr__(self,"eligible_authority_scope",FrozenMap(self.eligible_authority_scope))
        object.__setattr__(self,"separation_of_duties_constraints",tuple(self.separation_of_duties_constraints))


@dataclass(frozen=True, slots=True)
class OrganizationRoleProjection:
    organization_id: OrganizationId
    genesis_completed: bool
    founding_role_id: RoleId
    roles: tuple[RoleProjection, ...]
    last_organization_stream_position: int

    def __post_init__(self) -> None:
        object.__setattr__(self,"roles",tuple(self.roles))

    def role(self,role_id: RoleId) -> RoleProjection | None:
        return next((role for role in self.roles if role.role_id == role_id),None)


class OrganizationRoleReducer:
    """Pure Role projection seeded by an already-replayed constitutional genesis."""
    def __init__(self,initial: OrganizationRoleProjection) -> None:
        if type(initial) is not OrganizationRoleProjection or not initial.genesis_completed:
            raise ValueError("Role projection requires completed genesis")
        founding=initial.role(initial.founding_role_id)
        if founding is None or not founding.is_founding_role or founding.lifecycle_state != "active":
            raise ValueError("Role projection requires the active founding Role")
        self._initial=initial

    def initial_state(self) -> OrganizationRoleProjection:
        return self._initial

    def apply(self,state: OrganizationRoleProjection,event: EventRecord) -> OrganizationRoleProjection:
        if event.event_type not in (ROLE_CREATED_EVENT,ROLE_ACTIVATED_EVENT):
            return OrganizationRoleProjection(
                state.organization_id,state.genesis_completed,state.founding_role_id,
                state.roles,event.envelope.stream_position,
            )
        if event.event_type == ROLE_ACTIVATED_EVENT:
            return self._apply_role_activated(state,event)
        if event.event_version != ROLE_CREATED_VERSION or event.envelope.schema_version != RECORD_V1:
            raise ValueError("RoleCreated version is unsupported")
        attributes=event.payload.get("role")
        if type(attributes) is not RoleCreationAttributes:
            raise ValueError("RoleCreated lacks typed creation attributes")
        if event.payload.get("lifecycle_state") != "draft" or event.payload.get("entity_revision") != 1:
            raise ValueError("RoleCreated must establish draft revision one")
        if attributes.role_id == state.founding_role_id:
            raise ValueError("RoleCreated cannot recreate the founding Role")
        if state.role(attributes.role_id) is not None:
            raise ValueError("RoleCreated repeats an existing Role identity")
        references=tuple(
            reference for reference in event.entity_references
            if reference.entity_type == "Role" and reference.entity_id == str(attributes.role_id)
        )
        if len(references) != 1 or references[0].expected_version != 1:
            raise ValueError("RoleCreated lacks its entity revision reference")
        role=RoleProjection(
            attributes.role_id,state.organization_id,attributes.name,attributes.duties,
            attributes.eligible_capability_references,attributes.eligible_authority_scope,
            attributes.escalation_path,attributes.separation_of_duties_constraints,
            "draft",1,event.envelope.initiating_actor_id,
            event.envelope.recording_command_id,event.event_id,
            event.envelope.evaluation_time,False,
        )
        return OrganizationRoleProjection(
            state.organization_id,state.genesis_completed,state.founding_role_id,
            state.roles+(role,),event.envelope.stream_position,
        )

    def _apply_role_activated(
        self,state: OrganizationRoleProjection,event: EventRecord,
    ) -> OrganizationRoleProjection:
        expected_fields={
            "role_id","prior_lifecycle_state","lifecycle_state",
            "prior_entity_revision","entity_revision",
        }
        if set(event.payload) != expected_fields:
            raise ValueError("RoleActivated payload is malformed")
        role_id=event.payload.get("role_id")
        if type(role_id) is not RoleId:
            raise ValueError("RoleActivated Role identity is malformed")
        role=state.role(role_id)
        if role is None:
            raise ValueError("RoleActivated targets a nonexistent Role")
        prior_revision=event.payload.get("prior_entity_revision")
        resulting_revision=event.payload.get("entity_revision")
        if (event.payload.get("prior_lifecycle_state") != "draft"
                or event.payload.get("lifecycle_state") != "active"
                or role.lifecycle_state != "draft"):
            raise ValueError("RoleActivated source state is invalid")
        if (type(prior_revision) is not int or type(resulting_revision) is not int
                or prior_revision != role.entity_revision
                or resulting_revision != prior_revision+1):
            raise ValueError("RoleActivated revision transition is invalid")
        references=tuple(event.entity_references)
        if (len(references) != 1 or references[0].entity_type != "Role"
                or references[0].entity_id != str(role_id)
                or references[0].expected_version != resulting_revision):
            raise ValueError("RoleActivated lacks its resulting entity revision reference")
        activated=replace(role,lifecycle_state="active",entity_revision=resulting_revision)
        roles=tuple(activated if existing.role_id == role_id else existing
                    for existing in state.roles)
        return OrganizationRoleProjection(
            state.organization_id,state.genesis_completed,state.founding_role_id,
            roles,event.envelope.stream_position,
        )


def _validate_common_organization_event(
    event: EventRecord,organization_id: OrganizationId,expected_position: int,
    event_ids: set[EventId],
) -> None:
    if type(event) is not EventRecord or type(event.envelope) is not EventEnvelope:
        raise ValueError("Role replay contains a malformed Event record")
    envelope=event.envelope
    if (
        type(envelope.message_id) is not MessageId
        or type(envelope.organization_id) is not OrganizationId
        or type(envelope.initiating_actor_id) is not ActorId
        or type(envelope.recording_command_id) is not CommandId
        or type(envelope.correlation_id) is not CorrelationId
        or type(envelope.stream_id) is not StreamId
        or type(envelope.stream_position) is not int
        or type(envelope.integrity_reference) is not IntegrityReference
        or type(event.event_id) is not EventId
        or type(event.event_type) is not str
        or not event.event_type
        or type(event.audit_record_id) is not AuditRecordId
        or type(event.integrity_reference) is not IntegrityReference
        or type(event.event_version) is not RecordTypeVersion
        or type(event.payload) is not FrozenMap
        or not envelope.classification
        or type(envelope.evaluation_time) is not datetime
        or envelope.evaluation_time.tzinfo is None
        or envelope.evaluation_time.utcoffset() is None
        or envelope.traffic_mode is not TrafficMode.LIVE
        or event.epistemic_status is not EpistemicStatus.DETERMINISTIC
        or event.confidence is not NOT_APPLICABLE
        or event.result != "recorded"
    ):
        raise ValueError("Role replay Event envelope is malformed")
    if envelope.organization_id != organization_id:
        raise ValueError("Role Event crosses Organization boundary")
    if str(envelope.stream_id) != f"organization:{organization_id}":
        raise ValueError("Role Event is not on the Organization stream")
    if envelope.stream_position != expected_position:
        raise ValueError("Organization Event order is missing or reordered")
    if envelope.schema_version != RECORD_V1 or event.event_version != RECORD_V1:
        raise ValueError("Organization Event version is unsupported")
    if envelope.message_type != event.event_type:
        raise ValueError("Organization Event type is inconsistent")
    if event.event_type not in _SUPPORTED_ORGANIZATION_HISTORY_EVENTS:
        raise ValueError("Organization Event type is unsupported by Role replay")
    if event.event_id in event_ids:
        raise ValueError("Organization history repeats Event identity")
    if envelope.integrity_reference != event.integrity_reference:
        raise ValueError("Organization Event integrity linkage is inconsistent")


def _same_execution_lineage(first: EventRecord,second: EventRecord) -> bool:
    return (
        first.envelope.organization_id == second.envelope.organization_id
        and first.envelope.initiating_actor_id == second.envelope.initiating_actor_id
        and first.envelope.recording_command_id == second.envelope.recording_command_id
        and first.envelope.correlation_id == second.envelope.correlation_id
        and first.envelope.evaluation_time == second.envelope.evaluation_time
        and first.audit_record_id == second.audit_record_id
    )


def _validate_command_accepted(event: EventRecord) -> tuple[str,RecordTypeVersion]:
    operation=event.payload.get("operation_type")
    references=tuple(event.entity_references)
    expected_entity_type=("Task" if operation == "CreateTask" else "Role")
    if (
        set(event.payload) != {"operation_type","operation_version","disposition_id"}
        or operation not in _ACCEPTED_DOMAIN_SEQUENCES
        or event.payload.get("operation_version") != RECORD_V1
        or not event.payload.get("disposition_id")
        or len(references) != 1
        or references[0].entity_type != expected_entity_type
        or type(references[0].expected_version) is not int
        or references[0].expected_version < 0
        or event.causal_reference is not None
    ):
        raise ValueError("CommandAccepted is not a supported ordinary acceptance")
    return operation,event.payload["operation_version"]


def _validate_role_created_lineage(accepted: EventRecord,event: EventRecord) -> None:
    if not _same_execution_lineage(accepted,event):
        raise ValueError("RoleCreated lineage does not match its accepted Command")
    if event.causal_reference != str(event.envelope.recording_command_id):
        raise ValueError("RoleCreated causal Command linkage is inconsistent")
    role=event.payload.get("role")
    reference=accepted.entity_references[0]
    if (type(role) is not RoleCreationAttributes
            or reference.entity_id != str(role.role_id)
            or reference.expected_version != 0):
        raise ValueError("RoleCreated identity does not match its accepted target")


def _validate_role_activated_lineage(accepted: EventRecord,event: EventRecord) -> None:
    if not _same_execution_lineage(accepted,event):
        raise ValueError("RoleActivated lineage does not match its accepted Command")
    if event.causal_reference != str(event.envelope.recording_command_id):
        raise ValueError("RoleActivated causal Command linkage is inconsistent")
    reference=accepted.entity_references[0]
    if (type(event.payload.get("role_id")) is not RoleId
            or reference.entity_id != str(event.payload["role_id"])
            or reference.expected_version != event.payload.get("prior_entity_revision")):
        raise ValueError("RoleActivated identity or revision does not match its accepted target")


def _validate_create_task_event(accepted: EventRecord,event: EventRecord) -> None:
    if not _same_execution_lineage(accepted,event):
        raise ValueError("CreateTask domain lineage does not match its accepted Command")
    if event.causal_reference is not None:
        raise ValueError("CreateTask domain Event has unsupported causation")
    task_references=tuple(reference for reference in event.entity_references
                          if reference.entity_type == "Task")
    if len(task_references) != 1 or task_references[0].expected_version != 1:
        raise ValueError("CreateTask domain Event lacks its Task reference")
    task_id=event.payload.get("task_id")
    if task_id != task_references[0].entity_id or event.payload.get("decision_id") is None:
        raise ValueError("CreateTask domain Event payload is inconsistent")
    accepted_reference=accepted.entity_references[0]
    if (accepted_reference.entity_id != task_id or accepted_reference.expected_version != 0):
        raise ValueError("CreateTask identity does not match its accepted target")
    if event.event_type == "TaskCreated":
        required={"task_id","decision_id","title","purpose","lifecycle_state","entity_version"}
        if (set(event.payload)!=required or event.payload.get("lifecycle_state")!="proposed"
                or event.payload.get("entity_version")!=1):
            raise ValueError("TaskCreated payload is malformed")
    elif set(event.payload)!={"task_id","decision_id"}:
        raise ValueError("CreateTask linkage Event payload is malformed")


def _validate_command_rejected(event: EventRecord) -> None:
    if (
        set(event.payload) != {"failed_gate","reason_code","disposition_id"}
        or not all(event.payload.get(name) for name in event.payload)
        or event.entity_references
        or event.causal_reference is not None
    ):
        raise ValueError("CommandRejected payload is malformed")


def _validate_audit_linked(disposition: EventRecord,event: EventRecord) -> None:
    if not _same_execution_lineage(disposition,event):
        raise ValueError("AuditLinked lineage does not match its disposition")
    if (
        set(event.payload) != {"audit_record_id","outcome","admission_evidence","facts"}
        or event.payload.get("audit_record_id") != str(event.audit_record_id)
        or event.payload.get("outcome")
            != ("accepted" if disposition.event_type == "CommandAccepted" else "rejected")
        or type(event.payload.get("admission_evidence")) is not AdmissionEvidenceSnapshot
        or type(event.payload.get("facts")) is not FrozenMap
        or event.entity_references
        or event.causal_reference is not None
    ):
        raise ValueError("AuditLinked payload is malformed")
    evidence=event.payload["admission_evidence"]
    if (
        evidence.organization_id != event.envelope.organization_id
        or evidence.initiating_actor_id != event.envelope.initiating_actor_id
        or evidence.command_id != event.envelope.recording_command_id
    ):
        raise ValueError("AuditLinked admission evidence is inconsistent")


def replay_organization_roles(
    initial: OrganizationRoleProjection,events: tuple[EventRecord, ...],
) -> OrganizationRoleProjection:
    reducer=OrganizationRoleReducer(initial)
    state=reducer.initial_state()
    event_ids:set[EventId]=set()
    ordered=tuple(events)
    for expected_position,event in enumerate(ordered,1):
        _validate_common_organization_event(
            event,state.organization_id,expected_position,event_ids,
        )
        event_ids.add(event.event_id)
    index=0
    while index < len(ordered):
        disposition=ordered[index]
        if disposition.event_type == "CommandRejected":
            _validate_command_rejected(disposition)
            if index+1 >= len(ordered) or ordered[index+1].event_type != "AuditLinked":
                raise ValueError("Organization history contains an incomplete rejected sequence")
            audit=ordered[index+1]
            _validate_audit_linked(disposition,audit)
            state=OrganizationRoleProjection(
                state.organization_id,state.genesis_completed,state.founding_role_id,
                state.roles,audit.envelope.stream_position,
            )
            index+=2
            continue
        if disposition.event_type != "CommandAccepted":
            raise ValueError("Organization history contains an orphan domain or audit Event")
        operation,_version=_validate_command_accepted(disposition)
        sequence=_ACCEPTED_DOMAIN_SEQUENCES[operation]
        end=index+1+len(sequence)
        if end >= len(ordered):
            raise ValueError("Organization history contains an incomplete accepted sequence")
        domain_events=ordered[index+1:end]
        if tuple(event.event_type for event in domain_events) != sequence:
            raise ValueError("accepted operation has an invalid domain Event sequence")
        if ordered[end].event_type != "AuditLinked":
            raise ValueError("accepted operation lacks its AuditLinked Event")
        if operation == CREATE_ROLE_OPERATION:
            _validate_role_created_lineage(disposition,domain_events[0])
        elif operation == "ActivateRole":
            _validate_role_activated_lineage(disposition,domain_events[0])
        else:
            for event in domain_events:
                _validate_create_task_event(disposition,event)
        audit=ordered[end]
        _validate_audit_linked(disposition,audit)
        for event in domain_events:
            state=reducer.apply(state,event)
        state=OrganizationRoleProjection(
            state.organization_id,state.genesis_completed,state.founding_role_id,
            state.roles,audit.envelope.stream_position,
        )
        index=end+1
    return state


class CreateRoleGovernanceEvaluator:
    """Capability authority evaluation after authenticated Organization admission."""
    def __init__(self,*,authority_evaluator: ProcessingEvaluator) -> None:
        self._authority_evaluator=authority_evaluator

    def evaluate(self,context) -> ProcessingEvaluation:
        if not context.command.submission.authority_references:
            return ProcessingDenied(ReasonCode.AUTH_MISSING,"authority",
                                    "Role creation requires explicit Authority Grant evidence")
        evaluated=self._authority_evaluator.evaluate(context)
        if type(evaluated) in (ProcessingAllowed,ProcessingDenied):
            return evaluated
        return ProcessingDenied(ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,"authority",
                                "authority evaluation is unavailable")


class CreateRoleHandler:
    operation_type=CREATE_ROLE_OPERATION
    operation_version=CREATE_ROLE_VERSION

    def __init__(self,initial_projection: OrganizationRoleProjection) -> None:
        self._initial_projection=initial_projection

    def validate(self,command: RuntimeCommand) -> HandlerRejected | None:
        if type(command) is not CreateRoleCommand:
            return HandlerRejected(ReasonCode.INPUT_MALFORMED,"CreateRole command is malformed")
        submission=command.submission
        expected_target=(EntityReference("Role",str(command.role.role_id),0),)
        invalid=(
            submission.envelope.message_type != "CommandSubmission"
            or type(submission.envelope.organization_id) is not OrganizationId
            or type(submission.envelope.initiating_actor_id) is not ActorId
            or type(submission.command_id) is not CommandId
            or type(command.role) is not RoleCreationAttributes
            or submission.envelope.payload_type != CREATE_ROLE_OPERATION
            or submission.envelope.schema_version != RECORD_V1
            or submission.envelope.payload_version.raw != "1.0"
            or submission.target_references != expected_target
            or submission.work_root is not None or submission.work_root_required
            or submission.tool_request is not None
            or "lifecycle_state" in submission.envelope.payload
        )
        if invalid:
            return HandlerRejected(ReasonCode.INPUT_MALFORMED,"CreateRole structure is invalid")
        return None

    def handle(self,context: HandlerContext):
        command=context.command
        if type(command) is not CreateRoleCommand:
            return HandlerRejected(ReasonCode.INPUT_MALFORMED,"CreateRole command is malformed")
        try:
            projection=replay_organization_roles(self._initial_projection,context.prior_events)
        except ValueError:
            return HandlerRejected(ReasonCode.INTEGRITY_VERIFICATION_FAILED,
                                   "Organization Role history is invalid")
        if projection.organization_id != context.organization_id:
            return HandlerRejected(ReasonCode.ORG_BOUNDARY_VIOLATION,
                                   "Role Organization scope is inconsistent")
        existing=projection.role(command.role.role_id)
        if existing is not None:
            detail=("founding Role already exists" if existing.is_founding_role
                    else "Role identity already exists")
            return HandlerRejected(ReasonCode.LIFECYCLE_INVALID_TRANSITION,detail)
        proposal=DomainEventProposal(
            ROLE_CREATED_EVENT,ROLE_CREATED_VERSION,
            FrozenMap({"role":command.role,"lifecycle_state":"draft","entity_revision":1}),
            FrozenMap({"role_id":command.role.role_id,"lifecycle_state":"draft",
                       "entity_revision":1}),
            (EntityReference("Role",str(command.role.role_id),1),),
            causal_reference=str(command.submission.command_id),
        )
        return HandlerAccepted((proposal,),FrozenMap({
            "role_id":command.role.role_id,"initial_state":"draft",
            "organization_stream_precondition":command.expected_stream_position,
        }))
