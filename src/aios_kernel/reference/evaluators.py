"""Evidence-preserving configurable evaluators; missing configuration never allows."""
from dataclasses import dataclass
from aios_protocol.identifiers import IntegrityReference
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap
from ..gates import GateName, GateResult, GateStatus

@dataclass
class ConfiguredEvaluator:
    gate: GateName
    result: GateResult
    calls: int = 0
    trace: list[GateName] | None = None
    def evaluate(self, context):
        self.calls += 1
        if self.trace is not None: self.trace.append(self.gate)
        return self.result

def allow(gate, evidence=("evidence:configured",), *, reservation=None, approval_use=None):
    return ConfiguredEvaluator(gate, GateResult(gate,GateStatus.PASS,None,FrozenMap({"fixture":"1"}),
        tuple(IntegrityReference(x) for x in evidence),"configured pass","none",FrozenMap({"source":"fixture"}),reservation,approval_use))
def deny(gate, reason, detail="configured denial"):
    return ConfiguredEvaluator(gate, GateResult(gate,GateStatus.DENY,reason,FrozenMap(),(),detail,"correct and resubmit",FrozenMap()))
def unavailable(gate, reason=ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE):
    return ConfiguredEvaluator(gate, GateResult(gate,GateStatus.UNAVAILABLE,reason,FrozenMap(),(),"dependency unavailable","retry after recovery",FrozenMap()))
def indeterminate(gate, reason=ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE):
    return ConfiguredEvaluator(gate, GateResult(gate,GateStatus.INDETERMINATE,reason,FrozenMap(),(),"result indeterminate","escalate",FrozenMap()))
