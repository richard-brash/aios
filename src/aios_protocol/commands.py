"""Command submission and Work Root structural contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .envelope import CallerEnvelope
from .identifiers import (
    ActorId, ApprovalId, AuthorityGrantId, DecisionId, GoalId,
    IntegrityReference, OperationId, ResourceId, ToolId,
)
from .validation import FrozenMap, require_nonempty, require_nonnegative, require_type
from .versions import RecordTypeVersion


@dataclass(frozen=True, slots=True)
class EntityReference:
    entity_type: str
    entity_id: str
    expected_version: int | None = None

    def __post_init__(self) -> None:
        require_nonempty(self.entity_type, type(self).__name__, "entity_type")
        require_nonempty(self.entity_id, type(self).__name__, "entity_id")
        if self.expected_version is not None and self.expected_version < 0:
            raise ValueError("expected_version cannot be negative")


@dataclass(frozen=True, slots=True)
class GoalWorkRoot:
    goal_id: GoalId

    def __post_init__(self) -> None:
        require_type(self.goal_id, GoalId, type(self).__name__, "goal_id")


@dataclass(frozen=True, slots=True)
class DutyWorkRoot:
    duty_type: str
    governing_mandate_reference: str
    accountable_actor_id: ActorId
    scope: str
    review_or_completion_condition: str

    def __post_init__(self) -> None:
        for field_name in (
            "duty_type", "governing_mandate_reference", "scope",
            "review_or_completion_condition",
        ):
            require_nonempty(getattr(self, field_name), type(self).__name__, field_name)
        require_type(self.accountable_actor_id, ActorId, type(self).__name__, "accountable_actor_id")


WorkRoot = GoalWorkRoot | DutyWorkRoot


class RiskClass(str, Enum):
    OBSERVE = "observe"
    PROPOSE = "propose"
    REVERSIBLE = "reversible"
    CONSEQUENTIAL = "consequential"
    HUMAN_RESERVED = "human_reserved"


@dataclass(frozen=True, slots=True)
class Reversibility:
    reversible: bool
    restoration_plan_reference: IntegrityReference | None
    verification_method: str
    window: str
    uncertainty: str = "none"

    def __post_init__(self) -> None:
        require_nonempty(self.verification_method, type(self).__name__, "verification_method")
        require_nonempty(self.window, type(self).__name__, "window")
        if self.reversible and self.restoration_plan_reference is None:
            raise ValueError("reversible action requires restoration plan reference")


class ResourceDimension(str, Enum):
    MONEY = "money"
    COMPUTE = "compute"
    TOOL_CALLS = "tool_calls"
    DATA_ACCESS = "data_access"
    ELAPSED_TIME = "elapsed_time"
    HUMAN_ATTENTION = "human_attention"
    CREDENTIALS = "credentials"
    REPUTATION_EXPOSURE = "reputation_exposure"


@dataclass(frozen=True, slots=True)
class ResourceEstimate:
    resource_id: ResourceId
    dimension: ResourceDimension
    amount: int | float
    unit: str
    maximum_exposure: int | float

    def __post_init__(self) -> None:
        require_type(self.resource_id, ResourceId, type(self).__name__, "resource_id")
        require_nonnegative(self.amount, type(self).__name__, "amount")
        require_nonnegative(self.maximum_exposure, type(self).__name__, "maximum_exposure")
        require_nonempty(self.unit, type(self).__name__, "unit")
        if self.maximum_exposure < self.amount:
            raise ValueError("maximum_exposure cannot be below estimate")


@dataclass(frozen=True, slots=True)
class ToolRequestDetails:
    tool_id: ToolId
    operation_type: str
    operation_version: RecordTypeVersion
    bounded_inputs: FrozenMap = field(default_factory=FrozenMap)
    result_contract: FrozenMap = field(default_factory=FrozenMap)

    def __post_init__(self) -> None:
        require_type(self.tool_id, ToolId, type(self).__name__, "tool_id")
        require_nonempty(self.operation_type, type(self).__name__, "operation_type")


@dataclass(frozen=True, slots=True)
class CommandSubmission:
    envelope: CallerEnvelope
    command_id: "CommandId"
    original_operation_id: OperationId
    operation_type: str
    operation_version: RecordTypeVersion
    target_references: tuple[EntityReference, ...]
    idempotency_key: str
    work_root: WorkRoot | None
    work_root_required: bool
    invocation_proof_reference: IntegrityReference
    authority_references: tuple[AuthorityGrantId, ...] = ()
    policy_references: tuple[str, ...] = ()
    decision_reference: DecisionId | None = None
    approval_references: tuple[ApprovalId, ...] = ()
    expected_resource_use: tuple[ResourceEstimate, ...] = ()
    lifecycle_preconditions: FrozenMap = field(default_factory=FrozenMap)
    risk: RiskClass = RiskClass.OBSERVE
    reversibility: Reversibility | None = None
    evidence_references: tuple[IntegrityReference, ...] = ()
    result_criteria: FrozenMap = field(default_factory=FrozenMap)
    stop_conditions: FrozenMap = field(default_factory=FrozenMap)
    tool_request: ToolRequestDetails | None = None

    def __post_init__(self) -> None:
        from .identifiers import CommandId
        require_type(self.command_id, CommandId, type(self).__name__, "command_id")
        require_type(self.original_operation_id, OperationId, type(self).__name__, "original_operation_id")
        require_type(
            self.invocation_proof_reference, IntegrityReference,
            type(self).__name__, "invocation_proof_reference",
        )
        require_nonempty(self.operation_type, type(self).__name__, "operation_type")
        require_nonempty(self.idempotency_key, type(self).__name__, "idempotency_key")
        object.__setattr__(self, "target_references", tuple(self.target_references))
        object.__setattr__(self, "authority_references", tuple(self.authority_references))
        object.__setattr__(self, "policy_references", tuple(self.policy_references))
        object.__setattr__(self, "approval_references", tuple(self.approval_references))
        object.__setattr__(self, "expected_resource_use", tuple(self.expected_resource_use))
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))
        if self.work_root_required and self.work_root is None:
            raise ValueError("operation requires exactly one Work Root")
        if self.work_root is not None and type(self.work_root) not in (GoalWorkRoot, DutyWorkRoot):
            raise TypeError("work_root must be one concrete Work Root form")
