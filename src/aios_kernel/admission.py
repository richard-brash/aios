"""Deterministic CreateTask admission functional core and imperative append shell."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

from aios_protocol.commands import DutyWorkRoot, GoalWorkRoot
from aios_protocol.dispositions import Accepted, PreviouslyAdmitted, Rejected
from aios_protocol.envelope import KernelDispositionEnvelope
from aios_protocol.identifiers import IntegrityReference, StreamId
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap

from .clock import Clock
from .create_task import CREATE_TASK, CreateTaskCommand, InitialTaskState
from .errors import KernelInternalError
from .events import create_authoritative_event
from .gates import GATE_ORDER, GateName, GateResult, GateStatus
from .ids import IdentifierAllocator
from .idempotency import (
    IdempotencyRegistration, IdempotencyScope, IdempotencyState,
    semantic_command_fingerprint,
)
from .ports import AtomicAppendStore, GovernancePorts, SnapshotReader
from .snapshots import EvaluationSnapshot, SnapshotUnavailable
from .transaction import AuditRecord, KernelTransaction, TransactionResult, TransactionStatus

@dataclass(frozen=True, slots=True)
class GateInput:
    command: CreateTaskCommand
    snapshot: EvaluationSnapshot
    evaluation_time: datetime
    prior_results: tuple[GateResult, ...]

@dataclass(frozen=True, slots=True)
class AdmissionContext:
    command: CreateTaskCommand
    evaluation_time: datetime
    snapshot: EvaluationSnapshot
    current_stream_position: int
    gate_results: tuple[GateResult, ...]
    audit_facts: FrozenMap

def _pass(gate: GateName, facts: FrozenMap = FrozenMap()) -> GateResult:
    return GateResult(gate, GateStatus.PASS, None, FrozenMap(), (), "passed", "none", facts)

def _fail(gate: GateName, reason: ReasonCode, detail: str, status: GateStatus = GateStatus.DENY) -> GateResult:
    return GateResult(gate, status, reason, FrozenMap(), (), detail, "submit a new Command after correction", FrozenMap({"failed_gate": gate.value}))

class CreateTaskAdmission:
    """Supports exactly CreateTask; evaluators are evidence-bearing and fail closed."""
    def __init__(self, *, clock: Clock, identifiers: IdentifierAllocator, snapshots: SnapshotReader,
                 evaluators: GovernancePorts, store: AtomicAppendStore) -> None:
        self._clock=clock; self._identifiers=identifiers; self._snapshots=snapshots; self._store=store
        self._evaluators = evaluators.by_gate()

    def admit(self, command: CreateTaskCommand) -> TransactionResult:
        evaluation_time = self._clock.evaluation_time()
        if evaluation_time.tzinfo is None or evaluation_time.utcoffset() is None:
            raise KernelInternalError("KERNEL.CLOCK_INVALID", "authoritative clock returned a naive time")
        snapshot_result = self._snapshots.bind(command.submission.envelope.organization_id,
                                               command.submission.envelope.initiating_actor_id)
        if isinstance(snapshot_result, SnapshotUnavailable):
            return TransactionResult(TransactionStatus.VALIDATION_FAILURE, None,
                                     ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE)
        snapshot = snapshot_result
        results: list[GateResult] = []
        fingerprint = semantic_command_fingerprint(command)
        scope = IdempotencyScope(snapshot.organization_id, command.submission.envelope.initiating_actor_id,
                                 command.submission.operation_type, command.submission.idempotency_key)
        for gate in GATE_ORDER:
            result = self._evaluate_gate(gate, command, snapshot, evaluation_time, tuple(results), scope, fingerprint)
            if gate is GateName.IDEMPOTENCY and result is None:
                # Preflight is advisory; the locked check is authoritative and append
                # repeats it before mutation to close the NEW-to-append race.
                self._store.inspect_idempotency(scope, fingerprint)
                inspection = self._store.enforce_idempotency(scope, fingerprint)
                if inspection.state is IdempotencyState.EXACT:
                    original = inspection.original_disposition
                    if not isinstance(original, (Accepted, Rejected)):
                        raise KernelInternalError("KERNEL.IDEMPOTENCY_INVALID", "original disposition is unavailable")
                    duplicate = PreviouslyAdmitted(original.envelope, original.envelope.message_id,
                        original.event_ids if isinstance(original, Accepted) else ())
                    return TransactionResult(TransactionStatus.PREVIOUSLY_ADMITTED, duplicate, None)
                if inspection.state is IdempotencyState.UNCERTAIN:
                    return TransactionResult(TransactionStatus.OUTCOME_UNCERTAIN, None,
                        ReasonCode.RECONCILIATION_REQUIRED,
                        authoritative_mutation_may_have_occurred=inspection.authoritative_mutation_may_have_occurred,
                        internal_reconciliation_metadata_recorded=inspection.internal_reconciliation_metadata_recorded,
                        reconciliation_reference=inspection.reconciliation_reference)
                if inspection.state is IdempotencyState.CONFLICT:
                    return TransactionResult(TransactionStatus.IDEMPOTENCY_CONFLICT, None,
                                             ReasonCode.IDEMPOTENCY_CONFLICT)
                result = _pass(gate)
            assert result is not None
            results.append(result)
            if not result.passed:
                return self._record_rejection(command, snapshot, evaluation_time, tuple(results), scope, fingerprint, result)
        context = AdmissionContext(command, evaluation_time, snapshot, snapshot.stream_position,
                                   tuple(results), FrozenMap({r.gate.value: r.safe_explanation for r in results}))
        return self._record_acceptance(context, scope, fingerprint)

    def _evaluate_gate(self, gate: GateName, command: CreateTaskCommand, snapshot: EvaluationSnapshot,
                       evaluation_time: datetime, prior: tuple[GateResult, ...], scope: IdempotencyScope,
                       fingerprint: str) -> GateResult | None:
        submission=command.submission; org=submission.envelope.organization_id
        if gate is GateName.STRUCTURE:
            if submission.tool_request is not None: return _fail(gate, ReasonCode.INPUT_MALFORMED, "Tool requests are unsupported")
            return _pass(gate)
        if gate is GateName.SUPPORTED_OPERATION:
            supported=snapshot.supported_operations.get(submission.operation_type)
            if submission.operation_type != CREATE_TASK: return _fail(gate, ReasonCode.VER_UNSUPPORTED, "operation unsupported")
            if supported != submission.operation_version: return _fail(gate, ReasonCode.VER_UNSUPPORTED, "operation version unsupported")
            return _pass(gate)
        if gate is GateName.ORGANIZATION:
            if org != snapshot.organization_id or not snapshot.organization_active: return _fail(gate, ReasonCode.ORG_BOUNDARY_VIOLATION, "Organization boundary unavailable")
            refs = [(snapshot.actor_organizations, submission.envelope.initiating_actor_id),
                    (snapshot.goal_organizations, getattr(submission.work_root, "goal_id", None)),
                    (snapshot.decision_organizations, submission.decision_reference)]
            refs += [(snapshot.authority_organizations, x) for x in submission.authority_references]
            refs += [(snapshot.approval_organizations, x) for x in submission.approval_references]
            refs += [(snapshot.resource_organizations, x.resource_id) for x in submission.expected_resource_use]
            if any(ref is not None and mapping.get(str(ref)) != org for mapping,ref in refs):
                return _fail(gate, ReasonCode.ORG_BOUNDARY_VIOLATION, "referenced record is outside Organization")
            return self._external(gate, command, snapshot, evaluation_time, prior)
        if gate is GateName.INCIDENT:
            if snapshot.incident_blocked or submission.envelope.initiating_actor_id in snapshot.suspended_actor_ids:
                return _fail(gate, ReasonCode.INCIDENT_SUSPENDED, "operation is suspended")
            return self._external(gate, command, snapshot, evaluation_time, prior)
        if gate is GateName.IDEMPOTENCY: return None
        if gate is GateName.TARGET:
            if command.proposed_task_id in snapshot.existing_task_ids: return _fail(gate, ReasonCode.STATE_STALE_VERSION, "Task identity already exists")
            if command.expected_stream_position != snapshot.stream_position: return _fail(gate, ReasonCode.STATE_STALE_VERSION, "expected stream position is stale")
            return _pass(gate)
        if gate is GateName.WORK_ROOT:
            if isinstance(submission.work_root, DutyWorkRoot): return _fail(gate, ReasonCode.VER_UNSUPPORTED, "Duty Work Roots are unsupported by this slice")
            if not isinstance(submission.work_root, GoalWorkRoot): return _fail(gate, ReasonCode.WORK_ROOT_MISSING, "active Goal Work Root required")
            if submission.work_root.goal_id not in snapshot.active_goals: return _fail(gate, ReasonCode.WORK_ROOT_INACTIVE, "Goal is inactive")
            return self._external(gate, command, snapshot, evaluation_time, prior)
        if gate is GateName.DECISION:
            decision=submission.decision_reference
            if decision is None or decision not in snapshot.complete_decisions: return _fail(gate, ReasonCode.DECISION_INCOMPLETE, "Decision is incomplete")
            if snapshot.decision_goal_links.get(str(decision)) != submission.work_root.goal_id:
                return _fail(gate, ReasonCode.DECISION_INCOMPLETE, "Decision is unrelated to Goal")
            return self._external(gate, command, snapshot, evaluation_time, prior)
        if gate is GateName.LIFECYCLE:
            if command.initial_state is not InitialTaskState.PROPOSED:
                return _fail(gate, ReasonCode.LIFECYCLE_INVALID_TRANSITION, "initial Task state must be proposed")
            return self._external(gate, command, snapshot, evaluation_time, prior)
        if gate is GateName.FINAL_INVARIANT: return _pass(gate)
        return self._external(gate, command, snapshot, evaluation_time, prior)

    def _external(self, gate, command, snapshot, evaluation_time, prior):
        evaluator=self._evaluators.get(gate)
        if evaluator is None:
            return _fail(gate, ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE, "governance evaluator unavailable", GateStatus.UNAVAILABLE)
        result=evaluator.evaluate(GateInput(command,snapshot,evaluation_time,prior))
        if result.gate is not gate: raise KernelInternalError("KERNEL.GATE_MISMATCH", "evaluator returned wrong gate")
        return result

    def _allocate(self, event_count: int):
        try:
            disposition=self._identifiers.disposition_id(); audit=self._identifiers.audit_id()
            events=tuple(self._identifiers.event_id() for _ in range(event_count))
            return disposition,audit,events
        except Exception as exc:
            raise KernelInternalError("KERNEL.ID_EXHAUSTED", "authoritative identifier allocation failed") from None

    def _record_acceptance(self, context, scope, fingerprint):
        command=context.command; reservation=[r.reservation_transition for r in context.gate_results if r.reservation_transition]
        approval=[r.approval_use_transition for r in context.gate_results if r.approval_use_transition]
        types=["CommandAccepted","TaskCreated","DecisionLinked","WorkRootLinked"]
        if reservation: types.append("ResourceReserved")
        if approval: types.append("ApprovalUsed")
        types.append("AuditLinked")
        disposition_id,audit_id,event_ids=self._allocate(len(types))
        events=[]
        for index,(kind,eid) in enumerate(zip(types,event_ids),1):
            payload={"task_id":command.proposed_task_id,"decision_id":command.submission.decision_reference}
            if kind=="TaskCreated": payload.update(title=command.title,purpose=command.purpose,lifecycle_state="proposed",entity_version=1)
            events.append(create_authoritative_event(command=command,snapshot=context.snapshot,evaluation_time=context.evaluation_time,
                event_id=eid,stream_position=context.snapshot.stream_position+index,event_type=kind,audit_id=audit_id,
                payload=payload,work_root=command.work_root))
        denv=KernelDispositionEnvelope(disposition_id,"Accepted",context.snapshot.organization_id,
            command.submission.envelope.initiating_actor_id,command.submission.command_id,
            command.submission.envelope.correlation_id,context.evaluation_time,command.submission.envelope.classification,audit_id)
        accepted=Accepted(denv,event_ids,"Task recorded in proposed state",FrozenMap({"task_version":1}))
        audit=AuditRecord(audit_id,context.snapshot.organization_id,command.submission.command_id,context.gate_results,"accepted",IntegrityReference(f"integrity:{audit_id}"))
        reg=IdempotencyRegistration(scope,fingerprint,disposition_id)
        projection=FrozenMap({"task_id":command.proposed_task_id})
        return self._store.append(KernelTransaction(context.snapshot.organization_id,StreamId(f"organization:{context.snapshot.organization_id}"),
            command.expected_stream_position,tuple(events),accepted,audit,reg,projection,tuple(reservation),tuple(approval)))

    def _record_rejection(self, command,snapshot,when,results,scope,fingerprint,failure):
        disposition_id,audit_id,event_ids=self._allocate(1)
        event=create_authoritative_event(command=command,snapshot=snapshot,evaluation_time=when,event_id=event_ids[0],
            stream_position=snapshot.stream_position+1,event_type="CommandRejected",audit_id=audit_id,
            payload={"failed_gate":failure.gate.value,"reason_code":failure.reason_code.value},work_root=command.work_root)
        denv=KernelDispositionEnvelope(disposition_id,"Rejected",snapshot.organization_id,
            command.submission.envelope.initiating_actor_id,command.submission.command_id,
            command.submission.envelope.correlation_id,when,command.submission.envelope.classification,audit_id)
        rejected=Rejected(denv,failure.reason_code,failure.gate.value,failure.safe_explanation)
        audit=AuditRecord(audit_id,snapshot.organization_id,command.submission.command_id,results,"rejected",IntegrityReference(f"integrity:{audit_id}"))
        reg=(None if failure.reason_code is ReasonCode.IDEMPOTENCY_CONFLICT else
             IdempotencyRegistration(scope,fingerprint,disposition_id))
        return self._store.append(KernelTransaction(snapshot.organization_id,StreamId(f"organization:{snapshot.organization_id}"),
            snapshot.stream_position,(event,),rejected,audit,reg,None))
