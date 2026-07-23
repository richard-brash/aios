# AIOS Event Model

**Specification version:** 0.0.2
**Status:** Normative kernel contract

## 1. Architecture

AIOS coordinates work through **Commands**, records facts as immutable **Events**, and computes entity **State Transitions** by applying accepted Events in order. Conversations, model outputs, API calls, timers, and tool results are inputs to this architecture; none is authoritative until admitted through the governed command and event path.

### Commands

A Command is an attributable request that the kernel evaluate and, if permitted, attempt an operation. It is an expression of intent, not proof that anything happened.

Every Command MUST contain:

- `command_id`: globally unique and never reused;
- `command_type` and schema version;
- `issued_at`, `organization_id`, and `actor_id`;
- `correlation_id` and nullable `causation_id`;
- target entity and Resource references;
- Goal, Task, or explicit governance/safety/maintenance duty reference;
- asserted Authority Grant and Approval references where applicable;
- requested operation, inputs, constraints, and idempotency key; and
- supporting evidence references and declared confidence when the request depends on uncertain claims.

The kernel MUST authenticate attribution, load current Policy and authority, validate schemas and preconditions, check lifecycle, approval, resource, risk, and idempotency constraints, and then accept or reject the Command. Rejection is itself recorded as an Event. An accepted Command MUST produce at least one Event. Every Event MUST reference exactly one originating Command. A trusted kernel-generated Command is required for timers, expiry, replay-independent scheduling, policy enforcement, and external observations; it MUST identify the trusted Service Actor and triggering source.

### Events

An Event is an immutable, timestamped assertion that the kernel accepted, rejected, attempted, observed, decided, or changed something. An Event records what is known to have occurred, not an instruction to make it occur. Event names use past tense.

Every Event MUST contain:

| Field | Contract |
|---|---|
| `event_id` | Globally unique, stable, and never reused. |
| `event_type` | Versioned past-tense semantic type. |
| `schema_version` | Version of the event contract used to interpret the payload. |
| `timestamp` | Kernel-recorded time of acceptance; observation time belongs in the payload when different. |
| `organization_id` | Exactly one organization whose stream owns the Event. |
| `actor_id` | Actor to whom the originating Command and resulting activity are attributable. Trusted automation uses a persistent Service Actor. |
| `originating_command_id` | Exactly one Command that caused this Event to be evaluated and recorded. |
| `correlation_id` | Stable identifier grouping one end-to-end operation or case. |
| `causation_id` | Identifier of the immediately preceding causal Event, or `null` only for the first Event caused by an independently initiated Command. It MUST NOT point to a Command. |
| `resource_references` | Complete typed identifiers of Resources read, reserved, consumed, created, changed, disclosed, or released; an empty collection is explicit. |
| `result` | Typed outcome, including success, rejection, failure, partial result, or observation. It MUST distinguish attempted from completed effects. |
| `supporting_evidence` | Pinned identifiers and versions of supporting and material contradictory evidence; an empty collection is explicit. |
| `confidence` | Explained confidence for uncertain assertions, using the organization-approved scale. Deterministic administrative facts use the designated maximum confidence with basis `kernel_observed`; confidence never creates authority. |
| `payload` | Type-specific facts sufficient to apply the Event without consulting mutable external state. |

Consequential Events MUST additionally reference the Goal or duty, Task when applicable, Authority Grant, relevant Policy versions, Decision, required Approvals, affected entities, Tool invocations, cost, reversibility status, and result evidence. Protected values MAY be represented by integrity-preserving restricted references.

### State Transitions

A State Transition is the deterministic application of an Event to a prior valid projection. Only a defined Event may change durable state. Each transition contract MUST state:

- eligible prior state or states;
- required event type and fields;
- authority, Policy, Approval, and invariant preconditions;
- next state and projection changes; and
- rejection behavior if a precondition is false.

The same ordered Event sequence and specification version MUST yield the same state. Models, wall-clock reads, network reads, random choices, or mutable external data MUST NOT participate in transition evaluation. Their results must first be captured as Events. Invalid transitions fail closed and generate a rejection or Incident Event without changing the target state.

## 2. Event sourcing contract

Event sourcing means the accepted Event stream is the authoritative history of organizational state. Current entity views, queues, balances, lifecycle states, memory indexes, and audit views are projections derived from that stream. A projection is disposable and MUST NOT become an independent source of truth.

### Immutable event logs

Once accepted, an Event MUST NOT be updated, reordered, overwritten, or silently removed. Corrections, reversals, supersession, redaction, and lawful deletion are expressed by later Events. Protected content may be removed when lawfully required, but the minimum lawful tombstone, integrity relationship, and deletion Event remain. The log MUST make unauthorized mutation detectable and preserve organization ordering.

The kernel MUST assign a monotonically ordered stream position within each Organization. Timestamp alone MUST NOT determine order. Duplicate delivery is expected; `event_id`, Command idempotency, and transition guards MUST prevent duplicate effects.

### Replay

Replay reconstructs a projection by applying Events in stream order from inception or from a verified checkpoint. Replay MUST:

1. use the event schema and deterministic transition rules applicable to each Event;
2. verify identity, ordering, integrity, and schema compatibility;
3. perform no external effects, Tool calls, notifications, Commands, or new Events;
4. reproduce the same derived state for the same stream and specification versions; and
5. report, rather than guess through, an unknown schema or violated invariant.

Snapshots or checkpoints MAY accelerate replay, but they are caches. They MUST reference the last incorporated stream position and integrity proof and MUST be discardable. Migration is represented by explicit, reviewable transformation rules or new Events; history remains interpretable under its original schema.

### Event subscriptions

A subscription is a declared interest in Events matching organization, type, subject, classification, or other authorized criteria. Subscribers receive Events asynchronously and MUST assume at-least-once delivery, delayed delivery, and redelivery. A subscriber MUST:

- authenticate as an Actor and pass organization, purpose, classification, and least-privilege checks;
- process idempotently and maintain an attributable checkpoint;
- preserve causal and organization ordering where its operation depends on them;
- treat an Event as a fact, not implicit authority to act;
- issue a new Command for any requested state change;
- record material delivery failure, dead-letter, lag, or access denial; and
- avoid leaking protected payloads through filters, errors, or metadata.

Subscriptions do not change the source Event, confer Authority Grants, or permit cross-organization access.

## 3. Event categories

Each Event has exactly one primary category and MAY have secondary classification tags.

| Category | Meaning | Representative event types |
|---|---|---|
| Identity and membership | Actor and Organization identity facts | `OrganizationCreated`, `EmployeeCreated`, `EmployeeSuspended` |
| Work and goals | Goal, Objective, Project, and Task coordination | `GoalActivated`, `TaskAssigned`, `GoalCompleted` |
| Authority and delegation | Issuance, narrowing, expiry, suspension, and revocation | `AuthorityGranted`, `AuthoritySuspended`, `WorkerSpawned`, `WorkerExpired` |
| Decision and approval | Consequential evaluation and disposition | `DecisionRecorded`, `ApprovalRequested`, `ApprovalGranted`, `ApprovalDenied` |
| Resource and budget | Reservation, consumption, variance, and release | `ResourceReserved`, `ResourceConsumed`, `BudgetExceeded` |
| Tool and action | Attempted and observed controlled effects | `ToolInvocationRequested`, `ActionAttempted`, `ActionCompleted`, `ActionFailed` |
| Memory and evidence | Admission, validation, conflict, correction, and deletion | `MemoryRecorded`, `MemorySuperseded`, `EvidencePinned`, `MemoryDeleted` |
| Artifact | Creation, review, publication, supersession, and withdrawal | `ArtifactCreated`, `ArtifactApproved`, `ArtifactSuperseded` |
| Policy and governance | Policy adoption and constitutional governance | `PolicyAdopted`, `PolicySuperseded`, `EmergencyRuleExpired` |
| Incident and safety | Detection, containment, review, and recovery | `IncidentOpened`, `ActivitySuspended`, `IncidentResolved` |
| Audit and system | Command disposition, subscription, replay, and integrity | `CommandRejected`, `SubscriptionLagged`, `IntegrityCheckFailed` |

## 4. Required example semantics

The following names have fixed minimum meanings. Implementations MAY add narrower event types but MUST NOT reuse these names incompatibly.

- `EmployeeCreated`: establishes a persistent Employee identity in exactly one Organization; it does not activate employment or grant authority.
- `TaskAssigned`: changes an eligible Task to `assigned` and identifies one eligible assignee; it does not expand task scope or authority.
- `GoalCompleted`: records that current success criteria were evaluated against pinned evidence and satisfied through an authorized completion Decision.
- `AuthorityGranted`: activates a valid Grant after all required approvals; its payload contains the complete effective scope and constraints.
- `ApprovalRequested`: creates an Approval in `requested` state for exactly one Decision and eligible approval route.
- `ApprovalGranted`: records an eligible approver's informed, specific, unexpired grant for the referenced Decision version and conditions.
- `ApprovalDenied`: records denial and rationale; it confers no authority and closes or returns the Decision according to Policy.
- `BudgetExceeded`: records detected actual use above a limit. It MUST suspend further affected consumption, open or link an Incident when material, and MUST NOT retroactively authorize the excess.
- `IncidentOpened`: creates an Incident and identifies reporter, detection, category, initial severity, affected references, and containment owner.
- `WorkerSpawned`: establishes and activates a Temporary Worker only after validating one Sponsor, express delegation, purpose, Tasks, budget, least-privilege Grant, and expiry.
- `WorkerExpired`: ends a worker at the first applicable expiry or completion condition and prevents new activity; prior accountability remains.
- `MemoryRecorded`: admits a Memory Record with provenance, validity, classification, retention, evidence, and confidence.
- `MemorySuperseded`: links a new current Record to an earlier Record, states reason and affected uses, and preserves the earlier Record as discoverable unless lawful deletion separately applies.

## 5. Concurrency and failure semantics

Commands that depend on current state MUST declare the expected entity version or equivalent precondition. If another Event changes that state first, the kernel MUST reject or require reevaluation; it MUST NOT silently apply stale authority, evidence, approval, budget, or Policy.

An external side effect and its recording cannot be assumed atomic. The Event stream MUST distinguish intent, attempt, observed external result, verification, and compensation. Uncertain outcomes remain uncertain, trigger reconciliation, and MUST NOT be reported as success. Retry requires idempotency evidence or an authorized Decision that accepts duplicate-effect risk.
