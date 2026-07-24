"""Fixed gate vocabulary and evidence-preserving results."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from aios_protocol.identifiers import IntegrityReference
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap

class GateName(str, Enum):
    STRUCTURE="structure"; SUPPORTED_OPERATION="supported_operation"; ORGANIZATION="organization"
    IDENTITY="identity"; IDEMPOTENCY="idempotency"; AUTHORITY="authority"; POLICY="policy"
    WORK_ROOT="work_root"; DECISION="decision"; APPROVAL="approval"; TARGET="target"
    INCIDENT="incident"; LIFECYCLE="lifecycle"; RESOURCE="resource"; FINAL_INVARIANT="final_invariant"

GATE_ORDER = (
    GateName.STRUCTURE,
    GateName.SUPPORTED_OPERATION,
    GateName.ORGANIZATION,
    GateName.IDENTITY,
    GateName.IDEMPOTENCY,
    GateName.AUTHORITY,
    GateName.POLICY,
    GateName.WORK_ROOT,
    GateName.DECISION,
    GateName.APPROVAL,
    GateName.TARGET,
    GateName.INCIDENT,
    GateName.LIFECYCLE,
    GateName.RESOURCE,
    GateName.FINAL_INVARIANT,
)

class GateStatus(str, Enum):
    PASS="pass"; DENY="deny"; UNAVAILABLE="unavailable"; INDETERMINATE="indeterminate"

@dataclass(frozen=True, slots=True)
class GateResult:
    gate: GateName
    status: GateStatus
    reason_code: ReasonCode | None
    evaluated_versions: FrozenMap
    evidence_references: tuple[IntegrityReference, ...]
    safe_explanation: str
    reevaluation_guidance: str
    audit_facts: FrozenMap
    reservation_transition: object | None = None
    approval_use_transition: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evaluated_versions", FrozenMap(self.evaluated_versions))
        object.__setattr__(self, "audit_facts", FrozenMap(self.audit_facts))
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))
        if self.status is GateStatus.PASS and self.reason_code is not None:
            raise ValueError("passing gate cannot have failure reason")
        if self.status is not GateStatus.PASS and self.reason_code is None:
            raise ValueError("nonpassing gate requires normative reason")

    @property
    def passed(self) -> bool: return self.status is GateStatus.PASS
