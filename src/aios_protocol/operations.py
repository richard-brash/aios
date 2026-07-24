"""Structural control-operation messages; no transition decisions live here."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .commands import EntityReference, WorkRoot
from .identifiers import ActorId, CommandId, CorrelationId, IncidentId, MessageId, OperationId
from .reason_codes import ReasonCode
from .validation import require_aware, require_nonempty


class ControlKind(str, Enum):
    SUSPEND = "suspend"
    CANCEL = "cancel"
    TIMEOUT = "timeout"
    RETRY = "retry"
    ESCALATE = "escalate"


@dataclass(frozen=True, slots=True)
class ControlOperation:
    message_id: MessageId
    command_id: CommandId
    operation_id: OperationId
    correlation_id: CorrelationId
    initiating_actor_id: ActorId
    kind: ControlKind
    target: EntityReference
    work_root: WorkRoot
    effective_at: datetime
    reason_code: ReasonCode
    safe_detail: str
    incident_id: IncidentId | None = None
    prior_operation_id: OperationId | None = None

    def __post_init__(self) -> None:
        require_aware(self.effective_at, type(self).__name__, "effective_at")
        require_nonempty(self.safe_detail, type(self).__name__, "safe_detail")
        if self.kind is ControlKind.RETRY and self.prior_operation_id is None:
            raise ValueError("retry must identify the prior operation")
