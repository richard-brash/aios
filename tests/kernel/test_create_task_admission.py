"""Eighty behavioral acceptance scenarios for the narrow CreateTask slice."""
from __future__ import annotations
import dataclasses, pathlib, unittest
from datetime import datetime, timezone

from aios_kernel.admission import CreateTaskAdmission
from aios_kernel.create_task import CreateTaskCommand, InitialTaskState
from aios_kernel.gates import GateName
from aios_kernel.projections import compare_projection, rebuild_task_projection
from aios_kernel.ports import GovernancePorts
from aios_kernel.reference import BoundSnapshotReader, DeterministicIdentifiers, Fault, FixedClock, InMemoryStore, allow, deny, indeterminate, unavailable
from aios_kernel.snapshots import EvaluationSnapshot, SnapshotUnavailable
from aios_kernel.transaction import TransactionStatus
from aios_protocol.commands import CommandSubmission, DutyWorkRoot, EntityReference, GoalWorkRoot, ResourceDimension, ResourceEstimate, Reversibility, RiskClass, ToolRequestDetails
from aios_protocol.dispositions import Accepted, PreviouslyAdmitted, Rejected
from aios_protocol.envelope import CallerEnvelope
from aios_protocol.identifiers import *
from aios_protocol.reason_codes import ReasonCode
from aios_protocol.validation import FrozenMap, StructuralValidationError
from aios_protocol.versions import PayloadVersion, RecordTypeVersion
from conformance_map import SCENARIO_MAP

T=datetime(2035,1,2,3,4,5,tzinfo=timezone.utc); V=RecordTypeVersion("1.0")

def snapshot(org=OrganizationId("org-1"), **changes):
    values=dict(generation="snapshot-1",organization_id=org,organization_active=True,
      actor_organizations=FrozenMap({"actor-1":org}),goal_organizations=FrozenMap({"goal-1":org}),
      active_goals=frozenset({GoalId("goal-1")}),decision_organizations=FrozenMap({"decision-1":org}),
      complete_decisions=frozenset({DecisionId("decision-1")}),decision_goal_links=FrozenMap({"decision-1":GoalId("goal-1")}),
      authority_organizations=FrozenMap({"grant-1":org}),approval_organizations=FrozenMap({"approval-1":org}),
      resource_organizations=FrozenMap({"resource-1":org}),existing_task_ids=frozenset(),suspended_actor_ids=frozenset(),
      incident_blocked=False,stream_position=0,supported_operations=FrozenMap({"CreateTask":V}))
    values.update(changes); return EvaluationSnapshot(**values)

def command(org=OrganizationId("org-1"), **changes):
    env=CallerEnvelope(MessageId("message-1"),"CommandSubmission",org,ActorId("actor-1"),CorrelationId("corr-1"),T,
      "internal","create proposed task","CreateTask",PayloadVersion("1.0"))
    sub=CommandSubmission(env,CommandId("command-1"),OperationId("operation-1"),"CreateTask",V,
      (EntityReference("Task","task-1",0),),"idem-1",GoalWorkRoot(GoalId("goal-1")),True,
      (AuthorityGrantId("grant-1"),),("policy-1",),DecisionId("decision-1"),(),(),FrozenMap(),RiskClass.REVERSIBLE,
      Reversibility(True,IntegrityReference("restore-1"),"event replay","before assignment"),(),FrozenMap({"state":"proposed"}),FrozenMap({"incident":"stop"}),None)
    values=dict(submission=sub,proposed_task_id="task-1",title="Draft plan",purpose="Produce reviewable proposal",
                initial_state=InitialTaskState.PROPOSED,expected_stream_position=0)
    values.update(changes); return CreateTaskCommand(**values)

def evaluators(overrides=None, trace=None, reservation=None, approval=None):
    external=(GateName.ORGANIZATION,GateName.IDENTITY,GateName.INCIDENT,GateName.WORK_ROOT,GateName.DECISION,
              GateName.AUTHORITY,GateName.POLICY,GateName.APPROVAL,GateName.RESOURCE,GateName.LIFECYCLE)
    items={g:allow(g,reservation=reservation if g is GateName.RESOURCE else None,
                     approval_use=approval if g is GateName.APPROVAL else None) for g in external}
    if overrides: items.update(overrides)
    for item in items.values(): item.trace=trace
    return GovernancePorts(items[GateName.ORGANIZATION],items[GateName.IDENTITY],items[GateName.AUTHORITY],
      items[GateName.POLICY],items[GateName.WORK_ROOT],items[GateName.DECISION],items[GateName.APPROVAL],
      items[GateName.INCIDENT],items[GateName.LIFECYCLE],items[GateName.RESOURCE])

def engine(cmd=None,snap=None,fault=Fault.NONE,overrides=None,trace=None,reservation=None,approval=None,store=None,ids=None):
    store=store or InMemoryStore(fault); ids=ids or DeterministicIdentifiers(
      [f"disp-{i}" for i in range(20)],[f"audit-{i}" for i in range(20)],[f"event-{i}" for i in range(200)])
    app=CreateTaskAdmission(clock=FixedClock(T),identifiers=ids,snapshots=BoundSnapshotReader(snap or snapshot()),
      evaluators=evaluators(overrides,trace,reservation,approval),store=store)
    return app,store,ids,(cmd or command())

class CreateTaskBehavior(unittest.TestCase):
    def test_conformance_mapping_is_complete(self):
        self.assertEqual(set(SCENARIO_MAP), set(range(1, 81)))
        specification=(pathlib.Path(__file__).parents[2]/"docs"/"specifications"/"KERNEL_CONFORMANCE.md").read_text()
        self.assertTrue(all(code in specification for code in SCENARIO_MAP.values()))

    def scenario(self,n):
        app,store,ids,cmd=engine()
        if n in {1,2,3,4,5,6,7,8,47,70}:
            result=app.admit(cmd); self.assertEqual(result.status,TransactionStatus.CONFIRMED); self.assertIsInstance(result.disposition,Accepted)
            stream=store.stream(OrganizationId("org-1")); tasks=store.task_projection(OrganizationId("org-1"))
            checks={1:isinstance(result.disposition,Accepted),2:[e.event_type for e in stream]==["CommandAccepted","TaskCreated","DecisionLinked","WorkRootLinked","AuditLinked"],
              3:tasks[0].lifecycle_state=="proposed",4:[e.envelope.stream_position for e in stream]==list(range(1,6)),
              5:all(e.envelope.evaluation_time==T for e in stream),6:all(str(e.event_id).startswith("event-") for e in stream),
              7:all(e.audit_record_id in store.audits for e in stream),8:rebuild_task_projection(stream)==tasks,47:tasks[0].lifecycle_state=="proposed",70:compare_projection(stream,tasks).equivalent}
            self.assertTrue(checks[n]); return
        if n==9:
            a,s,_,c=engine(); b,t,_,d=engine(); a.admit(c); b.admit(d); self.assertEqual(s.stream(OrganizationId("org-1")),t.stream(OrganizationId("org-1"))); return
        if n==10:
            a,s,_,c=engine(); a.admit(c); report=compare_projection(s.stream(OrganizationId("org-1")),s.task_projection(OrganizationId("org-1"))); self.assertTrue(report.equivalent); return
        if n==11:
            source="\n".join(p.read_text() for p in (pathlib.Path(__file__).parents[2]/"src"/"aios_kernel").rglob("*.py"));
            for token in ("datetime.now(","datetime.utcnow(","time.time(","random.","uuid.","os.environ","getenv(","socket."): self.assertNotIn(token,source)
            return
        if n==12:
            result=app.admit(cmd); audit=next(iter(store.audits.values())); self.assertEqual([x.gate for x in audit.evaluation_facts],list(GateName)); return
        if n in {13,14,15,16,28,29,30,31,32,33,34,36,37,38,39,40,41,46}:
            mapping={13:(GateName.IDENTITY,deny(GateName.IDENTITY,ReasonCode.IDENTITY_UNKNOWN)),14:(GateName.POLICY,unavailable(GateName.POLICY,ReasonCode.POLICY_UNAVAILABLE)),
             15:(GateName.AUTHORITY,indeterminate(GateName.AUTHORITY)),16:(GateName.POLICY,deny(GateName.POLICY,ReasonCode.POLICY_DENIED)),
             28:(GateName.AUTHORITY,deny(GateName.AUTHORITY,ReasonCode.AUTH_MISSING)),29:(GateName.AUTHORITY,deny(GateName.AUTHORITY,ReasonCode.AUTH_EXPIRED)),
             30:(GateName.AUTHORITY,deny(GateName.AUTHORITY,ReasonCode.AUTH_REVOKED)),31:(GateName.AUTHORITY,deny(GateName.AUTHORITY,ReasonCode.AUTH_INSUFFICIENT)),
             32:(GateName.AUTHORITY,deny(GateName.AUTHORITY,ReasonCode.AUTH_DELEGATION_INVALID)),33:(GateName.POLICY,deny(GateName.POLICY,ReasonCode.POLICY_DENIED)),
             34:(GateName.POLICY,unavailable(GateName.POLICY,ReasonCode.POLICY_UNAVAILABLE)),36:(GateName.APPROVAL,deny(GateName.APPROVAL,ReasonCode.APPROVAL_MISSING)),
             37:(GateName.APPROVAL,deny(GateName.APPROVAL,ReasonCode.APPROVAL_EXPIRED)),38:(GateName.APPROVAL,deny(GateName.APPROVAL,ReasonCode.APPROVAL_EXHAUSTED)),
             39:(GateName.APPROVAL,deny(GateName.APPROVAL,ReasonCode.APPROVAL_OUT_OF_SCOPE)),40:(GateName.AUTHORITY,deny(GateName.AUTHORITY,ReasonCode.AUTH_MISSING)),
             41:(GateName.RESOURCE,deny(GateName.RESOURCE,ReasonCode.RESOURCE_UNAVAILABLE)),46:(GateName.POLICY,deny(GateName.POLICY,ReasonCode.POLICY_DENIED))}
            gate,override=mapping[n]; later=allow(GateName.RESOURCE); configured={gate:override}
            if gate is not GateName.RESOURCE: configured[GateName.RESOURCE]=later
            app,store,_,cmd=engine(overrides=configured); result=app.admit(cmd)
            self.assertIsInstance(result.disposition,Rejected); self.assertEqual(result.disposition.reason_code,override.result.reason_code)
            if n==13:self.assertEqual(later.calls,0)
            if n==16:self.assertEqual(next(iter(store.audits.values())).evaluation_facts[-1].gate,gate)
            self.assertFalse(store.task_projection(OrganizationId("org-1"))); return
        if n in {17,18,19,20,21,22}:
            foreign=OrganizationId("org-2"); s=snapshot()
            changes={17:("actor_organizations",FrozenMap({"actor-1":foreign})),18:("goal_organizations",FrozenMap({"goal-1":foreign})),
              19:("decision_organizations",FrozenMap({"decision-1":foreign})),20:("approval_organizations",FrozenMap({"approval-1":foreign})),
              21:("resource_organizations",FrozenMap({"resource-1":foreign}))}
            c=command();
            if n==20:c=dataclasses.replace(c,submission=dataclasses.replace(c.submission,approval_references=(ApprovalId("approval-1"),)))
            if n==21:c=dataclasses.replace(c,submission=dataclasses.replace(c.submission,expected_resource_use=(ResourceEstimate(ResourceId("resource-1"),ResourceDimension.MONEY,1,"USD",1),)))
            if n==22: changes[22]=("goal_organizations",FrozenMap({"goal-1":foreign}))
            key,val=changes[n]; app,store,_,_=engine(cmd=c,snap=dataclasses.replace(s,**{key:val})); result=app.admit(c)
            self.assertEqual(result.disposition.reason_code,ReasonCode.ORG_BOUNDARY_VIOLATION); self.assertNotIn("org-2",result.disposition.safe_detail); return
        if n in {23,24,25,26,27,48,49,76,77,78,79}:
            c=cmd; s=snapshot()
            if n==23:
                with self.assertRaises(ValueError): dataclasses.replace(c.submission,work_root=None)
                return
            if n==24:s=dataclasses.replace(s,active_goals=frozenset())
            if n in {25,79}:c=dataclasses.replace(c,submission=dataclasses.replace(c.submission,work_root=DutyWorkRoot("maintenance","policy:x",ActorId("actor-1"),"one task","review")))
            if n==26:s=dataclasses.replace(s,complete_decisions=frozenset())
            if n==27:s=dataclasses.replace(s,decision_goal_links=FrozenMap({"decision-1":GoalId("other-goal")}))
            if n==48:c=dataclasses.replace(c,initial_state=InitialTaskState.ACTIVE)
            if n==49:s=dataclasses.replace(s,existing_task_ids=frozenset({"task-1"}))
            if n==76:c=dataclasses.replace(c,submission=dataclasses.replace(c.submission,operation_type="CreateGoal"))
            if n==77:c=dataclasses.replace(c,submission=dataclasses.replace(c.submission,operation_version=RecordTypeVersion("2.0")))
            if n==78:c=dataclasses.replace(c,submission=dataclasses.replace(c.submission,tool_request=ToolRequestDetails(ToolId("tool-1"),"invoke",V)))
            app,store,_,_=engine(cmd=c,snap=s); result=app.admit(c); self.assertIsInstance(result.disposition,Rejected); self.assertFalse(store.task_projection(OrganizationId("org-1"))); return
        if n==35:
            app,store,_,cmd=engine(overrides={GateName.AUTHORITY:deny(GateName.AUTHORITY,ReasonCode.AUTH_MISSING)}); self.assertEqual(app.admit(cmd).disposition.reason_code,ReasonCode.AUTH_MISSING); return
        if n in {42,43}:
            app,store,_,cmd=engine(reservation="reservation-1" if n==42 else None,approval="approval-use-1" if n==43 else None); app.admit(cmd)
            self.assertEqual(store.resource_transitions if n==42 else store.approval_use_transitions,["reservation-1" if n==42 else "approval-use-1"]); return
        if n in {44,45,62,63,64,65}:
            fault={44:Fault.APPEND_FAILURE,45:Fault.APPEND_FAILURE,62:Fault.APPEND_FAILURE,63:Fault.AUDIT_FAILURE,64:Fault.PROJECTION_FAILURE,65:Fault.IDEMPOTENCY_FAILURE}[n]
            app,store,_,cmd=engine(fault=fault,reservation="r",approval="a"); result=app.admit(cmd); self.assertEqual(result.status,TransactionStatus.APPEND_FAILURE)
            self.assertFalse(store.streams); self.assertFalse(store.tasks); self.assertFalse(store.resource_transitions); self.assertFalse(store.approval_use_transitions); return
        if n==50:
            with self.assertRaises(StructuralValidationError): EntityReference("Task"," bad",0)
            return
        if n==51:
            self.assertNotIn("stream_position",cmd.submission.envelope.__dataclass_fields__); self.assertNotIn("event_id",cmd.__dataclass_fields__); return
        if n in {52,53,54,55,58}:
            app,store,ids,cmd=engine(reservation="r",approval="a"); first=app.admit(cmd); calls=len(ids.calls); before=len(store.stream(cmd.submission.envelope.organization_id)); second=app.admit(cmd)
            self.assertIsInstance(second.disposition,PreviouslyAdmitted); self.assertEqual(len(store.stream(cmd.submission.envelope.organization_id)),before); self.assertEqual(len(ids.calls),calls)
            self.assertEqual(store.resource_transitions,["r"]); self.assertEqual(store.approval_use_transitions,["a"]); return
        if n==56:
            app,store,ids,cmd=engine(); app.admit(cmd)
            changed=dataclasses.replace(cmd,title="Different")
            second,_,_,_=engine(cmd=changed,snap=dataclasses.replace(snapshot(),stream_position=5),store=store)
            result=second.admit(changed); self.assertEqual(result.disposition.reason_code,ReasonCode.IDEMPOTENCY_CONFLICT)
            third,_,_,_=engine(cmd=cmd,snap=dataclasses.replace(snapshot(),stream_position=6),store=store)
            self.assertIsInstance(third.admit(cmd).disposition,PreviouslyAdmitted)
            self.assertEqual(len(store.task_projection(cmd.submission.envelope.organization_id)),1); return
        if n==57:
            shared=InMemoryStore(); a,_,_,c=engine(store=shared); a.admit(c); org2=OrganizationId("org-2"); c2=command(org2); s2=snapshot(org2); b,_,_,_=engine(cmd=c2,snap=s2,store=shared); self.assertIsInstance(b.admit(c2).disposition,Accepted); return
        if n in {59,66,67,68,69}:
            fault=Fault.UNCERTAIN_BEFORE if n in {66} else Fault.UNCERTAIN_AFTER
            app,store,_,cmd=engine(fault=fault); result=app.admit(cmd); self.assertEqual(result.status,TransactionStatus.OUTCOME_UNCERTAIN); self.assertIsNone(result.disposition)
            if n in {59,69}: self.assertEqual(app.admit(cmd).status,TransactionStatus.OUTCOME_UNCERTAIN)
            return
        if n in {60,61}:
            app,store,_,cmd=engine(fault=Fault.CONCURRENCY); result=app.admit(cmd); self.assertEqual(result.status,TransactionStatus.CONCURRENCY_CONFLICT); self.assertFalse(store.tasks); return
        if n==71:
            app,store,_,cmd=engine(); app.admit(cmd); corrupted=(dataclasses.replace(store.task_projection(cmd.submission.envelope.organization_id)[0],title="corrupt"),); self.assertFalse(compare_projection(store.stream(cmd.submission.envelope.organization_id),corrupted).equivalent); return
        if n==72:
            app,store,_,cmd=engine(); app.admit(cmd); reversed_events=tuple(reversed(store.stream(cmd.submission.envelope.organization_id)))
            with self.assertRaises(ValueError): rebuild_task_projection(reversed_events)
            return
        if n==73:
            app,store,_,cmd=engine(); app.admit(cmd); bad=dataclasses.replace(store.stream(cmd.submission.envelope.organization_id)[1],audit_record_id=AuditRecordId("missing")); self.assertNotIn(bad.audit_record_id,store.audits); return
        if n in {74,75}:
            app,store,ids,cmd=engine(); app.admit(cmd); calls=len(ids.calls); before=store.stream(cmd.submission.envelope.organization_id); rebuild_task_projection(before); self.assertEqual(len(ids.calls),calls); self.assertEqual(store.stream(cmd.submission.envelope.organization_id),before); return
        if n==80:
            source="\n".join(p.read_text() for p in (pathlib.Path(__file__).parents[2]/"src"/"aios_kernel").rglob("*.py"));
            for term in ("scheduler","subscriber runtime","model call","Tool execution"): self.assertNotIn(term,source)
            return
        self.fail(f"unimplemented scenario {n}")

def _make_test(number):
    def test(self): self.scenario(number)
    test.__name__=f"test_{number:02d}"; test.__doc__=f"KERNEL_CONFORMANCE scenario {number}."
    return test
for _number in range(1,81): setattr(CreateTaskBehavior,f"test_{_number:02d}",_make_test(_number))
