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

The kernel MUST authenticate attribution, load current Policy and authority, validate schemas and preconditions, check lifecycle, approval, resource, risk, and idempotency constraints, and then accept or reject the Command. Rejection after an authenticated Organization recording boundary is established is recorded as an Event when the relevant append can commit; pre-boundary rejection is typed but non-authoritative and MUST NOT enter an Organization stream. An accepted Command MUST produce at least one Event. Every Event MUST reference exactly one `recording_command_id`: the Command through which AIOS admitted or generated the Event. A trusted kernel-generated Command is required for timers, expiry, replay-independent scheduling, policy enforcement, and external observations; it MUST identify the trusted Service Actor and triggering source. The recording Command explains why AIOS recorded a fact; it MUST NOT be represented as the cause of an external fact merely because it admitted the observation.

Organization bootstrap is the one-time constitutional genesis admission boundary. Because ordinary organizational Authority Grants cannot authorize their own initial creation, the reserved genesis Command is admitted directly under the Constitution, not under a preexisting organizational Grant. It MUST be initiated by a verified Human and MUST use reserved genesis Command and Event types, or an equivalently explicit reserved classification that cannot be confused with ordinary operations. One atomic append establishes the Organization, Human Actor, constitutional owner or governor Role, Role Assignment, founding constitutional Decision, initial Authority Grant or Grants, recording Command, founding Events, and Audit Record references. No partial state is observable and the transaction MUST NOT perform ordinary operational work. Exact retries are idempotent; competing or materially different attempts are rejected or deterministically resolved. No operational Command is admissible before completion, and ordinary admission rules apply immediately afterward.

### Events

An Event is an immutable, timestamped assertion that the kernel accepted, rejected, attempted, observed, decided, or changed something. An Event records what is known to have occurred, not an instruction to make it occur. Event names use past tense.

Every Event MUST conform to the common envelope and its versioned Event-type schema. The common envelope preserves identity, ordering, organization, recording provenance, correlation, causal accounting, type, payload interpretation, and integrity. The Event-type schema MUST classify semantic fields as required, optional, prohibited, or explicitly not applicable; it MUST NOT require empty or invented ceremonial values.

| Field | Contract |
|---|---|
| `event_id` | Globally unique, stable, and never reused. |
| `event_type` | Versioned past-tense semantic type. |
| `schema_version` | Version of the event contract used to interpret the payload. |
| `timestamp` | Kernel-recorded time of acceptance; observation time belongs in the payload when different. |
| `organization_id` | Exactly one organization whose stream owns the Event. |
| `stream_position` | Kernel-assigned monotonic position in that Organization's Event stream; it is ordering, not an entity or schema version. |
| `initiating_actor_id` | Exactly one Actor who technically initiated the recording Command. Trusted automation uses a persistent Service Actor. The initiator is not automatically the decider, approver, observer, or cause. |
| `recording_command_id` | Exactly one Command through which AIOS admitted or generated this Event. This is recording provenance, not necessarily real-world causation. |
| `correlation_id` | Stable identifier grouping one end-to-end operation or case. |
| `causal_reference` | Typed reference to a prior AIOS Event, external occurrence, Tool result, timer or deadline, webhook or message, human observation, imported record, or `null` for an independently initiated internal Command. It states the known trigger or cause of the underlying occurrence and MUST distinguish causal evidence from mere sequence. |
| `resource_references` | REQUIRED when Resources are materially read, reserved, consumed, created, changed, disclosed, or released; otherwise optional or explicitly not applicable as the type schema declares. A mechanical Event MUST NOT invent a Resource reference. |
| `result` | REQUIRED for dispositions, Actions, attempts, observations, and outcome Events; optional or not applicable for a mechanical transition whose complete meaning is the transition itself. Where present, it MUST distinguish attempted from completed effects. |
| `supporting_evidence` | REQUIRED for claims, observations, assessments, recommendations, Decisions, Actions, outcomes, and evidence-dependent transitions; optional or not applicable for a purely mechanical transition. Material contradictions are pinned whenever evidence is required. |
| `epistemic_status` | REQUIRED whenever the Event asserts, observes, infers, predicts, disputes, recommends, decides, acts upon, or reports an outcome about the world. A type schema MAY mark it `not_applicable` for a purely mechanical lifecycle or bookkeeping fact whose truth is wholly the deterministic application of already admitted inputs. It MUST NOT use a fabricated status to simulate evidence. |
| `payload` | Type-specific facts sufficient to apply the AIOS transition without consulting mutable external state. External content may remain behind governed stable references. |
| `integrity_reference` | Integrity identifier covering the immutable envelope and payload, or the explicitly governed redacted form. |

Events MAY also record participating, proposing, recommending, deciding, approving, reviewing, and technically recording Actor identifiers; a Governing Body; and individually attributable votes, recusals, or dispositions. Consequential Events MUST distinguish the accountable decider from the approver and technical initiator. They MUST additionally reference the Work Root, Task when applicable, Authority Grant, relevant Policy versions, Decision, required Approvals, affected entities, Tool invocations, cost, reversibility status, and result evidence. Protected values MAY be represented by integrity-preserving restricted references.

For Milestone 3 governed Task delegation, accepted lifecycle and capability-execution history MUST additionally preserve the Temporary Worker Actor/enrollment reference, qualifying Role Assignment, pinned source Authority Grant evidence, exact Task capability scope, deterministic Resource ceiling and consumption, and Task execution/outcome lineage. These facts remain in the applicable envelope, audit, relationship, Resource, or domain Event contract rather than being redundantly copied into every payload. One atomic accepted delegated execution records the common accepted disposition, capability domain Event or Events, Task execution reference, ceiling consumption, and audit linkage. Task completion, failure, or cancellation is a separate accepted execution and atomically records the terminal Task Event with `WorkerCompleted` for the one-Task profile.

### Epistemic status

`epistemic_status` describes the basis on which an Event's assertion is recorded:

- `deterministic`: a kernel-derived administrative or state-transition fact that follows completely from admitted inputs and deterministic rules;
- `observed`: a direct measurement or observation, with source and acquisition method recorded, that may still contain measurement uncertainty;
- `asserted`: a proposition reported by a Human, external party, message, imported record, or system without AIOS independently establishing it;
- `inferred`: a conclusion derived from evidence by a stated transformation or reasoning process;
- `predicted`: a statement about a future or counterfactual condition;
- `disputed`: an assertion for which material contradictory evidence or an attributable challenge remains unresolved.

`confidence` MUST be omitted or explicitly `not_applicable` for deterministic state-transition facts and Events whose epistemic status is not applicable. It is REQUIRED for inferred and predicted assertions, uncertain observed assertions, and disputed assertions. It MAY be recorded for asserted facts when it represents a sourced assessment rather than invented certainty. Where applicable, confidence MUST be explained using the Organization-approved scale and tied to evidence quality, independence, recency, and contradiction. Confidence never creates authority, validity, or truth. An empty evidence collection, artificial confidence value, generic result, or other placeholder MUST NOT be used to create an appearance of conformance.

### State Transitions

A State Transition is the deterministic application of an Event to a prior valid projection. Only a defined Event may change durable state. Each transition contract MUST state:

- eligible prior state or states;
- required event type and fields;
- authority, Policy, Approval, and invariant preconditions;
- next state and projection changes; and
- rejection behavior if a precondition is false.

The same ordered Event sequence and applicable schema and transition-specification versions MUST yield the same state. This determinism applies to governance validation, admission, transition evaluation, and replay—not to Employee planning, model inference, recommendations, Tool behavior, or external execution, which may be nondeterministic. Their material results must first be captured through governed Commands and Events before affecting authoritative state. Invalid transitions fail closed and generate a rejection or Incident Event without changing the target state.

## 2. Event sourcing contract

Event sourcing governs authoritative AIOS governance, identity, authority, lifecycle, decision, resource-accounting, memory, and audit state. Current AIOS entity views, governance queues, governed balances, lifecycle states, memory indexes, and audit views are projections derived from the accepted Event stream. A projection is disposable and MUST NOT become an independent source of AIOS governance truth.

External or specialized systems MAY retain their own state, including artifact content stores, credential stores, search indexes, transient caches, model context, vendor platforms, banking systems, and external communication systems. AIOS does not duplicate every byte or claim to reconstruct those systems. It MUST record stable references, observed or reconciled versions, integrity identifiers, ownership, authority, classification, provenance, relevant external state observations, reconciliation status, and Decision and audit linkage sufficient to govern their use.

### Immutable event logs

Once accepted, an Event MUST NOT be updated, reordered, overwritten, or silently removed. Events SHOULD contain the minimum sensitive content necessary for integrity, accountability, and interpretation; sensitive, erasable, sealed, or access-controlled content SHOULD normally be stored in governed Records or Resources behind stable identifiers and integrity references. Corrections, reversals, supersession, redaction, restriction, and lawful deletion are expressed by later Events. Policy or law MAY require content redaction or cryptographic erasure, but the minimum lawful nonreconstructive tombstone, integrity relationship, governed availability state, and deletion or restriction Event remain. Replay reconstructs that availability state deterministically. Historical reference never authorizes disclosure or recovery of content that is deleted, sealed, redacted, or inaccessible under current Policy. The log MUST make unauthorized mutation detectable and preserve organization ordering.

The kernel MUST assign a monotonically ordered stream position within each Organization. The Organization is the tenancy, isolation, governance, and Event-ordering boundary; AIOS defines no separate Tenant entity. All authoritative post-genesis Events for Organization-contained entities, including Role lifecycle Events, MUST be appended to one authoritative Organization stream. Timestamp alone MUST NOT determine order. Duplicate delivery is expected; `event_id`, Command idempotency, and transition guards MUST prevent duplicate effects.

An Event affecting a contained entity MUST identify that entity and the applicable named `entity_revision` so its state can be projected independently from the Organization history. Per-entity projections, indexes, and filtered Event views MAY exist, but they are derived and non-authoritative. A per-Role Event stream MUST NOT be treated as an independent source of authoritative history or write concurrency. A future implementation MAY physically partition storage only if it preserves one authoritative Organization ordering, atomic append semantics, and deterministic replay. Reserved pre-Organization genesis recording remains the distinct bootstrap exception defined by the bootstrap contract.

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
- `RoleActivated`: a deterministic ordinary post-genesis transition Event that changes exactly one existing Role from `draft` at revision `n` to `active` at revision `n + 1`. Its versioned payload contains `role_id`, `prior_lifecycle_state=draft`, `lifecycle_state=active`, `prior_entity_revision=n`, and `entity_revision=n + 1`. It creates no Role Assignment or Authority Grant and is appended only to the authoritative Organization stream.
- `TaskAssigned`: changes an eligible Task to `assigned` and identifies one eligible assignee; it does not expand task scope or authority.
- `GoalCompleted`: a deterministic transition Event recording that current success criteria were evaluated against pinned evidence and satisfied through an authorized completion Decision; confidence belongs to uncertain evidence Events, not this transition fact.
- `AuthorityGranted`: activates a valid Grant after all required approvals; its payload contains the complete effective scope and constraints.
- `ApprovalRequested`: creates an Approval in `requested` state for exactly one Decision and eligible approval route.
- `ApprovalGranted`: records an eligible approver's informed, specific, unexpired grant for the referenced `decision_content_version` and conditions.
- `ApprovalDenied`: records denial and rationale; it confers no authority and closes or returns the Decision according to Policy.
- `BudgetExceeded`: records detected actual use above a limit. It MUST suspend further affected consumption, open or link an Incident when material, and MUST NOT retroactively authorize the excess.
- `IncidentOpened`: creates an Incident and identifies reporter, detection, category, initial severity, affected references, and containment owner.
- `WorkerSpawned`: establishes and activates a Temporary Worker only after validating one Sponsor, express delegation, purpose, Tasks, budget, least-privilege Grant, and expiry.
- `WorkerExpired`: ends a worker at the first applicable expiry or completion condition and prevents new activity; prior accountability remains.
- `MemoryRecorded`: admits a Memory Record with provenance, validity, classification, retention, evidence, epistemic status, and confidence when the epistemic contract requires it.
- `MemorySuperseded`: links a new current Record to an earlier Record, states reason and affected uses, and preserves the earlier Record as discoverable unless lawful deletion separately applies.

## 5. Concurrency and failure semantics

Commands that depend on current state MUST declare the expected Organization `stream_position` and any applicable `entity_revision`, named business-content version, or other exact subject precondition. These dimensions MUST NOT be conflated. For an entity-scoped mutation, the Organization stream position is the authoritative append precondition; entity state or revision is an additional domain precondition evaluated against the same Organization history used for the append decision. No independent entity-stream version can authorize a write that conflicts with the Organization stream. If another Event changes that state first, the kernel MUST reject or require reevaluation; it MUST NOT silently apply stale authority, evidence, approval, budget, or Policy.

An external side effect and its recording cannot be assumed atomic. The Event stream MUST distinguish intent, attempt, observed external result, verification, and compensation. Uncertain outcomes remain uncertain, trigger reconciliation, and MUST NOT be reported as success. Retry requires idempotency evidence or an authorized Decision that accepts duplicate-effect risk.
