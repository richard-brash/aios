"""Task projection derived only from authoritative Event history."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from aios_protocol.commands import GoalWorkRoot
from aios_protocol.events import EventRecord
from aios_protocol.identifiers import ActorId, CommandId, DecisionId, EventId, OrganizationId

@dataclass(frozen=True, slots=True)
class TaskProjection:
    task_id: str; organization_id: OrganizationId; title: str; purpose: str; lifecycle_state: str
    work_root: GoalWorkRoot; decision_id: DecisionId; initiating_actor_id: ActorId
    creation_command_id: CommandId; creation_event_id: EventId; created_at: datetime
    entity_version: int; classification: str

@dataclass(frozen=True, slots=True)
class ProjectionComparisonReport:
    equivalent: bool
    replayed: tuple[TaskProjection, ...]
    stored: tuple[TaskProjection, ...]
    safe_detail: str

def rebuild_task_projection(events: tuple[EventRecord, ...]) -> tuple[TaskProjection, ...]:
    tasks: dict[str, TaskProjection] = {}
    for expected_position, event in enumerate(events, 1):
        if event.envelope.stream_position != expected_position:
            raise ValueError("authoritative Event order is not sequential")
        if event.event_type != "TaskCreated":
            continue
        data = event.payload
        decision = data["decision_id"]
        root = event.work_root
        if not isinstance(root, GoalWorkRoot) or not isinstance(decision, DecisionId):
            raise ValueError("TaskCreated history lacks typed Goal or Decision linkage")
        tasks[data["task_id"]] = TaskProjection(
            data["task_id"], event.envelope.organization_id, data["title"], data["purpose"],
            data["lifecycle_state"], root, decision, event.envelope.initiating_actor_id,
            event.envelope.recording_command_id, event.event_id, event.envelope.evaluation_time,
            data["entity_version"], event.envelope.classification,
        )
    return tuple(tasks[key] for key in sorted(tasks))

def compare_projection(events: tuple[EventRecord, ...], stored: tuple[TaskProjection, ...]) -> ProjectionComparisonReport:
    replayed = rebuild_task_projection(events)
    return ProjectionComparisonReport(replayed == stored, replayed, tuple(stored), "equivalent" if replayed == tuple(stored) else "projection divergence")
