"""Immutable, coherent CreateTask evaluation snapshot."""
from __future__ import annotations
from dataclasses import dataclass
from aios_protocol.identifiers import ActorId, ApprovalId, AuthorityGrantId, DecisionId, GoalId, OrganizationId, ResourceId
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import RecordTypeVersion

@dataclass(frozen=True, slots=True)
class EvaluationSnapshot:
    generation: str
    organization_id: OrganizationId
    organization_active: bool
    actor_organizations: FrozenMap
    goal_organizations: FrozenMap
    active_goals: frozenset[GoalId]
    decision_organizations: FrozenMap
    complete_decisions: frozenset[DecisionId]
    decision_goal_links: FrozenMap
    authority_organizations: FrozenMap
    approval_organizations: FrozenMap
    resource_organizations: FrozenMap
    existing_task_ids: frozenset[str]
    suspended_actor_ids: frozenset[ActorId]
    incident_blocked: bool
    stream_position: int
    supported_operations: FrozenMap

    def __post_init__(self) -> None:
        for name in ("actor_organizations","goal_organizations","decision_organizations","decision_goal_links",
                     "authority_organizations","approval_organizations","resource_organizations","supported_operations"):
            object.__setattr__(self,name,FrozenMap(getattr(self,name)))
        object.__setattr__(self, "active_goals", frozenset(self.active_goals))
        object.__setattr__(self, "complete_decisions", frozenset(self.complete_decisions))
        object.__setattr__(self, "existing_task_ids", frozenset(self.existing_task_ids))
        object.__setattr__(self, "suspended_actor_ids", frozenset(self.suspended_actor_ids))
        if self.stream_position < 0:
            raise ValueError("stream position cannot be negative")

@dataclass(frozen=True, slots=True)
class SnapshotUnavailable:
    safe_detail: str

SnapshotResult = EvaluationSnapshot | SnapshotUnavailable
