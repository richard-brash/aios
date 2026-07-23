"""Pure authoritative Event construction for the CreateTask slice."""
from __future__ import annotations
from datetime import datetime
from aios_protocol.commands import EntityReference, WorkRoot
from aios_protocol.envelope import EventEnvelope
from aios_protocol.events import EpistemicStatus, EventRecord
from aios_protocol.identifiers import AuditRecordId, EventId, IntegrityReference, MessageId, StreamId
from aios_protocol.presence import NOT_APPLICABLE
from aios_protocol.validation import FrozenMap
from aios_protocol.versions import RECORD_V1
from .create_task import CreateTaskCommand
from .snapshots import EvaluationSnapshot

def create_authoritative_event(*, command: CreateTaskCommand, snapshot: EvaluationSnapshot,
    evaluation_time: datetime, event_id: EventId, stream_position: int, event_type: str,
    audit_id: AuditRecordId, payload: dict[str, object], work_root: WorkRoot | None) -> EventRecord:
    envelope=EventEnvelope(MessageId(f"record:{event_id}"),event_type,snapshot.organization_id,
        command.submission.envelope.initiating_actor_id,command.submission.command_id,
        command.submission.envelope.correlation_id,evaluation_time,
        StreamId(f"organization:{snapshot.organization_id}"),stream_position,
        command.submission.envelope.classification,IntegrityReference(f"integrity:{event_id}"))
    return EventRecord(envelope,event_id,event_type,RECORD_V1,(),
        f"message:{command.submission.envelope.message_id}",evaluation_time,
        (EntityReference("Task",command.proposed_task_id,0),),EpistemicStatus.DETERMINISTIC,
        NOT_APPLICABLE,work_root,FrozenMap(),FrozenMap(),FrozenMap(),audit_id,
        IntegrityReference(f"integrity:{event_id}"),payload=FrozenMap(payload))
