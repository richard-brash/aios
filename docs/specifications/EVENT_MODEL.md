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
- `issued_at`, `organization_id`, and exactly one `initiating_actor_id`;
- `correlation_id` and the trigger or subject reference that motivated the Command;
- target entity and Resource references;
- for a Command that proposes or performs a Task or Action, exactly one Work Root (`goal_id` XOR `duty_reference`), or a target Task that already has one; administrative Commands identify their governed subject and duty where applicable, and constitutional bootstrap uses the bounded founding Decision described below;
- asserted Authority Grant and Approval references where applicable;
- requested operation, inputs, constraints, and idempotency key; and
- supporting evidence references and declared confidence when the request depends on uncertain claims.

Commands MAY additionally identify `participating_actor_ids`, `approver_actor_ids`, `reviewer_actor_ids`, a `governing_body_id`, and individually attributable votes or dispositions. These do not replace the single technical initiator and do not make that initiator the deciding authority.

The kernel MUST authenticate attribution, load current Policy and authority, validate schemas and preconditions, check lifecycle, approval, resource, risk, and idempotency constraints, and then accept or reject the Command. Rejection is itself recorded as an Event. An accepted Command MUST produce at least one Event. Every Event MUST reference exactly one `recording_command_id`: the Command through which AIOS admitted or generated the Event. A trusted kernel-generated Command is required for timers, expiry, replay-independent scheduling, policy enforcement, and external observations; it MUST identify the trusted Service Actor and triggering source. The recording Command explains why AIOS recorded a fact; it MUST NOT be represented as the cause of an external fact merely because it admitted the observation.

Organization bootstrap is one constitutional transaction and Command boundary. It atomically records the Organization, initiating verified Human Actor, constitutional owner or governor Role, Role Assignment, founding Decision, initial Authority Grant or Grants, founding Events, and Audit Record references. No operational Command is admissible before bootstrap completes. Bootstrap authority covers only this Human-reserved establishment act; ordinary admission rules apply immediately afterward.

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
| `initiating_actor_id` | Exactly one Actor who technically initiated the recording Command. Trusted automation uses a persistent Service Actor. The initiator is not automatically the decider, approver, observer, or cause. |
| `recording_command_id` | Exactly one Command through which AIOS admitted or generated this Event. This is recording provenance, not necessarily real-world causation. |
| `correlation_id` | Stable identifier grouping one end-to-end operation or case. |
| `causal_reference` | Typed reference to a prior AIOS Event, external occurrence, Tool result, timer or deadline, webhook or message, human observation, imported record, or `null` for an independently initiated internal Command. It states the known trigger or cause of the underlying occurrence and MUST distinguish causal evidence from mere sequence. |
| `resource_references` | Complete typed identifiers of Resources read, reserved, consumed, created, changed, disclosed, or released; an empty collection is explicit. |
| `result` | Typed outcome, including success, rejection, failure, partial result, or observation. It MUST distinguish attempted from completed effects. |
| `supporting_evidence` | Pinned identifiers and versions of supporting and material contradictory evidence; an empty collection is explicit. |
| `epistemic_status` | One baseline value from the epistemic contract below. |
| `payload` | Type-specific facts sufficient to apply the AIOS transition without consulting mutable external state. External content may remain behind governed stable references. |

Events MAY also record participating, approving, and reviewing Actor identifiers; a Governing Body; and individually attributable votes or dispositions. Consequential Events MUST additionally reference the Work Root, Task when applicable, Authority Grant, relevant Policy versions, Decision, required Approvals, affected entities, Tool invocations, cost, reversibility status, and result evidence. Protected values MAY be represented by integrity-preserving restricted references.

### Epistemic status

`epistemic_status` describes the basis on which an Event's assertion is recorded:

- `deterministic`: a kernel-derived administrative or state-transition fact that follows completely from admitted inputs and deterministic rules;
- `observed`: a direct measurement or observation, with source and acquisition method recorded, that may still contain measurement uncertainty;
- `asserted`: a proposition reported by a Human, external party, message, imported record, or system without AIOS independently establishing it;
- `inferred`: a conclusion derived from evidence by a stated transformation or reasoning process;
- `predicted`: a statement about a future or counterfactual condition;
- `disputed`: an assertion for which material contradictory evidence or an attributable challenge remains unresolved.

`confidence` MUST be omitted or explicitly `not_applicable` for deterministic state-transition facts. It is REQUIRED for inferred and predicted assertions, uncertain observed assertions, and disputed assertions. It MAY be recorded for asserted facts when it represents a sourced assessment rather than invented certainty. Where applicable, confidence MUST be explained using the Organization-approved scale and tied to evidence quality, independence, recency, and contradiction. Confidence never creates authority, validity, or truth.

### State Transitions

A State Transition is the deterministic application of an Event to a prior valid projection. Only a defined Event may change durable state. Each transition contract MUST state:

- eligible prior state or states;
- required event type and fields;
- authority, Policy, Approval, and invariant preconditions;
- next state and projection changes; and
- rejection behavior if a precondition is false.

The same ordered Event sequence and specification version MUST yield the same state. Models, wall-clock reads, network reads, random choices, or mutable external data MUST NOT participate in transition evaluation. Their results must first be captured as Events. Invalid transitions fail closed and generate a rejection or Incident Event without changing the target state.

## 2. Event sourcing contract

Event sourcing governs authoritative AIOS governance, identity, authority, lifecycle, decision, resource-accounting, memory, and audit state. Current AIOS entity views, governance queues, governed balances, lifecycle states, memory indexes, and audit views are projections derived from the accepted Event stream. A projection is disposable and MUST NOT become an independent source of AIOS governance truth.

External or specialized systems MAY retain their own state, including artifact content stores, credential stores, search indexes, transient caches, model context, vendor platforms, banking systems, and external communication systems. AIOS does not duplicate every byte or claim to reconstruct those systems. It MUST record stable references, observed or reconciled versions, integrity identifiers, ownership, authority, classification, provenance, relevant external state observations, reconciliation status, and Decision and audit linkage sufficient to govern their use.

### Immutable event logs

Once accepted, an Event MUST NOT be updated, reordered, overwritten, or silently removed. Corrections, reversals, supersession, redaction, and lawful deletion are expressed by later Events. Protected content may be removed when lawfully required, but the minimum lawful tombstone, integrity relationship, and deletion Event remain. The log MUST make unauthorized mutation detectable and preserve organization ordering.

The kernel MUST assign a monotonically ordered stream position within each Organization. Timestamp alone MUST NOT determine order. Duplicate delivery is expected; `event_id`, Command idempotency, and transition guards MUST prevent duplicate effects.

### Replay

Replay reconstructs a projection by applying Events in stream order from inception or from a verified checkpoint. Replay MUST:

1. use the event schema and deterministic transition rules applicable to each Event;
2. verify identity, ordering, integrity, and schema compatibility;
3. perform no external effects, Tool calls, notifications, Commands, or new Events;
4. reproduce the same authoritative AIOS projections and governed external references for the same stream and specification versions, without pretending to reconstruct inaccessible external domain state; and
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
| Work roots and goals | Goal, duty, Objective, Project, and Task coordination | `GoalActivated`, `TaskAssigned`, `GoalCompleted` |
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

- `EmployeeCreated`: a deterministic Event that establishes a persistent Employee identity in exactly one Organization; it does not activate employment or grant authority, and its confidence is not applicable.
- `TaskAssigned`: changes an eligible Task to `assigned` and identifies one eligible assignee; it does not expand task scope or authority.
- `GoalCompleted`: a deterministic transition Event recording that current success criteria were evaluated against pinned evidence and satisfied through an authorized completion Decision; confidence belongs to uncertain evidence Events, not this transition fact.
- `AuthorityGranted`: activates a valid Grant after all required approvals; its payload contains the complete effective scope and constraints.
- `ApprovalRequested`: creates an Approval in `requested` state for exactly one Decision and eligible approval route.
- `ApprovalGranted`: records an eligible approver's informed, specific, unexpired grant for the referenced Decision version and conditions.
- `ApprovalDenied`: records denial and rationale; it confers no authority and closes or returns the Decision according to Policy.
- `BudgetExceeded`: records detected actual use above a limit. It MUST suspend further affected consumption, open or link an Incident when material, and MUST NOT retroactively authorize the excess.
- `IncidentOpened`: creates an Incident and identifies reporter, detection, category, initial severity, affected references, and containment owner.
- `WorkerSpawned`: establishes and activates a Temporary Worker only after validating one Sponsor, express delegation, purpose, Tasks, budget, least-privilege Grant, and expiry.
- `WorkerExpired`: ends a worker at the first applicable expiry or completion condition and prevents new activity; prior accountability remains.
- `MemoryRecorded`: admits a Memory Record with provenance, validity, classification, retention, evidence, epistemic status, and confidence when the epistemic contract requires it.
- `MemorySuperseded`: links a new current Record to an earlier Record, states reason and affected uses, and preserves the earlier Record as discoverable unless lawful deletion separately applies.

## 5. Concurrency and failure semantics

Commands that depend on current state MUST declare the expected entity version or equivalent precondition. If another Event changes that state first, the kernel MUST reject or require reevaluation; it MUST NOT silently apply stale authority, evidence, approval, budget, or Policy.

An external side effect and its recording cannot be assumed atomic. The Event stream MUST distinguish intent, attempt, observed external result, verification, and compensation. Uncertain outcomes remain uncertain, trigger reconciliation, and MUST NOT be reported as success. Retry requires idempotency evidence or an authorized Decision that accepts duplicate-effect risk.
