"""Deterministic in-memory runtime Event store for tests, never production use."""
from __future__ import annotations

from threading import Lock

from aios_protocol.events import EventRecord
from aios_protocol.identifiers import OrganizationId

from aios_protocol.reason_codes import ReasonCode

from ..idempotency import IdempotencyInspection, IdempotencyState
from ..runtime import (
    AppendConfirmed, AppendConflict, AppendIdempotencyConflict,
    AppendPreviouslyRecorded, AppendRejected, RuntimeAppendBatch,
)


class StoredRuntimeIdempotency:
    __slots__=("fingerprint","result")
    def __init__(self,fingerprint,result):
        self.fingerprint=fingerprint
        self.result=result


class InMemoryRuntimeEventStore:
    def __init__(self) -> None:
        self._lock=Lock()
        self._streams: dict[OrganizationId, tuple[EventRecord, ...]]={}
        self._idempotency={}
        self.read_calls=0
        self.append_calls=0
        self.idempotency_calls=0
        self.builder_calls=0

    def read(self, organization_id: OrganizationId) -> tuple[EventRecord, ...]:
        with self._lock:
            self.read_calls+=1
            return tuple(self._streams.get(organization_id, ()))

    @staticmethod
    def _scope_key(scope):
        return (str(scope.organization_id),str(scope.initiating_actor_id),
                scope.operation_family,scope.idempotency_key)

    def _inspect_unlocked(self,scope,fingerprint):
        existing=self._idempotency.get(self._scope_key(scope))
        if existing is None:
            return IdempotencyInspection(IdempotencyState.NEW)
        if existing.fingerprint==fingerprint:
            return IdempotencyInspection(
                IdempotencyState.EXACT,existing.result,existing.fingerprint)
        return IdempotencyInspection(
            IdempotencyState.CONFLICT,existing.result,existing.fingerprint)

    def inspect_idempotency(self,scope,fingerprint):
        with self._lock:
            self.idempotency_calls+=1
            return self._inspect_unlocked(scope,fingerprint)

    def append_if_current(self, organization_id: OrganizationId,
                          expected_prior_position: int,scope,fingerprint,build_batch):
        with self._lock:
            self.append_calls+=1
            if scope.organization_id!=organization_id:
                return AppendRejected(ReasonCode.INTEGRITY_VERIFICATION_FAILED,
                                      "idempotency scope does not bind Organization")
            inspection=self._inspect_unlocked(scope,fingerprint)
            if inspection.state is IdempotencyState.EXACT:
                return AppendPreviouslyRecorded(inspection.original_disposition)
            if inspection.state is IdempotencyState.CONFLICT:
                return AppendIdempotencyConflict()
            current=self._streams.get(organization_id, ())
            if len(current) != expected_prior_position:
                return AppendConflict(expected_prior_position,len(current))
            try:
                self.builder_calls+=1
                batch=build_batch()
            except Exception:
                return AppendRejected(ReasonCode.APPEND_FAILED,"Event materialization failed")
            if type(batch) is not RuntimeAppendBatch:
                return AppendRejected(ReasonCode.INTEGRITY_VERIFICATION_FAILED,
                                      "Event builder returned an invalid batch")
            candidate=batch.events
            if not candidate:
                return AppendRejected(ReasonCode.INTEGRITY_VERIFICATION_FAILED,
                                      "Event batch must be nonempty")
            expected_stream_id=f"organization:{organization_id}"
            known_event_ids={event.event_id for event in current}
            for offset,event in enumerate(candidate,1):
                if (event.envelope.organization_id != organization_id or
                    event.envelope.initiating_actor_id != scope.initiating_actor_id or
                    str(event.envelope.stream_id) != expected_stream_id or
                    event.envelope.stream_position != expected_prior_position+offset or
                    event.event_id in known_event_ids):
                    return AppendRejected(ReasonCode.INTEGRITY_VERIFICATION_FAILED,
                                          "Event batch violates stream invariants")
                known_event_ids.add(event.event_id)
            if tuple(batch.result.recorded_events)!=candidate:
                return AppendRejected(ReasonCode.INTEGRITY_VERIFICATION_FAILED,
                                      "recorded result does not bind Event batch")
            if (batch.result.audit_record is None or
                batch.result.audit_record.organization_id!=organization_id):
                return AppendRejected(ReasonCode.INTEGRITY_VERIFICATION_FAILED,
                                      "recorded result does not bind Organization audit")
            self._streams[organization_id]=current+candidate
            self._idempotency[self._scope_key(scope)]=StoredRuntimeIdempotency(
                fingerprint,batch.result)
            return AppendConfirmed(
                expected_prior_position+1,len(current)+len(candidate),candidate,batch.result)
