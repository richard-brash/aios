# ADR-0006: Governed Task delegation for the first Temporary Worker

## Status

Accepted for Milestone 3 architecture.

## Context

The initial Milestone 3 direction used a separate Work Item, treated Worker as
a second identity, derived permission without an Authority Grant, and deferred
every Resource ceiling and termination condition. Those choices conflicted
with the Constitution: Task is already the smallest independently governed
unit of work; Temporary Worker is an Actor kind; consequential action requires
an Authority Grant; and a Temporary Worker requires bounded Resources and an
expiry or completion condition.

Milestone 3 needs the smallest safe delegation envelope without implementing a
general Grant lifecycle, budgeting platform, scheduler, or AI-specific kernel.

## Decision

### Existing Task remains canonical

Milestone 3 uses the existing Task entity and lifecycle. `WorkItem` is not an
entity, protocol alias, aggregate, or independent source of state. The
first-worker profile follows the existing Task transitions from proposed,
through governed readiness and assignment, to worker acceptance (`in_progress`)
and one terminal outcome.

### Worker enrollment shares Actor identity

A Temporary Worker enrollment is the Organization-scoped institutional record
for an existing Actor whose immutable `actor_kind` is `temporary_worker`. It
shares that Actor's `actor_id`; it creates no `worker_id`, credential,
authentication principal, or second accountable identity. Authentication
continues to resolve the Actor through ordinary admission.

The Milestone 3 profile permits exactly one enrollment, one active Role
Assignment, one source Authority Grant, and one Task for that Actor. This is a
milestone constraint, not a universal restriction on the broader ontology.
The one Sponsor is also the Assignment assigner, source Grant issuer, and Task
issuer; those capacities remain separately evidenced and do not waive approval
separation.

### Authority remains Grant-based and Task-attenuated

Every consequential delegated execution cites one active source Authority
Grant whose recipient is the Temporary Worker Actor. The Grant is the source
of permission. Enrollment, Role Assignment, Task state, Task capability scope,
and ordinary governance are independently necessary constraints, but none is
authority by itself.

The accepted Task pins its source Grant and attenuation evidence. Its
Organization, Actor, purpose, capabilities, Resources, risk, approval
conditions, termination condition, and delegation prohibition must be equal to
or narrower than the source Grant. Missing, incomparable, or wider scope fails
closed. Grant revocation prevents a new capability execution but does not
rewrite a prior accepted execution.

The repository defines Authority Grant normatively but has no executable Grant
record or proof port. Milestone 3 therefore requires a narrow immutable
source-Grant snapshot and closed validation result before Task acceptance and
delegated execution. It reads and pins existing Grant evidence; it does not
create, revise, revoke, or generalize the Grant lifecycle.

### Minimal deterministic Resource ceiling

The first-worker Task permits exactly one accepted delegated capability
execution: `maximum_accepted_capability_executions = 1`. Consumption is the
count of accepted delegated executions for the Task in authoritative
Organization history. Its increment and the accepted execution commit in one
atomic append. A second execution fails closed before capability handling.

The ceiling is represented through the existing Budget/Resource vocabulary as
one immutable Task-scoped Budget dimension whose unit is
`accepted_delegated_capability_execution` and whose authorized limit is one.
This satisfies the existing `budget_ids` contract without requiring a general
budget administration or metering subsystem.

The source Grant ceiling identifies its authoritative Resource record. The
Task Budget has its own `budget_id` and retains an explicit reference to that
source Resource; it does not reuse the Resource identity as its Budget
identity. Attenuation requires the same canonical Resource dimension and unit,
that exact source-Resource lineage, and a Task limit no greater than the source
limit. The source Grant must also enumerate exact `capability_id` values in its
permitted actions. Otherwise deterministic attenuation is incomparable and
fails closed.

This is deterministic, replayable, attributable to the enrollment and source
Grant, and prevents unbounded accepted execution without monetary, token,
elapsed-time, or generalized Resource metering. Rejected attempts consume no
capacity because they produce no capability effect.

### Task terminality ends the enrollment

The enrollment completion condition is terminality of its one Task. Task
completion, failure, or cancellation immediately prevents new work and the
same accepted execution atomically records the terminal Task Event and
`WorkerCompleted`. No ambient-time read is required. Historical identity and
accepted execution remain resolvable.

Delegated domain execution and Task completion are separate accepted Commands.
A successful capability invocation does not prove Task acceptance criteria.

### Historical validity is immutable

Replay uses the admission, enrollment, assignment, Grant, Task, governance,
Resource-ceiling, accepted-execution, and outcome evidence recorded at the
time. It does not reauthorize history using current state. Later Worker
completion, assignment termination, Grant revocation, Role change, Task
terminality, or Policy change governs new Commands only.

## Rejected alternatives

- A separate Work Item duplicates Task and creates competing work authority.
- A Worker identifier separate from Actor duplicates attribution.
- Role Assignment, enrollment, Task acceptance, or capability availability as
  permission violates deny-by-default Grant semantics.
- A Task that is itself a Grant collapses work and permission.
- Wildcards, dynamic capability discovery, redelegation, multiple Tasks, and
  multiple Workers broaden the first slice unnecessarily.
- General monetary, token, time, scheduler, lease, or budget systems are not
  needed for one deterministic accepted-execution ceiling.
- Reauthorizing history under current Policy rewrites institutional truth.

## Consequences

- The accountability chain is Actor -> Temporary Worker enrollment -> Role
  Assignment -> source Authority Grant -> Task -> accepted delegated capability
  execution -> Events.
- All records belong to one Organization and use its single Event stream.
- Capability handlers remain pure; admission, governance, idempotency,
  allocation, audit, and append remain kernel responsibilities.
- The source-Grant proof contract precedes Task and execution slices.
- General Grant administration, budgets, retries, scheduling, planning,
  decomposition, and multiple Tasks per Worker remain deferred.
