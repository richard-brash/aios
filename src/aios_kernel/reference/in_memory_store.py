"""Atomic, fault-injectable reference store; not production infrastructure."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from aios_protocol.dispositions import Accepted
from aios_protocol.identifiers import IntegrityReference, OrganizationId
from aios_protocol.reason_codes import ReasonCode
from ..admission import IdempotencyInspection, IdempotencyScope, IdempotencyState
from ..projections import TaskProjection, rebuild_task_projection
from ..transaction import KernelTransaction, TransactionResult, TransactionStatus

class Fault(str, Enum):
    NONE="none"; APPEND_FAILURE="append_failure"; CONCURRENCY="concurrency"
    UNCERTAIN_BEFORE="uncertain_before"; UNCERTAIN_AFTER="uncertain_after"
    PROJECTION_FAILURE="projection_failure"; AUDIT_FAILURE="audit_failure"; IDEMPOTENCY_FAILURE="idempotency_failure"

@dataclass(frozen=True, slots=True)
class StoredIdempotency:
    fingerprint: str; disposition: object; uncertain: bool=False

class InMemoryStore:
    def __init__(self, fault=Fault.NONE):
        self._lock=Lock(); self.fault=fault; self.streams={}; self.dispositions={}; self.audits={}; self.tasks={}
        self.idempotency={}; self.resource_transitions=[]; self.approval_use_transitions=[]; self.append_calls=0

    @staticmethod
    def _scope_key(scope): return (scope.organization_id,scope.initiating_actor_id,scope.operation_family,scope.idempotency_key)
    def inspect_idempotency(self, scope, fingerprint):
        existing=self.idempotency.get(self._scope_key(scope))
        if existing is None: return IdempotencyInspection(IdempotencyState.NEW)
        if existing.uncertain: return IdempotencyInspection(IdempotencyState.UNCERTAIN,reconciliation_reference=IntegrityReference("reconcile:idempotency"))
        if existing.fingerprint==fingerprint: return IdempotencyInspection(IdempotencyState.EXACT,existing.disposition,existing.fingerprint)
        return IdempotencyInspection(IdempotencyState.CONFLICT,existing.disposition,existing.fingerprint)

    def append(self, tx):
        with self._lock:
            self.append_calls += 1
            stream=tuple(self.streams.get(tx.organization_id, ()))
            if self.fault is Fault.CONCURRENCY or len(stream)!=tx.expected_prior_position:
                return TransactionResult(TransactionStatus.CONCURRENCY_CONFLICT,None,ReasonCode.STREAM_CONCURRENCY_CONFLICT)
            if self.fault in {Fault.APPEND_FAILURE,Fault.PROJECTION_FAILURE,Fault.AUDIT_FAILURE,Fault.IDEMPOTENCY_FAILURE}:
                return TransactionResult(TransactionStatus.APPEND_FAILURE,None,ReasonCode.APPEND_FAILED)
            if self.fault is Fault.UNCERTAIN_BEFORE:
                if tx.idempotency_registration:
                    reg=tx.idempotency_registration; key=(str(reg.organization_id),reg.actor_id,reg.operation_family,reg.idempotency_key)
                    self.idempotency[key]=StoredIdempotency(reg.fingerprint,tx.disposition,True)
                return TransactionResult(TransactionStatus.OUTCOME_UNCERTAIN,None,ReasonCode.APPEND_OUTCOME_UNCERTAIN,
                    mutation_may_have_occurred=False,reconciliation_reference=IntegrityReference("reconcile:before"))
            new_stream=stream+tx.events
            new_tasks=rebuild_task_projection(new_stream)
            self.streams[tx.organization_id]=new_stream
            self.dispositions[tx.disposition.envelope.message_id]=tx.disposition
            self.audits[tx.audit_record.audit_record_id]=tx.audit_record
            self.tasks[tx.organization_id]=new_tasks
            self.resource_transitions.extend(tx.resource_transitions)
            self.approval_use_transitions.extend(tx.approval_use_transitions)
            if tx.idempotency_registration:
                reg=tx.idempotency_registration; key=(str(reg.organization_id),reg.actor_id,reg.operation_family,reg.idempotency_key)
                self.idempotency[key]=StoredIdempotency(reg.fingerprint,tx.disposition,self.fault is Fault.UNCERTAIN_AFTER)
            if self.fault is Fault.UNCERTAIN_AFTER:
                return TransactionResult(TransactionStatus.OUTCOME_UNCERTAIN,None,ReasonCode.APPEND_OUTCOME_UNCERTAIN,
                    mutation_may_have_occurred=True,reconciliation_reference=IntegrityReference("reconcile:after"))
            return TransactionResult(TransactionStatus.CONFIRMED,tx.disposition,None,
                tx.events[0].envelope.stream_position,tx.events[-1].envelope.stream_position)

    def stream(self, organization_id): return tuple(self.streams.get(organization_id, ()))
    def task_projection(self, organization_id): return tuple(self.tasks.get(organization_id, ()))
