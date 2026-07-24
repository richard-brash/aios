"""Deterministic in-memory genesis store for tests; not production persistence."""

from __future__ import annotations

from enum import Enum
from threading import Lock

from aios_protocol.bootstrap import BootstrapPreviouslyAdmitted, BootstrapRequest, BootstrapUncertain
from aios_protocol.events import EventRecord
from aios_protocol.identifiers import IntegrityReference, StreamId
from aios_protocol.reason_codes import ReasonCode

from ..bootstrap_runtime import (
    GenesisAppendCommitted, GenesisAppendPreviouslyAdmitted, GenesisAppendRejected,
    GenesisAppendUncertain, GenesisComparison, compare_genesis_candidates,
    replay_genesis,
)


class GenesisFault(str, Enum):
    NONE = "none"
    FAIL_BEFORE_COMMIT = "fail_before_commit"
    UNCERTAIN_BEFORE_COMMIT = "uncertain_before_commit"
    BUILDER_FAILURE = "builder_failure"


class InMemoryGenesisStore:
    def __init__(self, *, fault: GenesisFault = GenesisFault.NONE,
                 initial_streams: tuple[tuple[StreamId, tuple[EventRecord, ...]], ...] = ()) -> None:
        self._lock = Lock()
        self._streams: dict[StreamId, tuple[EventRecord, ...]] = {
            stream_id: tuple(events) for stream_id, events in initial_streams
        }
        self._registrations: dict[StreamId, tuple[str, BootstrapRequest, object | None]] = {}
        self._fault = fault
        self.builder_calls = 0

    def read(self, stream_id: StreamId):
        with self._lock:
            return tuple(self._streams.get(stream_id, ()))

    def append_genesis(self, *, request, evaluation_time, accepted_decision,
                       expected_prior_position, build_transaction):
        with self._lock:
            stream_id = request.genesis_stream_id
            if accepted_decision.proposal.request != request:
                return GenesisAppendRejected(
                    ReasonCode.INTEGRITY_VERIFICATION_FAILED, "accepted_decision",
                    "recording decision does not match the proposed genesis",
                )
            registration = self._registrations.get(stream_id)
            if registration is not None:
                state, original_request, outcome = registration
                comparison = compare_genesis_candidates(original_request, request)
                if state == "uncertain":
                    uncertain = BootstrapUncertain(
                        request, outcome, ReasonCode.BOOTSTRAP_IDENTITY_QUARANTINED,
                        IntegrityReference(f"quarantine:{stream_id}"),
                        IntegrityReference(f"reconcile:{stream_id}"),
                    )
                    return GenesisAppendUncertain(uncertain)
                if comparison is GenesisComparison.EXACT:
                    previous = BootstrapPreviouslyAdmitted(
                        request, outcome, outcome.evaluation_time, outcome.outcome_integrity_reference,
                    )
                    return GenesisAppendPreviouslyAdmitted(previous)
                return GenesisAppendRejected(
                    ReasonCode.BOOTSTRAP_COMPETING_GENESIS, "competing_genesis",
                    "a materially different genesis is already registered",
                )
            current = self._streams.get(stream_id, ())
            if expected_prior_position != 0 or len(current) != expected_prior_position:
                return GenesisAppendRejected(
                    ReasonCode.STREAM_CONCURRENCY_CONFLICT, "expected_stream",
                    "genesis stream is not empty",
                )
            if self._fault is GenesisFault.UNCERTAIN_BEFORE_COMMIT:
                # Internal retry-blocking metadata only; no authoritative Event mutation.
                self._registrations[stream_id] = ("uncertain", request, evaluation_time)
                uncertain = BootstrapUncertain(
                    request, evaluation_time, ReasonCode.BOOTSTRAP_IDENTITY_QUARANTINED,
                    IntegrityReference(f"quarantine:{stream_id}"),
                    IntegrityReference(f"reconcile:{stream_id}"),
                )
                return GenesisAppendUncertain(uncertain)
            if self._fault is GenesisFault.FAIL_BEFORE_COMMIT:
                return GenesisAppendRejected(ReasonCode.APPEND_FAILED, "append", "genesis append failed")
            try:
                self.builder_calls += 1
                if self._fault is GenesisFault.BUILDER_FAILURE:
                    raise RuntimeError("injected builder boundary failure")
                events, outcome = build_transaction()
            except Exception:
                return GenesisAppendRejected(ReasonCode.APPEND_FAILED, "materialization", "genesis materialization failed")
            events = tuple(events)
            if not events or len(events) != len(request.proposed_founding_events.ordered_events):
                return GenesisAppendRejected(ReasonCode.BOOTSTRAP_INCOMPLETE, "append", "founding Event set is incomplete")
            for position, event in enumerate(events, 1):
                if (
                    event.envelope.stream_id != stream_id
                    or event.envelope.stream_position != position
                    or event.envelope.organization_id != request.organization.organization_id
                    or event.envelope.recording_command_id != request.recording_command.command_id
                    or event.audit_record_id != request.proposed_audit_record_id
                    or event.event_type != request.proposed_founding_events.ordered_events[position - 1].event_type
                ):
                    return GenesisAppendRejected(ReasonCode.INTEGRITY_VERIFICATION_FAILED, "append", "founding Event order is invalid")
            if len({event.event_id for event in events}) != len(events):
                return GenesisAppendRejected(
                    ReasonCode.INTEGRITY_VERIFICATION_FAILED, "append",
                    "founding Event identities are not unique",
                )
            try:
                founded = replay_genesis(events)
            except (TypeError, ValueError):
                return GenesisAppendRejected(
                    ReasonCode.INTEGRITY_VERIFICATION_FAILED, "replay_parity",
                    "founding Event history fails committed-genesis validation",
                )
            if founded.organization.organization_id != request.organization.organization_id:
                return GenesisAppendRejected(
                    ReasonCode.INTEGRITY_VERIFICATION_FAILED, "replay_parity",
                    "founded projection does not bind the proposed Organization",
                )
            self._streams[stream_id] = events
            self._registrations[stream_id] = ("committed", request, outcome)
            return GenesisAppendCommitted(outcome, events)
