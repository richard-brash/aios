"""Narrow dependency and atomic persistence ports."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from aios_protocol.identifiers import ActorId, OrganizationId
from .gates import GateName, GateResult
from .snapshots import SnapshotResult
from .transaction import KernelTransaction, TransactionResult

class SnapshotReader(Protocol):
    def bind(self, organization_id: OrganizationId, actor_id: ActorId) -> SnapshotResult: ...

class GovernanceEvaluator(Protocol):
    gate: GateName
    def evaluate(self, context: "GateInput") -> GateResult: ...

class IdentityEvaluator(GovernanceEvaluator, Protocol): pass
class OrganizationEvaluator(GovernanceEvaluator, Protocol): pass
class AuthorityEvaluator(GovernanceEvaluator, Protocol): pass
class PolicyEvaluator(GovernanceEvaluator, Protocol): pass
class WorkRootEvaluator(GovernanceEvaluator, Protocol): pass
class DecisionEvaluator(GovernanceEvaluator, Protocol): pass
class ApprovalEvaluator(GovernanceEvaluator, Protocol): pass
class ResourceEvaluator(GovernanceEvaluator, Protocol): pass
class LifecycleEvaluator(GovernanceEvaluator, Protocol): pass
class IncidentEvaluator(GovernanceEvaluator, Protocol): pass

@dataclass(frozen=True, slots=True)
class GovernancePorts:
    organization: OrganizationEvaluator
    identity: IdentityEvaluator
    authority: AuthorityEvaluator
    policy: PolicyEvaluator
    work_root: WorkRootEvaluator
    decision: DecisionEvaluator
    approval: ApprovalEvaluator
    incident: IncidentEvaluator
    lifecycle: LifecycleEvaluator
    resource: ResourceEvaluator

    def by_gate(self) -> dict[GateName, GovernanceEvaluator]:
        ports = (self.organization,self.identity,self.authority,self.policy,self.work_root,
                 self.decision,self.approval,self.incident,self.lifecycle,self.resource)
        mapping = {port.gate: port for port in ports}
        if len(mapping) != len(ports):
            raise ValueError("each governance port must bind one distinct gate")
        return mapping

class AtomicAppendStore(Protocol):
    def inspect_idempotency(self, key: "IdempotencyScope", fingerprint: str) -> "IdempotencyInspection": ...
    def append(self, transaction: KernelTransaction) -> TransactionResult: ...

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .admission import GateInput, IdempotencyInspection, IdempotencyScope
