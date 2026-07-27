"""Deterministic governed activation of one draft Role."""
from __future__ import annotations

from dataclasses import dataclass

from aios_protocol.commands import EntityReference
from aios_protocol.identifiers import ActorId, CommandId, OrganizationId, RoleId
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap, require_positive, require_type
from aios_protocol.versions import RECORD_V1

from .create_role import (
    OrganizationRoleProjection, ROLE_ACTIVATED_EVENT, ROLE_ACTIVATED_VERSION,
    replay_organization_roles,
)
from .runtime import (
    DomainEventProposal, HandlerAccepted, HandlerContext, HandlerRejected,
    ProcessingAllowed, ProcessingDenied, ProcessingEvaluation, ProcessingEvaluator,
    RuntimeCommand,
)


ACTIVATE_ROLE_OPERATION = "ActivateRole"
ACTIVATE_ROLE_VERSION = RECORD_V1
ROLE_ACTIVATE_AUTHORITY_SCOPE = "role.activate"


@dataclass(frozen=True, slots=True)
class ActivateRolePayload:
    role_id: RoleId
    expected_entity_revision: int

    def __post_init__(self) -> None:
        require_type(self.role_id,RoleId,type(self).__name__,"role_id")
        require_positive(
            self.expected_entity_revision,type(self).__name__,"expected_entity_revision",
        )


@dataclass(frozen=True, slots=True)
class ActivateRoleCommand(RuntimeCommand):
    payload: ActivateRolePayload

    def __post_init__(self) -> None:
        super(ActivateRoleCommand,self).__post_init__()
        require_type(self.payload,ActivateRolePayload,type(self).__name__,"payload")
        submission=self.submission
        if (submission.operation_type != ACTIVATE_ROLE_OPERATION
                or submission.operation_version != ACTIVATE_ROLE_VERSION):
            raise ValueError("ActivateRole operation type or version is invalid")
        expected=FrozenMap({
            "role_id":self.payload.role_id,
            "expected_entity_revision":self.payload.expected_entity_revision,
        })
        if submission.envelope.payload != expected:
            raise ValueError("ActivateRole payload must contain exactly the typed activation facts")


class ActivateRoleGovernanceEvaluator:
    """Delegated role.activate evaluation after authenticated admission."""
    def __init__(self,*,authority_evaluator: ProcessingEvaluator) -> None:
        self._authority_evaluator=authority_evaluator

    def evaluate(self,context) -> ProcessingEvaluation:
        if not context.command.submission.authority_references:
            return ProcessingDenied(ReasonCode.AUTH_MISSING,"authority",
                                    "Role activation requires explicit Authority Grant evidence")
        evaluated=self._authority_evaluator.evaluate(context)
        if type(evaluated) is ProcessingDenied:
            return evaluated
        if (type(evaluated) is ProcessingAllowed
                and evaluated.audit_facts.get("authority_scope") == ROLE_ACTIVATE_AUTHORITY_SCOPE):
            return evaluated
        return ProcessingDenied(ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,"authority",
                                "role.activate authority evaluation is unavailable")


class ActivateRoleHandler:
    operation_type=ACTIVATE_ROLE_OPERATION
    operation_version=ACTIVATE_ROLE_VERSION

    def __init__(self,initial_projection: OrganizationRoleProjection) -> None:
        self._initial_projection=initial_projection

    def validate(self,command: RuntimeCommand) -> HandlerRejected | None:
        if type(command) is not ActivateRoleCommand:
            return HandlerRejected(ReasonCode.INPUT_MALFORMED,"ActivateRole command is malformed")
        submission=command.submission
        expected_target=(EntityReference(
            "Role",str(command.payload.role_id),command.payload.expected_entity_revision,
        ),)
        invalid=(
            submission.envelope.message_type != "CommandSubmission"
            or type(submission.envelope.organization_id) is not OrganizationId
            or type(submission.envelope.initiating_actor_id) is not ActorId
            or type(submission.command_id) is not CommandId
            or submission.envelope.payload_type != ACTIVATE_ROLE_OPERATION
            or submission.envelope.schema_version != RECORD_V1
            or submission.envelope.payload_version.raw != "1.0"
            or submission.target_references != expected_target
            or submission.lifecycle_preconditions != FrozenMap({
                "current_state":"draft","requested_state":"active",
            })
            or submission.work_root is not None or submission.work_root_required
            or submission.tool_request is not None
        )
        if invalid:
            return HandlerRejected(ReasonCode.INPUT_MALFORMED,"ActivateRole structure is invalid")
        return None

    def handle(self,context: HandlerContext):
        command=context.command
        if type(command) is not ActivateRoleCommand:
            return HandlerRejected(ReasonCode.INPUT_MALFORMED,"ActivateRole command is malformed")
        try:
            projection=replay_organization_roles(self._initial_projection,context.prior_events)
        except ValueError:
            return HandlerRejected(ReasonCode.INTEGRITY_VERIFICATION_FAILED,
                                   "Organization Role history is invalid")
        if projection.organization_id != context.organization_id:
            return HandlerRejected(ReasonCode.ORG_BOUNDARY_VIOLATION,
                                   "Role Organization scope is inconsistent")
        role=projection.role(command.payload.role_id)
        if role is None or role.lifecycle_state != "draft":
            return HandlerRejected(ReasonCode.LIFECYCLE_INVALID_TRANSITION,
                                   "Role activation requires an existing draft Role")
        if role.entity_revision != command.payload.expected_entity_revision:
            return HandlerRejected(ReasonCode.STATE_STALE_VERSION,
                                   "expected Role entity revision is stale")
        resulting_revision=role.entity_revision+1
        proposal=DomainEventProposal(
            ROLE_ACTIVATED_EVENT,ROLE_ACTIVATED_VERSION,
            FrozenMap({
                "role_id":role.role_id,
                "prior_lifecycle_state":"draft",
                "lifecycle_state":"active",
                "prior_entity_revision":role.entity_revision,
                "entity_revision":resulting_revision,
            }),
            FrozenMap({
                "role_id":role.role_id,"lifecycle_state":"active",
                "entity_revision":resulting_revision,
            }),
            (EntityReference("Role",str(role.role_id),resulting_revision),),
            causal_reference=str(command.submission.command_id),
        )
        return HandlerAccepted((proposal,),FrozenMap({
            "role_id":role.role_id,"prior_entity_revision":role.entity_revision,
            "entity_revision":resulting_revision,
            "organization_stream_precondition":command.expected_stream_position,
        }))
