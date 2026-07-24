"""Stable governed references to audit and consequential Decision records."""

from __future__ import annotations

from dataclasses import dataclass

from .commands import WorkRoot
from .identifiers import ActorId, AuditRecordId, CommandId, DecisionId, IntegrityReference, OrganizationId


@dataclass(frozen=True, slots=True)
class AuditReference:
    audit_record_id: AuditRecordId
    organization_id: OrganizationId
    recording_command_id: CommandId
    work_root: WorkRoot
    integrity_reference: IntegrityReference


@dataclass(frozen=True, slots=True)
class ConsequentialDecisionReference:
    decision_id: DecisionId
    initiating_actor_id: ActorId
    deciding_actor_ids: tuple[ActorId, ...]
    evidence_integrity_references: tuple[IntegrityReference, ...]
    contradiction_integrity_references: tuple[IntegrityReference, ...]
    audit_reference: AuditReference

    def __post_init__(self) -> None:
        object.__setattr__(self, "deciding_actor_ids", tuple(self.deciding_actor_ids))
        object.__setattr__(self, "evidence_integrity_references", tuple(self.evidence_integrity_references))
        object.__setattr__(self, "contradiction_integrity_references", tuple(self.contradiction_integrity_references))
        if not self.deciding_actor_ids or not self.evidence_integrity_references:
            raise ValueError("consequential Decision requires deciding Actors and evidence")
