"""Validated, runtime-distinct logical identifier value types."""

from __future__ import annotations

import re


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,254}$")


class Identifier(str):
    """Base class. Concrete identifier classes are not interchangeable in validators."""

    def __new__(cls, value: str):
        if cls is Identifier:
            raise TypeError("Identifier must be constructed through a concrete type")
        if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
            raise ValueError(f"invalid {cls.__name__}")
        return str.__new__(cls, value)

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and str.__eq__(self, other)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((type(self), str(self)))


class MessageId(Identifier): pass
class OrganizationId(Identifier): pass
class ActorId(Identifier): pass
class CommandId(Identifier): pass
class EventId(Identifier): pass
class StreamId(Identifier): pass
class CorrelationId(Identifier): pass
class OperationId(Identifier): pass
class DeliveryId(Identifier): pass
class DispatchId(Identifier): pass
class AttemptId(Identifier): pass
class ScheduleId(Identifier): pass
class ScheduleInstanceId(Identifier): pass
class SubscriptionId(Identifier): pass
class ApprovalId(Identifier): pass
class ApprovalUseId(Identifier): pass
class AuthorityGrantId(Identifier): pass
class BudgetId(Identifier): pass
class CapabilityId(Identifier): pass
class DecisionId(Identifier): pass
class ResourceId(Identifier): pass
class MemoryRecordId(Identifier): pass
class AuditRecordId(Identifier): pass
class IntegrityReference(Identifier): pass
class RoleId(Identifier): pass
class RoleAssignmentId(Identifier): pass
class MissionId(Identifier): pass
class PolicyId(Identifier): pass
class GoalId(Identifier): pass
class IncidentId(Identifier): pass
class ToolId(Identifier): pass
class ExternalOperationId(Identifier): pass
class ProjectionId(Identifier): pass
class CheckpointId(Identifier): pass


IDENTIFIER_TYPES = (
    MessageId, OrganizationId, ActorId, CommandId, EventId, StreamId,
    CorrelationId, OperationId, DeliveryId, DispatchId, AttemptId,
    ScheduleId, ScheduleInstanceId, SubscriptionId, ApprovalId,
    ApprovalUseId, AuthorityGrantId, BudgetId, CapabilityId, DecisionId, ResourceId,
    MemoryRecordId, AuditRecordId, IntegrityReference, RoleId,
    RoleAssignmentId, MissionId, PolicyId, GoalId, IncidentId, ToolId, ExternalOperationId,
    ProjectionId, CheckpointId,
)
