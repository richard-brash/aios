# AIOS Governed Work Delegation

**Specification version:** 0.1.0
**Status:** Normative Milestone 3 architecture

## 1. Scope and reconciliation

This specification defines the minimum constitutional envelope for AIOS to
supervise its first Temporary Worker. It refines existing Actor, Temporary
Worker, Role Assignment, Authority Grant, Task, Command, Event, audit, and
replay contracts. It introduces no Work Item, independent Worker identity,
general Grant administration, or alternate execution pipeline.

| Conflict | Constitutional basis | Resolution | Rejected alternative |
|---|---|---|---|
| Work Item versus Task | Task is the smallest independently governed assignable unit | Use the existing Task with this constrained profile | Parallel Work Item or replacement Task |
| Derived permission versus Authority Grant | Consequential action and audit trace to a Grant | Pin one source Grant and prove Task attenuation | Enrollment, Role, Task, Approval, or capability as authority |
| Worker versus Actor | Temporary Worker is an Actor kind | Enrollment is its Organization-scoped specialization sharing `actor_id` | A second identity, credential, or principal |
| Deferred Resources and expiry | Temporary Worker requires a ceiling and expiry or completion | One accepted delegated execution and terminal Task completion | Unbounded execution, ambient expiry, or generalized budgeting |

## 2. Canonical relationships

```text
authenticated Actor (actor_kind=temporary_worker)
  -> Temporary Worker enrollment (same actor_id, one Organization)
  -> active Role Assignment (same Actor, Role, Organization)
  -> active source Authority Grant (recipient is the Actor)
  -> accepted and assigned Task (same Organization and Actor)
  -> accepted delegated capability execution
  -> immutable Organization Events and audit lineage
```

Each arrow is an independently validated authoritative reference. No inverse
collection, cache, model identity, credential, display name, or caller claim
establishes it. The first-worker profile is one-to-one: one Temporary Worker
Actor, enrollment, active Role Assignment, source Grant, and Task. A different
purpose, Grant, Role, Organization, or Task is outside this profile.

## 3. Temporary Worker enrollment

Enrollment is governed activation of the existing Temporary Worker Actor, not
a new entity. Its accepted evidence MUST establish:

- canonical `organization_id` and existing `actor_id` with
  `actor_kind=temporary_worker`;
- one active same-Organization Human or Employee `sponsor_actor_id`;
- one immutable bounded purpose;
- one qualifying `role_assignment_id` once qualification is established;
- one `source_authority_grant_id` whose recipient is the Actor;
- one `task_id` after issuance;
- exact capability and Tool bounds no wider than the Grant;
- one immutable Task-scoped Budget reference with its own `budget_id`, exact
  source-Grant Resource lineage, and Resource dimension and unit
  `accepted_delegated_capability_execution`, authorized limit one, and
  `maximum_accepted_capability_executions=1`;
- terminality of that Task as its completion condition;
- redelegation prohibited; and
- required admission, Decision, Approval, Policy, and audit references.

For this first profile, the Sponsor is also the Role Assignment assigner,
source Grant issuer, and Task issuer. Each capacity remains separately recorded
and validated; identity equality does not collapse governance stages or permit
self-approval where Policy requires separation.

The enrollment uses the existing Temporary Worker lifecycle. Until all facts
needed for a particular transition are present and active, the Actor is
ineligible for Task acceptance or execution. Enrollment conveys eligibility,
never authority. Suspension, revocation, completion, or archival prevents new
activity without erasing Actor identity or accepted history.

## 4. Role Assignment qualification

One canonical Role Assignment binds the Temporary Worker Actor to one active
Role in the same Organization. It requires an eligible assigner and active
enrollment and remains historically addressable after termination.

Role Assignment proves occupational qualification and is a governance input;
it grants no capability authority. Ending it blocks new Task acceptance and
execution. It does not infer cancellation or rewrite prior execution. An
in-progress Task ends only through an explicit terminal Task transition.

The Milestone 3 lifecycle is the existing relationship lifecycle:

```text
nonexistent -> proposed -> active
active -> suspended | expired | revoked
suspended -> active | expired | revoked
suspended | expired | revoked -> archived
```

`RoleAssignmentProposed`, `RoleAssignmentActivated`,
`RoleAssignmentSuspended`, `RoleAssignmentRestored`,
`RoleAssignmentExpired`, `RoleAssignmentRevoked`, and
`RoleAssignmentArchived` are immutable Organization Events for those semantic
transitions. Activation requires the exact Worker Actor and active Role in the
same Organization, an eligible assigner, duty scope, and a review or completion
condition. Termination means expiry or revocation for new qualification;
archival preserves the relationship and its historical use.

## 5. Constrained Task contract

The Milestone 3 Task is the existing Task with these pinned facts at acceptance:

- stable `task_id`, canonical `organization_id`, and exactly one Work Root;
- `issuer_actor_id` and issuer authority evidence;
- assigned Temporary Worker `actor_id` and enrollment evidence;
- qualifying active `role_assignment_id` and Role reference;
- `source_authority_grant_id` and pinned Grant evidence version;
- a nonempty finite ordered set of exact `permitted_capability_ids`, with no
  wildcard, namespace, pattern, or discovery expression;
- immutable input or governed input reference and integrity identifier;
- purpose, expected output, acceptance criteria, risk, and reversibility;
- one immutable `budget_id` referencing the source Grant Resource and using
  Resource dimension and unit
  `accepted_delegated_capability_execution`, authorized limit one, and
  `maximum_accepted_capability_executions=1`, initially unconsumed;
- redelegation prohibited;
- Task terminality as Worker completion condition; and
- issuance, assignment, worker-acceptance, execution, and outcome lineage.

The existing lifecycle remains authoritative:

```text
nonexistent -> proposed -> ready -> assigned -> in_progress
in_progress -> completed | failed
ready | assigned | in_progress | blocked | suspended -> cancelled
```

For this profile, `TaskProposed` is issuance, `TaskAccepted` is governed Task
acceptance, `TaskAssigned` binds the enrollment and Role Assignment, and
`TaskStarted` is the assigned Worker Actor's acceptance of work. Only an
`in_progress` nonterminal Task permits delegated execution. `TaskCompleted`,
`TaskFailed`, or `TaskCancelled` is terminal and atomically records
`WorkerCompleted` for the one-Task enrollment.

Invalid transitions reject without lifecycle mutation. A failed Task is
terminal. Retry is a new Task with explicit causation.

## 6. Authority derivation and attenuation

The source Authority Grant is the sole permission source. Every dimension must
be comparable and the Task equal or narrower:

| Dimension | Attenuation proof |
|---|---|
| Organization | Task, Worker, Assignment, Grant, issuer, and execution share the canonical Organization |
| Recipient | Grant recipient and authenticated Actor equal the enrolled Actor |
| Issuer | Task issuer equals the Sponsor and source Grant issuer, is eligible under the parent Grant chain, and has the delegation right |
| Purpose | Task purpose is within Grant purpose; ambiguity denies |
| Capability | For this profile the Grant's permitted actions enumerate exact `capability_id` values; every Task capability is present and not prohibited |
| Resource | Grant evidence names one source Resource with dimension and unit `accepted_delegated_capability_execution` and limit at least one; the independently identified Task Budget retains that source lineage, uses the same dimension and unit, and has limit exactly one |
| Risk/approval | Task risk is no higher and preserves every approval condition |
| Duration | Task completion condition is no later than Grant applicability |
| Delegation | Task prohibits redelegation and sub-worker creation |
| Policy | Constitution and current Policy may narrow or deny, never expand |

An absent, inactive, revoked, expired, malformed, cross-Organization,
wrong-recipient, incomparable, or insufficient Grant fails closed. Task
acceptance pins its Grant evidence. Each later capability execution revalidates
current Grant applicability because it is a new Action. Revocation blocks new
execution under an accepted Task but leaves prior history intact.

The minimum executable prerequisite is the capability-neutral immutable
`SourceAuthorityGrantClaim` and `SourceAuthorityGrantProof` contract with a
closed `SourceAuthorityGrantDenied` result. It binds one Command and canonical
Organization to Grant identity, versioned Event evidence, issuer, recipient,
exact purpose, exact permitted and prohibited capabilities, one comparable
source-Resource ceiling, an independently identified Task Budget bound that
retains the source Resource lineage, deterministic completion condition,
affirmative delegation basis, evaluated effective lifecycle state, and
authoritative revision and stream position. Purpose containment is exact
normalized equality because the
constitutional purpose is descriptive; no semantic inference or policy
language is introduced. It MUST NOT create, update, revoke, infer, or broaden
Grants. Risk and approval conditions remain independently mandatory governance
constraints and are not invented as fields of this minimal proof.

## 7. Delegated capability execution

Delegated execution is an ordinary `RuntimeCommand` handled only through
`KernelRuntime`. After ordinary admission establishes canonical Organization
and Actor attribution, governance proves:

1. Actor equals the Temporary Worker enrollment Actor;
2. enrollment is active and Sponsor authority remains applicable;
3. Role Assignment and Role are active and same-Organization;
4. Task is assigned to the Actor, `in_progress`, and nonterminal;
5. source Grant is active and covers the exact attempt;
6. requested exact capability appears in the Task allowlist;
7. accepted-execution consumption is zero of one;
8. Task expands no Grant or Policy dimension; and
9. ordinary constitutional and Organization governance approves.

The ceiling check and increment use Organization-scoped concurrency and
idempotency. Acceptance atomically records common accepted-execution lineage,
capability domain Events, Task execution reference, ceiling consumption, and
audit linkage. Rejection records no domain Event or consumption. Pre-boundary
rejection remains non-authoritative.

The canonical accepted lineage preserves the existing kernel shape:

```text
CommandAccepted(delegated operation, Task, Grant, ceiling prior=0)
  -> capability domain Event or Events
  -> AuditLinked(enrollment, Assignment, Grant evidence, Task,
                 exact capability, ceiling resulting=1, outcome references)
```

The selected protocol schemas MUST make all listed Task, authority, and ceiling
facts immutable and replayable through the common acceptance and audit
representation. They MUST NOT copy authentication-provider material or generic
governance fields into the capability domain payload. Attributable rejection
uses the existing `CommandRejected -> AuditLinked` lineage, retains the proven
enrollment, Assignment, Grant, Task, requested capability, gate, and admission
evidence applicable to the denial, emits no capability domain Event, and does
not consume the ceiling.

## 8. Outcomes, replay, and historical validity

Delegated domain execution and Task completion are separate accepted Commands.
A successful invocation does not establish Task acceptance criteria.
Completion requires pinned execution references and outcome evidence; failure
records attempted work and effects; cancellation records its governance basis
and known effects. Each terminal transition atomically records its Task outcome
Event and `WorkerCompleted`.

Replay folds complete canonical Organization history and reconstructs Actor and
enrollment, Sponsor, Assignment and Role, source Grant evidence and later
state, Task lifecycle and consumption, accepted/rejected delegated Commands,
admission evidence, capability Events, terminal outcome, and audit lineage.

Replay validates every envelope, version, Organization position, recording
Command, transaction sequence, causal reference, revision, authority reference,
and audit link before projection advancement. Unknown, malformed, unsupported,
incomplete, duplicate, or inconsistent history fails without a partial
projection. Replay never authenticates, reauthorizes, calls current governance,
reads a Clock, allocates, handles, dispatches, or writes. Later Worker,
Assignment, Grant, Role, Task, or Policy changes govern new Commands only and
do not invalidate historical acceptance.

## 9. Validation and closure obligations

Later conformance and implementation MUST independently prove:

- Actor authentication, exact enrollment attribution, same-Organization scope,
  Sponsor, purpose, classification, and durable identity;
- active Worker, Role, Assignment, and source Grant where required;
- Role Assignment and enrollment alone confer no authority;
- attenuation across capability, Organization, recipient, purpose, Resources,
  risk, approval, duration, and delegation;
- issue, governed acceptance, assignment, worker acceptance, completion,
  failure, cancellation, and every invalid transition;
- wrong Worker/Organization, inactive Assignment, terminal Task, unlisted
  capability, missing Grant, and expanded scope fail closed;
- one accepted execution consumes the ceiling atomically and a second invokes
  no handler and appends no domain Event;
- ordinary governance, Organization concurrency, idempotent redelivery, atomic
  accepted recording, deterministic replay, and immutable historical validity;
  and
- no ambient time, scheduler, queue, lease, heartbeat, automatic retry,
  redelegation, wildcard, or general budget dependency.

The positive closure scenario is bootstrap; CreateRole; ActivateRole; recognize
and enroll a Temporary Worker Actor; assign it to the Role; pin an eligible
source Grant; issue, accept, assign, and worker-accept one Task permitting one
existing capability; execute once through ordinary admission; complete the
Task with execution references; and replay the chain from an empty projection.

The negative companion uses the same chain to request an exact capability
absent from the Task allowlist. It is denied without capability handling,
ceiling consumption, domain Event, or partial append.

This architecture does not allocate conformance identifiers. The later
protocol/conformance slice does so after executable record shapes are approved,
with direct scenario-to-test evidence and unique reason codes.

## 10. Scope and dependency-ordered PR stack

Architecture and executable-contract foundation:

1. governed Task delegation reconciliation and ADR;
2. Temporary Worker enrollment and lifecycle contract;
3. Role Assignment lifecycle contract;
4. constrained Task lifecycle and attenuation contract;
5. source-Grant snapshot and delegated-execution admission contract;
6. protocol records, reason codes, and conformance scenarios.

Implementation, only after architecture approval:

7. Temporary Worker enrollment and disablement;
8. Role Assignment creation and termination;
9. Task issuance, acceptance, assignment, worker acceptance, and terminal
   outcomes;
10. delegated capability execution, replay, negative allowlist proof, and
    Milestone 3 closure.

General Grant administration, multiple Tasks per enrollment, multiple Workers
per Task, retries, planning, decomposition, scheduling, queues, leases,
heartbeats, ambient expiry, general budgeting, resource markets, hierarchy,
redelegation, dynamic capabilities, artifact repositories, and AI-specific
kernel semantics are deferred.
