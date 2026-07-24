# AIOS Kernel Contract

**Specification version:** 0.0.2
**Status:** Normative kernel boundary

## 1. Purpose and scope

This document defines the minimum behavior and responsibility boundary of every conforming AIOS kernel. The kernel is the deterministic governance-enforcement and orchestration boundary for an Organization; it is not a source of organizational authority. It admits Commands, evaluates current institutional constraints, records immutable Events, derives authoritative AIOS state, coordinates governed work, and fails closed when safe admission cannot be established.

The kernel is not an autonomous employee, model, planner, researcher, Tool, external-system adapter, or source of organizational purpose. It MUST NOT perform domain reasoning or substitute its own preferences for an Actor's attributable Decision. It makes only the deterministic governance decisions assigned to it by this contract and current Policy.

This contract refines, and MUST be read with:

- [`ARCHITECTURE_PRINCIPLES.md`](ARCHITECTURE_PRINCIPLES.md), which defines implementation-wide constraints;
- [`ENTITY_MODEL.md`](ENTITY_MODEL.md), which defines identities, Work Roots, authority, work, Resources, memory, and audit entities;
- [`EVENT_MODEL.md`](EVENT_MODEL.md), which defines Commands, Events, epistemic status, event sourcing, replay, and subscriptions;
- [`INVARIANTS.md`](INVARIANTS.md), which defines conditions no accepted transition may violate;
- [`LIFECYCLES.md`](LIFECYCLES.md), which defines legal entity transitions; and
- [`DECISION_RECORD.md`](DECISION_RECORD.md), which defines the consequential Decision audit format.

The Constitution and its Authority and Memory policies control if this contract conflicts with them. An implementation may provide additional internal mechanisms, but it MUST NOT weaken, bypass, or create an alternate interpretation of these normative boundaries.

## 2. Normative responsibility boundary

| Concern | Kernel-owned responsibility | Employee-owned responsibility | Adapter-owned responsibility | External-system-owned responsibility |
|---|---|---|---|---|
| Purpose and work | Validate exactly one Work Root and current scope; coordinate accepted work | Define plans, proposals, evidence needs, execution choices, and result assessment | None | May supply requests or observations but cannot define AIOS authority |
| Identity | Resolve persistent Actor, Role Assignment, Organization, and Service identities | Act through assigned institutional identity | Authenticate its configured Service identity and preserve caller attribution | Maintain its own identities; these do not become AIOS Actors implicitly |
| Authority and Policy | Evaluate current Authority Grants, hierarchy, constraints, Policy versions, and human-reserved powers | Request authority, refuse or escalate gaps, and operate within granted scope | Enforce narrower technical controls; never broaden authority | May enforce its own access rules; technical access is not organizational authority |
| Decisions and Approvals | Validate Decision completeness, accountable-decider eligibility, approval eligibility, mode, scope, usage, and current conditions | Frame and record proposals, alternatives, evidence, rationale, risks, costs, benefit, and outcome within delegated authority | Carry only approval and Decision references required by the invocation | May record external authorization, but it is not an AIOS Approval unless admitted |
| Events and lifecycle | Accept, order, append, and deterministically apply Events; enforce legal transitions | Issue attributable Commands and assess work outcomes | Return attributable observations and results through Commands | Retain domain state and expose observations or reconciliation evidence |
| Tool use | Authorize and record a Tool-action request; reserve Resources; reconcile reported outcomes | Select an eligible Tool and requested operation within authority | Translate an authorized request, attempt the external operation, and report result evidence | Execute or reject the domain operation and retain its own authoritative domain state |
| Resources | Reserve, aggregate, account, release, enforce thresholds, and stop affected work | Estimate expected use, choose proportionate use, report variance, and escalate | Meter and report actual use and uncertainty | Produce authoritative charges, balances, quotas, or consumption observations |
| Memory | Govern admission, provenance, classification, access, retrieval purpose, validity, and audit | Gather evidence, formulate Claims, request admission, interpret retrieved material | Fetch or store content under authorized scope without changing institutional status | Retain source content or indexes under their own controls |
| Scheduling | Admit and persist governed schedules; materialize due triggers as attributable Commands; enforce timeout, expiry, cancellation, and current-state revalidation | Propose timing, dependencies, priority, sequencing, recurrence, and scheduling strategy | Execute only an admitted dispatch | Supply clocks, calendars, or delivery facilities without creating authority |
| Replay and projections | Rebuild authoritative AIOS projections and governed references with no effects | None | MUST NOT be invoked by replay | MUST NOT be mutated, charged, notified, or treated as reconstructed by replay |

Specialized services MAY assist any column, but the allocation above remains authoritative. No service may become an alternate source of Authority Grants, Actor identity, Policy, institutional memory truth, Event order, Resource-accounting truth, or lifecycle state.

## 3. Kernel-owned responsibilities

The kernel MUST own and enforce:

1. Command schema, version, attribution, organization, and idempotency validation;
2. persistent identity, active Role Assignment, and organization-boundary resolution;
3. Authority Grant, delegation-chain, Policy-precedence, and human-reserved-power evaluation;
4. exclusive Work Root validation for every Task and Action;
5. Decision and Approval validation, including reusable-Approval usage accounting;
6. pre-execution Resource reservation, aggregation, threshold, and stop-condition enforcement;
7. lifecycle preconditions and deterministic transition selection;
8. organization-local Event ordering, acceptance, rejection, immutable append, and integrity linkage;
9. authoritative AIOS projection definition, checkpoint validation, rebuild, and comparison;
10. replay isolation and the prohibition of external effects during replay;
11. subscription authorization, filtering, delivery position, and auditability;
12. governed schedule admission and trigger enforcement, orchestration state, timeout, cancellation, retry eligibility, reconciliation, and escalation state, but not scheduling strategy;
13. Employee and Temporary Worker operational lifecycle supervision;
14. Tool-request authorization and separation from external execution;
15. Incident-linked emergency suspension and kill-switch enforcement;
16. constitutional Organization bootstrap atomicity;
17. consequential audit linkage and Decision-record completeness; and
18. memory admission and retrieval governance.

The kernel MAY delegate deterministic mechanical work to specialized services only when the service operates through a versioned contract, least-privilege identity, attributable Commands and Events, and kernel-controlled validation. Delegation does not transfer the kernel's normative responsibility.

## 4. Responsibilities excluded from the kernel

The kernel MUST NOT own:

- mission formation, Goal selection, planning, prioritization, or Task decomposition;
- scheduling strategy, priority selection, sequencing optimization, or sole workflow-engine responsibility;
- domain research, evidence gathering, interpretation, synthesis, forecasting, or creative work;
- selection among business or operational alternatives except deterministic validation of an attributable Decision against governing rules;
- private model reasoning, prompt construction, model-provider selection, or model output quality;
- the Employee's choice of an eligible Tool, tactic, or work product;
- factual determination that an external effect succeeded without admitted result evidence;
- execution of external Tool effects, external communications, transfers, purchases, publications, or other domain operations;
- authoritative content storage for every Artifact, Credential, vendor platform, bank, communication system, or other specialized domain;
- invention of missing evidence, Claims, Decisions, Approvals, authority, Resource availability, or external state; or
- legal, fiduciary, constitutional, or human-reserved judgment.

In this contract, **Employee** means the constitutional AI Employee and excludes Human Actors. Employees remain accountable institutional Actors for planning, evidence gathering, proposals, execution choices, and result assessment within their authority. Model instances are replaceable computational Resources used by Actors; they are never institutional Actors, Authority Grant holders, approving Humans, accountable deciders, or sources of Policy. Goal is the primary purpose-bearing concept for ordinary work; Project, Objective, and Plan are optional structures and are never mandatory Work Roots.

## 5. Command admission input contract

The admission boundary accepts one immutable Command envelope conforming to [`EVENT_MODEL.md`](EVENT_MODEL.md). The minimum input is:

| Input | Admission contract |
|---|---|
| Identity and version | Globally unique `command_id`, known `command_type`, supported schema version, `issued_at`, and idempotency key |
| Organization | Exactly one `organization_id` and an organization-scoped target |
| Attribution | Exactly one `initiating_actor_id`; participating, approving, reviewing, and Governing Body references where applicable |
| Correlation and trigger | `correlation_id` and the typed trigger or subject reference that motivated admission |
| Requested operation | Exact operation, target entities, inputs, declared constraints, and expected entity versions or other concurrency preconditions |
| Work Root | For every Task or Action, exactly one active `goal_id` or complete `duty_reference`, never both or neither |
| Authority | Asserted Authority Grant references and delegation chain where applicable; absence is explicit |
| Policy and Approval | Relevant Policy assertions and Approval references where applicable; absence is explicit |
| Resources | Affected Resource references, expected consumption by independently governed dimension, reservation request, and maximum exposure |
| Lifecycle | Target current state assertion and requested legal transition where applicable |
| Evidence | Pinned supporting and contradictory evidence references and epistemic metadata where the request depends on Claims |
| Consequence | Risk class, reversibility, Decision reference, result criteria, stop conditions, and Tool request when applicable |

The Command envelope is a claim about intent and context. References supplied by the caller MUST be resolved against current authoritative AIOS projections; their presence does not prove validity. The kernel MUST NOT fill a missing required field by inference from conversational context, prior success, credentials, Tool reachability, or model confidence.

At the admission boundary, the kernel MUST bind the Command to exactly one trusted `evaluation_time` and the current organization stream position. `evaluation_time` is kernel-supplied, not caller-controlled; it is included in the deterministic admission input and recorded in the resulting disposition Event. Expiry and effective-time evaluation use this bound value, not repeated wall-clock reads or untrusted `issued_at`. A retried idempotent Command returns the originally recorded evaluation rather than acquiring a new effective time.

## 6. Normative Command processing sequence

For each submitted Command, the kernel MUST perform the following logical sequence. Implementations MAY optimize mechanical evaluation only if the observable result is equivalent, no effect occurs before every required gate passes, and failure identifies the authoritative rejecting gate.

1. **Parse without effect.** Bound input size, decode the envelope, and reject malformed input without invoking a Tool, reserving a Resource, or changing governed state.
2. **Validate schema and version.** Require a known Command type, supported schema, required fields, field semantics, stable identifiers, and an allowed migration path. Unknown or ambiguous versions fail closed.
3. **Resolve organization boundary.** Confirm the Organization is eligible for the Command; every target, Actor, Policy, Grant, Approval, Resource, Task, Decision, and record belongs to it or has an explicit authorized cross-organization relationship.
4. **Authenticate attribution.** Resolve exactly one initiating Actor and any participants; verify identity state and invocation authenticity. Initiation does not imply deciding, approving, or causal authority.
5. **Resolve idempotency.** After authenticating access to the claimed Organization, compare the Command and idempotency key with recorded dispositions. For an exact duplicate, return the prior disposition without repeating validation-dependent mutations, reservations, Approval use, Events, scheduling, or external effects. Conflicting reuse rejects the Command and may open an Incident.
6. **Evaluate Role and Authority.** Confirm an active Role Assignment; evaluate each asserted Grant, Issuer, recipient, delegation chain, action and Resource scope, jurisdiction, risk, budget, time, delegation right, prohibition, and revocation state. Apply the narrowest safe constraint. Missing or ambiguous authority denies admission.
7. **Evaluate Policy.** Load pinned current versions in constitutional precedence order; evaluate legality, human-reserved powers, separation of duties, risk, privacy, records, retention, safety, and organization-specific constraints. A lower Policy may narrow but never expand a higher rule.
8. **Validate Work Root.** For every Task and Action, require exactly one `goal_id` or `duty_reference`. Confirm an active Goal or a complete, current duty identifying type, governing mandate, accountable issuer or owner, scope, and review or completion condition. Validate that the requested operation serves that root.
9. **Validate Decision and Approval.** Require the consequential Decision record when applicable. Validate its exact named `decision_content_version` and applicable `entity_revision`, the accountable decider's identity and eligibility, the separate eligibility of every required approver, collective dispositions and quorum when applicable, Approval mode, scope, assumptions, effective and expiry conditions, revocation triggers, review status, and separation from Authority. Every A4 disposition and every A3 disposition reserved by the Constitution or applicable Policy to Humans MUST name an eligible Human Actor as accountable decider or be the valid derived result of an eligible Human Governing Body process. An AI Employee MAY research, analyze, recommend, propose, route, prepare, initiate technical recording, or record the result, but MUST NOT be admitted as accountable decider for a Human-reserved matter. A separate Human Approval does not cure invalid accountable-decider attribution or convert an AI-authored Decision into a Human Decision. The technical initiator, proposer, recommender, recorder, accountable decider, and approver remain distinguishable even when one eligible Actor fills multiple roles. Operational Decisions validly delegated to an AI Employee remain permitted.
10. **Validate lifecycle and concurrency.** Confirm each target's current version and state, dependency states, legal transition, suspension and Incident conditions, and applicable approval requirements. Stale or conflicting state rejects the Command for reevaluation.
11. **Aggregate and prepare Resource reservations.** Aggregate related commitments across Action, Task, Work Root, Actor, vendor, and period; check all money and nonmoney dimensions; verify availability; and compute the reservation Events required before dispatch. No Resource state changes at this step. Unavailable or unverifiable capacity rejects or pauses admission.
12. **Determine transition and Approval use.** Compute, without mutation, the deterministic Event set and projection changes from admitted inputs. When execution is being authorized, include the applicable Approval-use transition: consume `single_use`, increment `bounded_repeat`, or record a `standing` use.
13. **Atomically append admission outcome.** In one indivisible organization-stream commit, verify the expected prior stream position, assign new positions, and append immutable acceptance and state-transition Events, Resource reservation Events, Approval-use facts, audit links, and any authorized dispatch intent. Either the complete set becomes authoritative or none of it does. Every Event identifies the recording Command; its causal-reference field remains semantically distinct from that Command and may be null only where [`EVENT_MODEL.md`](EVENT_MODEL.md) permits an independently initiated internal Command. A recorded Approval use is monotonic and MUST NOT be decremented or silently restored; uncertainty is reconciled, and any replacement permission requires a new valid Approval or other explicitly permitted disposition.
14. **Publish after append.** Only after successful append may the kernel expose accepted projection state, notify authorized subscribers, or dispatch an adapter request. Append failure produces no authorized external dispatch.

No earlier step may be treated as evidence that a later step passed. A Command rejected at any gate MUST produce an attributable rejection Event when a valid organization and recording boundary can be established. Input too malformed, hostile, or unattributable to admit as an AIOS Event MAY produce non-authoritative platform security telemetry under separate protective controls, but it MUST NOT enter an Organization stream, affect AIOS state, or be misattributed to an Organization or Actor.

## 7. Command admission output contract

Admission produces exactly one durable disposition class:

| Disposition | Required output |
|---|---|
| Accepted | `command_id`; disposition `accepted`; organization stream positions; accepted Event identifiers; derived target versions; reservations; claimed Approval use where applicable; authorized next orchestration step; audit reference |
| Rejected | For an attributable valid envelope: `command_id`; disposition `rejected`; stable reason code; failed gate; applicable Policy or invariant references; no target transition; no Tool dispatch; no Resource or Approval consumption except separately admitted security-processing cost; rejection Event and audit reference |
| Previously admitted | Original disposition and identifiers; proof of idempotency match; no repeated state change or effect |
| Paused or escalated | Recorded nonexecuting state; reason; unresolved references; accountable escalation route; review or timeout condition; no implied authority or success |

An accepted disposition authorizes only the recorded AIOS transition and, when stated, a request to an adapter. It does not assert that an external Tool action completed. External attempt, observation, verification, failure, uncertainty, and compensation are separately admitted facts.

## 8. Deterministic transition evaluation

For the same valid prior authoritative AIOS state, Command, Event schemas, Policy versions, and deterministic rules, the kernel MUST produce the same admission disposition, Events, and next projection state. Transition evaluation MUST NOT read an unrecorded wall clock, random value, model output, mutable network response, Tool result, external balance, or hidden configuration.

Time-based decisions use admitted timestamps, timer Commands, and recorded deadlines. Any external observation, model assessment, random selection, or Tool result that may influence state MUST first enter through an attributable Command and immutable Event with provenance and epistemic status. Unknown schema, missing Policy version, unverifiable integrity, or violated invariant stops evaluation; the kernel MUST NOT choose a plausible fallback.

Deterministic evaluation decides whether a proposed transition conforms. It does not decide whether an Employee's plan is wise, evidence is persuasive beyond explicit Policy rules, or a business result is desirable.

## 9. Event ordering, acceptance, rejection, and append

The kernel MUST maintain one unambiguous monotonic stream position within each Organization. Timestamp does not establish order. Cross-organization total ordering is not required and MUST NOT be used to infer cross-organization authority or causality.

An Event is accepted only when:

- its recording Command is sufficiently valid and attributable to establish an organization recording boundary; an acceptance Event records that all operation gates passed, while a rejection Event accurately identifies the gate that did not;
- it contains the complete common envelope required by [`EVENT_MODEL.md`](EVENT_MODEL.md) and conforms to its versioned Event-type schema;
- every semantic field satisfies the Event-type schema's applicability classification as required, optional, prohibited, or explicitly not applicable;
- Resource references, supporting evidence, result, epistemic status, and confidence are present when material to accountability or interpretation and are omitted, prohibited, or explicitly not applicable when the schema so declares; and no empty, invented, generic, or ceremonial value simulates conformance;
- consequential Event types retain every evidence, result, Resource, and epistemic field material to their Decision, Action, claim, observation, assessment, recommendation, or outcome;
- its transition is legal from the immediately preceding authoritative organization state; and
- appending it preserves all invariants.

Accepted Events are immutable. The kernel MUST NOT update, reorder, overwrite, silently omit, or physically reinterpret them. Correction, reversal, compensation, redaction, supersession, and deletion effects are later Events. Lawfully deleted content may leave a minimal nonreconstructive tombstone while Event identity, position, and accountability remain.

Command rejection MUST distinguish invalid intent from operational failure. Rejection changes no requested target state and confers no authority. A failed or uncertain external operation is not a rejected original Command; it is a subsequent observed outcome requiring its own recording Command, Events, reconciliation, and possibly an Incident.

## 10. Projection ownership and rebuilding

The kernel owns the normative definitions and versioned transition rules for authoritative AIOS governance, identity, authority, lifecycle, Decision, Resource-accounting, memory, and audit projections. Projection storage and computation MAY be delegated, but no projection service may accept direct authoritative edits or define alternate transition semantics.

Canonical relationship entities and accepted Events are authoritative relationship state. This includes Role Assignment for Actor-to-Role occupancy, Authority Grant for authority and delegation edges, and Governing Body membership records for membership. Inverse collections and navigation lists are derived projections or indexes unless an ontology definition explicitly declares otherwise. The kernel MAY use them for efficient reads but MUST validate against canonical relationship state; it MUST NOT accept or independently mutate a derived collection as competing authority. Replay MUST reconstruct inverse collections from canonical entities and Events. Conflict between canonical relationship state and a derived collection is an integrity failure requiring the affected operation to fail closed, not a discretionary reconciliation choice.

A projection MUST record the organization stream position and specification versions through which it was built. A checkpoint or snapshot is a discardable cache with an integrity reference, never an independent source of truth. On integrity mismatch, unknown Event schema, inconsistent version, or invariant violation, rebuilding MUST stop, report the exact position, and fail affected reads closed.

External systems retain their own domain state. Rebuild reconstructs AIOS references, last admitted observations, observed or reconciled versions, integrity identifiers, ownership, authority, classification, provenance, and reconciliation status. It MUST NOT fabricate unavailable Artifact content, Credential material, vendor state, bank state, message delivery, or other external facts.

## 11. Replay contract

Replay applies accepted Events in organization order to rebuild or verify authoritative AIOS projections. Replay MUST:

1. use the Event schema and deterministic transition rules applicable to each Event;
2. validate organization, ordering, integrity, and version compatibility;
3. reconstruct governed state and external references only from admitted facts;
4. produce the same projections for the same stream and specification versions; and
5. stop and report unknown or inconsistent history instead of guessing.

Replay MUST NOT:

- issue or synthesize Commands or Events;
- reserve, consume, release, or charge real Resources;
- consume or increment an Approval usage count beyond applying the historical Event that already recorded it;
- dispatch adapters or invoke Tools, models, subscriptions, webhooks, messages, timers, notifications, or human workflows;
- create Employees, workers, credentials, external accounts, or vendor objects;
- retry, compensate, reconcile, or repeat historical effects; or
- claim to have reconstructed inaccessible external-system state.

Replay MUST apply later redaction, deletion, sealing, access-restriction, tombstone, or cryptographic-erasure Events to the governed availability state of referenced content. It MUST NOT re-expose sensitive or erased content merely because an earlier Event referenced it.

Replay operates in an effect-prohibited mode whose breach is a critical conformance failure and Incident.

## 12. Subscription authorization and delivery

The kernel MUST authorize each subscription by subscriber Actor, Organization, active Role, Authority Grant, purpose, Event type, subject, classification, jurisdiction, and field-level disclosure scope. The ability to receive one Event MUST NOT imply access to causally related, correlated, referenced, or payload Events. Cross-organization delivery requires an explicit governed relationship and disclosure authority on both sides.

Delivery is asynchronous and at least once. Subscribers MUST tolerate redelivery, delay, independent availability, and explicit gaps. The kernel MUST provide stable Event identity, organization stream position, subscription position, schema version, and redaction state. A subscriber checkpoint is attributable but does not modify source history.

The kernel MUST preserve organization ordering where a subscription depends on it, prevent a later classified Event from leaking through filters or metadata, and record material denial, lag, delivery failure, dead-letter state, or checkpoint inconsistency. A delivered Event is a fact, not authority to act. Any subscriber-requested state change requires a new attributable Command and full admission.

## 13. Scheduling and orchestration

The kernel owns governed schedule admission and trigger enforcement, not scheduling strategy. Employees, planners, workflow services, and organizational processes MAY propose timing, dependencies, priority, sequencing, recurrence, and schedules. The kernel does not choose organizational priorities, optimize schedules, create plans, or become the sole workflow engine; it validates and persists admitted schedule state and may coordinate accepted Tasks, dependencies, timeouts, expiry, reviews, retries, subscriptions, adapters, Employees, and workers.

Every scheduled item MUST be created or changed by an admitted Command and Event and MUST retain:

- exactly one initiating Actor or persistent Service Actor;
- the governing Work Root or governed lifecycle subject;
- authorizing Grant, Policy, Decision, and Approval references where applicable;
- trigger, earliest and latest execution conditions, timeout, recurrence bound, and stop conditions;
- Resource reservation or maximum exposure;
- target Actor, Role, adapter, or subscription; and
- correlation, causal, and audit references.

When a trigger becomes due, the kernel or an authorized scheduling Service MUST submit or materialize a new attributable recording Command that cites the schedule and timer or deadline as its trigger. Before dispatch, the kernel MUST re-evaluate current Actor status, Role Assignment, Authority, Policy, Work Root, Approval, Resources, lifecycle, suspension, and stop conditions. A schedule never creates authority and MUST NOT preserve or bypass expired, revoked, stale, exhausted, cancelled, or otherwise changed conditions.

Recurring schedules require finite scope, review, cancellation, and Resource bounds. They MUST NOT create unbounded Tasks, workers, Tool calls, or Approval uses. Missed, duplicate, late, conflicting, or unverifiable triggers pause or reconcile rather than silently execute.

## 14. Employee and Temporary Worker supervision

The kernel supervises operational lifecycle and boundaries; it does not supervise domain thought.

For an Employee, the kernel MUST enforce active organization membership, Role Assignment, supervisor or governance owner, escalation path, Authority Grants, budgets, Tool eligibility, suspension, offboarding, credential disposition, and continuity across model replacement. Changing a model MUST NOT create a new Employee identity or transfer authority to the model.

For a Temporary Worker, the kernel MUST enforce one persistent Actor identity, exactly one Sponsor, one bounded purpose, eligible Tasks, least-privilege Tools, explicit Grant, Resource ceiling, expiry or completion condition, delegation prohibition unless separately authorized, and automatic suspension when Sponsor authority becomes inapplicable. Operational completion, expiry, revocation, or archival prevents new work but preserves resolvable identity and attribution.

Worker creation, restoration, purpose, authority, budget, expiry, and archival transitions require the Events and gates in [`LIFECYCLES.md`](LIFECYCLES.md). The kernel MUST NOT spawn a worker because a model asks informally, capacity appears useful, or a Tool is available.

## 15. Tool invocation boundary

A Tool request crosses two distinct boundaries:

1. **Kernel authorization boundary.** The kernel admits a Command, validates the Actor, Work Root, Task, Authority Grant, Policy, Approval, lifecycle, Tool eligibility, risk, reversibility, idempotency, and Resources; atomically appends expected-use reservation and authorized-dispatch Events; and produces a bounded adapter request only afterward.
2. **Adapter execution boundary.** An external adapter authenticates its own Service identity, verifies the immutable dispatch contract, attempts the exact operation against an external system, and reports attributable observations through a new Command.

The adapter request MUST contain a unique invocation identifier, exact Tool and operation version, bounded inputs or protected references, organization and initiating Actor attribution, Work Root, Task when applicable, Authority and Approval references, Resource reservation, idempotency contract, deadline, classification, expected result contract, stop conditions, and audit correlation. It MUST contain no broader credential or permission than required.

Kernel authorization means “this exact attempt may be requested under current governance.” It does not mean the adapter accepted the request, the external system executed it, the expected effect occurred, or the result is valid. The kernel MUST represent at least `authorized`, `dispatched`, `attempted`, `observed`, `verified`, `failed`, `uncertain`, and `compensated` distinctions as applicable. Timeout, transport acknowledgement, adapter success text, or Resource charge alone MUST NOT be recorded as verified success.

The adapter and external system cannot grant organizational authority. Their narrower denial is effective operationally; their willingness to execute cannot override kernel denial. Result evidence MUST identify external version, receipt, integrity, observation time, causal reference, Resources used, uncertainty, and reconciliation status before the kernel admits an outcome transition.

## 16. Resource governance

Resource governance applies independently to money, compute, Tool calls, data access, elapsed time, human attention, reputation, credentials, production capacity, and every other scarce or sensitive Resource defined by Policy.

Before any consequential dispatch, the kernel MUST:

1. calculate or accept an attributable expected-use estimate;
2. aggregate related commitments across Actor, Action, Task, Work Root, vendor, Resource, and period so splitting cannot evade a limit;
3. verify Grant and Approval Resource scope;
4. atomically reserve expected use in each affected dimension; and
5. enforce warning, stop, and escalation thresholds.

After an admitted observation, the kernel MUST record actual, pending, disputed, or unreconciled consumption; reconcile it against the reservation; release only demonstrably unused capacity; and retain variance and external evidence. Unknown actual use remains reserved or is handled by the safer Policy-defined bound. The kernel MUST NOT assume zero cost from silence or release capacity merely because an adapter timed out.

Exhaustion, attempted evasion, material variance, or `BudgetExceeded` prevents new affected consumption and triggers the applicable pause, escalation, or Incident. Unused budget is not transferable without authority. Resource accounting after consumption never substitutes for pre-execution reservation.

## 17. Approval gating and reusable enforcement

Approval and Authority are separate conjunctive gates. An Approval never creates Authority, and a Grant never satisfies a required Approval.

For every use, the kernel MUST validate the exact Decision version, Approval disposition, eligible individual or collective approvers, separation of duties, `approval_mode`, action and Resource scope, risk, budget, assumptions, conditions, effective and expiry state, revocation triggers, Policy versions, review schedule, and current `used_count`.

- `single_use` is atomically consumed by one authorized execution and cannot be reused after dispatch authorization.
- `bounded_repeat` atomically increments use and remains eligible only below its positive usage limit and before any earlier expiry, revocation, invalidation, or condition.
- `standing` applies only to the narrow recurring class of A2 activity expressly permitted by Policy, requires current periodic review, and MUST NOT authorize A4 or unspecified A3 activity.

Material change to operation, Decision, evidence, assumptions, parties, scope, cost, risk, benefit, reversibility, Resource, Policy, or recurring class invalidates the Approval. Every use remains separately attributable and re-evaluated against current Authority, Policy, budget, lifecycle, and stop conditions.

Approval-use claims MUST be idempotent, monotonic, and auditable. `used_count` MUST NOT be decremented. If an external attempt is uncertain, the kernel must reconcile whether the authorized execution was attempted; uncertainty does not restore the use. A new Approval or eligible human Decision is required when further execution is sought and safe reuse is not available under the original recorded scope.

## 18. Suspension, cancellation, timeout, retry, reconciliation, and escalation

### Suspension and cancellation

Suspension immediately prevents new affected Commands, dispatches, Approval uses, subscriptions, scheduled executions, and Resource consumption while preserving identity, evidence, history, and existing commitments. Emergency suspension is bounded to containment, opens or links an Incident, and requires timely human review. Restoration revalidates every ordinary gate.

Cancellation stops future work but does not assert that dispatched external effects were prevented or reversed. The kernel MUST identify in-flight invocations, reservations, commitments, dependencies, workers, Artifacts, and required compensation or reconciliation. A cancellation Event cannot erase an attempt or outcome.

### Timeout and retry

A timeout records absence of a required observation by a deadline; it is not proof of external failure. The affected Action becomes uncertain or reconciliation-required unless result evidence proves otherwise.

Retry requires a new attributable Command, current Work Root, Authority, Policy, Approval, Resource reservation, lifecycle eligibility, and either:

- proof that the prior attempt could not produce the effect;
- an external idempotency guarantee covering both attempts; or
- a consequential Decision and required Approval accepting duplicate-effect risk.

Retry counters, backoff, or scheduler convenience never create authority. Retry limits and stop conditions are enforced before dispatch.

### Reconciliation and escalation

Reconciliation compares admitted intent, adapter evidence, external observations, Resource records, Approval use, and expected result. It records verified, failed, partial, duplicated, compensated, disputed, or unresolved status without rewriting prior Events. Reconciliation may read an external system only through an authorized Tool request and attributable observation Command.

Unknown, stale, conflicting, expired, revoked, over-budget, unverifiable, or materially risky conditions cause refusal, pause, suspension, reconciliation, or escalation. Escalation identifies the unresolved issue, evidence, affected state, eligible Human or Role, deadline, safe default, and requested Decision. Nonresponse confers no authority.

## 19. Organization bootstrap

Constitutional bootstrap is the sole exception to preexisting organizational authority. Because ordinary organizational authority cannot authorize its own creation, the kernel admits one reserved genesis Command directly under the Constitution rather than under a preexisting organizational Authority Grant. The genesis Command MUST be initiated by a verified Human and use reserved genesis Command and Event types, or an equivalently explicit reserved genesis classification that cannot be confused with ordinary operations. The transaction MUST atomically create and link:

- the Organization;
- the initiating Human's persistent Actor identity;
- the constitutional owner or governor Role;
- the Human's active Role Assignment;
- the founding Decision, with the initiating eligible Human as accountable decider and a complete constitutional `duty_reference`;
- initial Authority Grant or Grants limited to the initial lawful governance scope;
- the genesis recording Command;
- founding Events with the initiating Actor, causal references, and organization stream positions; and
- an Audit Record and references sufficient to reconstruct the transaction.

The kernel MUST validate the complete post-transaction invariant set before making any component active. No intermediate partially valid or partially active state is observable, and bootstrap MUST perform no ordinary operational work. A failed pre-append bootstrap set is discarded without authoritative state change. Any detected partial authoritative bootstrap is an invariant and integrity failure that quarantines the affected stream pending accountable review; it is never an operational Organization. No operational Command, Tool invocation, subscription, Employee, Temporary Worker, or ordinary Resource consumption is permitted before bootstrap completes.

An exact retry of the same genesis transaction is idempotent and returns the original disposition. A competing or materially different attempt MUST be rejected or resolved through a deterministic constitutional conflict rule; it MUST NOT merge partial founding claims. Bootstrap authority exists only for the Human-reserved act of establishment and initial governance. After successful bootstrap, the exception is permanently exhausted for that Organization and MUST NOT be reused as standing operational authority, inferred for another Human or Organization, or used to bypass ordinary Role, Grant, Policy, Approval, Event, lifecycle, and audit rules.

## 20. Audit linkage and consequential Decisions

Every consequential operation MUST be reconstructably linked to exactly one Work Root; recording Command; initiating and participating Actors; Role Assignment; Authority Grant and derivation; pinned Policy versions; evidence and epistemic status; consequential Decision; required Approvals and their usage; Tool invocation; affected Resources; lifecycle transitions; causal references; attempted and observed outcomes; reconciliation; and result metrics.

Before authorizing a consequential attempt, the kernel MUST validate that the Decision record satisfies [`DECISION_RECORD.md`](DECISION_RECORD.md), including alternatives, evidence, confidence, risks, benefit, cost, reversibility, Approval requirement, outcome, follow-up review, result metrics, and lessons-learned status. For collective governance, each disposition remains individually attributable and the outcome is deterministically derived from current quorum and voting Policy. The initiating Actor is not automatically the decider.

For every A4 disposition and every A3 disposition reserved by the Constitution or applicable Policy to Humans, the kernel MUST enforce the accountable-decider rule in step 9 of admission independently from Approval eligibility. An Approval records satisfaction of a separate governance condition; it neither selects the underlying disposition nor manufactures Human deciding authority. Decision lifecycle states describe Decision governance only: even `governance_conditions_satisfied` does not establish current execution eligibility, and `executed` records linkage to an attempted Action rather than external success.

The kernel validates presence, identity, version, eligibility, and rule conformance. It MUST NOT generate the Employee's alternatives, evidence, rationale, risk judgment, benefit estimate, result assessment, or lessons learned. Protected content may remain behind authorized references, but missing audit substance cannot be replaced by an empty identifier.

## 21. Memory admission and retrieval boundary

Institutional memory is authoritative only after governed admission. For a `MemoryRecorded` Command, the kernel MUST validate creator, Organization, Work Root or duty, source, acquisition method, observed and effective times, transformation chain, evidence, epistemic status, confidence where applicable, validity, classification, retention, accountable owner, licensing or usage restrictions, and integrity reference.

The kernel MUST enforce append-correction, contradiction, dispute, supersession, redaction, deletion, legal hold, and tombstone rules. It MUST NOT silently merge conflicting Claims, rewrite provenance, promote model output to Evidence, raise confidence because models agree, or mark a Record authoritative without the required Policy-governed validation.

For retrieval, the kernel governs requester identity, Organization, active Role, Authority Grant, purpose, Work Root or duty, jurisdiction, classification, validity, retention, and field-level disclosure. It returns authorized Record identifiers, pinned versions, provenance, validity, epistemic status, confidence, material conflicts, supersession, and access audit linkage.

Search, ranking, semantic matching, summarization, and domain interpretation MAY be performed by specialized services or Employees. Their outputs are not institutional truth until admitted. An index cannot authorize disclosure, override the source Record, conceal conflicts, or become an alternate lifecycle authority. Sensitive or consequential retrieval produces an attributable Event.

## 22. Failure-closed behavior

The kernel MUST refuse, pause, suspend, reconcile, or escalate rather than guess when any required fact is unknown, stale, conflicting, expired, revoked, unverifiable, unsupported, out of scope, over budget, incorrectly classified, or unavailable. The safer or narrower constraint controls until an eligible authority resolves conflict.

Failure closed requires:

- no target transition from a rejected Command;
- no Tool dispatch before authorization and Event append;
- no post hoc Resource reservation;
- no Approval use without independent Authority;
- no success from intent, dispatch, acknowledgement, timeout, charge, or model assertion alone;
- no lifecycle transition through an undefined or stale state;
- no subscription disclosure across Organization, purpose, classification, or jurisdiction boundaries;
- no schedule-triggered work without a new attributable Command and current Work Root validation;
- no replay effects;
- no silent fallback to an older Policy, schema, Grant, Approval, projection, or external observation; and
- no erasure of the evidence needed to explain failure.

Availability pressure, urgency, prior success, Actor seniority, model confidence, technical access, and external-system willingness MUST NOT weaken these rules. A safe refusal is valid kernel behavior.

## 23. Prohibited kernel behaviors

A conforming kernel MUST NOT:

1. invent, infer, or silently amend a Command, Work Root, Actor, Role Assignment, Authority Grant, Policy, Approval, Decision, Evidence item, Resource balance, successful result, or external state;
2. treat a model, Tool, Credential, adapter, subscription, scheduler, or external service as a source of organizational authority;
3. perform domain planning, research, evidence interpretation, creative selection, or result judgment on behalf of an Employee;
4. admit a Task or Action with both or neither Work Root forms;
5. dispatch a Tool before all gates, reservation, Approval use, and Event append succeed;
6. conflate request authorization, dispatch, attempt, acknowledgement, observation, verification, and success;
7. apply an Approval as Authority, reuse an exhausted Approval, or permit standing Approval for A4 or unspecified A3 activity;
8. derive current permission from a stale schedule, cache, projection, conversation, model context, or prior run;
9. trigger external effects, notifications, timers, charges, subscriptions, retries, or compensation during replay;
10. bypass Policy, authority, or Approval because a lifecycle transition is technically valid;
11. reserve Resources only after consumption, split commitments to evade aggregation, or treat unknown use as zero;
12. create a Temporary Worker without one Sponsor, bounded purpose, Grant, budget, expiry, and attributable Command;
13. reuse or erase an expired or archived worker identity;
14. deliver an Event or referenced content across an unauthorized Organization or classification boundary;
15. accept a Tool or external report as verified outcome without provenance, integrity, causal reference, and reconciliation status;
16. represent a Governing Body as a fictional Human or treat the technical initiator as the collective decider; or
17. allow a specialized service to become an alternate authority, identity, Policy, memory, Event-ordering, Resource-accounting, or lifecycle source.

## 24. Conformance and adversarial testing

Conformance requires deterministic, integration-boundary, recovery, and adversarial tests. Tests MUST inspect both the expected Event history and the absence of forbidden state changes or external effects. A passing happy path is insufficient.

### Minimum conformance test matrix

| Area | Required adversarial case | Required result |
|---|---|---|
| Schema and version | Unknown, downgraded, ambiguous, oversized, or malformed Command | Reject before state change, reservation, Approval use, or dispatch; record safely when attributable |
| Organization isolation | Valid Actor references a target, Resource, Event, or subscription in another Organization | Reject without disclosure; record attempted boundary violation |
| Identity and Role | Missing, suspended, archived, forged, or model-only initiator; inactive Role Assignment | Reject or suspend; never infer identity or Role |
| Authority | Missing, expired, revoked, overbroad, wrong recipient, broken delegation chain, or conflicting Grant | Fail closed under narrowest constraint; no Approval may cure missing authority |
| Policy | Missing version, lower rule that expands authority, stale evaluation, or human-reserved A4 request from AI | Reject or escalate to eligible Human; never silently fall back |
| Human accountable decider | AI Actor recorded as accountable decider for A4 or Human-reserved A3, with separate Human Approval attached | Reject or escalate; Approval does not cure invalid accountable-decider attribution or convert the Decision into a Human Decision |
| Work Root | Task or Action has both roots, neither root, inactive Goal, incomplete duty, or scope mismatch | Reject without creating work |
| Approval | Wrong Decision version, self-approval, expired or invalidated Approval, exhausted use, stale standing review, A4 standing use | Reject; do not increment use or dispatch |
| Approval concurrency | Two Commands race for the last `single_use` or bounded use | At most one claim succeeds; ordering and loser rejection are auditable |
| Resources | Insufficient reservation, transaction splitting, delayed external charge, unknown actual use, or concurrent limit race | Stop before dispatch; aggregate; retain safe reservation until reconciliation |
| Lifecycle | Transition from wrong version or state; suspended dependency; restoration without review | Reject deterministically; no target mutation |
| Idempotency | Duplicate delivery and conflicting payload under the same key | Return original disposition for exact duplicate; reject conflict; no repeated effect |
| Event append | Failure before append, partial append attempt, duplicate Event, or ordering race | No authorized dispatch before durable append; one immutable order; safe recovery |
| Tool boundary | Adapter acknowledgement, timeout, success text without evidence, partial external effect, or duplicated attempt | Preserve attempt/uncertain status; reconcile; never invent success |
| Replay | Stream includes historical Tool, notification, charge, retry, Approval use, schedule, or worker Events | Rebuild projections only; zero external calls and zero new Commands or Events |
| Projection rebuild | Corrupt checkpoint, unknown Event schema, integrity mismatch, or divergent projection | Discard cache or stop at exact position; fail affected reads closed |
| Canonical relationships | Stale or forged inverse Role, Grant, or Governing Body collection conflicts with the canonical relationship entity or accepted Events | Fail closed and report integrity failure; never treat the inverse collection as competing authority |
| Subscription | Cross-organization request, classification downgrade, filter side channel, redelivery, or checkpoint gap | Deny leakage; deliver at least once within authorized scope; expose gap explicitly |
| Scheduling | Due item has expired Grant, cancelled Work Root, exhausted Approval, depleted budget, or duplicate trigger | Re-evaluate and reject, pause, or escalate; no stale-authority execution |
| Worker supervision | Sponsor suspended, expiry races with dispatch, unauthorized sub-worker, or archived identity reused | Prevent new work, preserve attribution, reject delegation or reuse |
| Bootstrap | Exact retry; competing or materially different genesis attempt; partial append; ordinary work during genesis; reused bootstrap authority; or invalid founding links | Exact retry returns original disposition; conflict rejects or follows deterministic constitutional resolution; no active partial Organization; partial authority quarantines; no ordinary work; exception permanently exhausted after completion |
| Memory admission | Missing provenance, model citation without source, contradictory Claim, unauthorized classification, or silent correction | Reject or mark unresolved; preserve conflicts and provenance; no unauthorized disclosure |
| Collective governance | Fictional Human body, missing vote, ineligible member, failed quorum, changed voting Policy, or initiator treated as decider | Reject outcome; preserve individual dispositions and current Policy derivation |
| Failure and recovery | Network partition, clock anomaly, stale projection, unavailable Policy evaluator, or uncertain external state | Fail closed or escalate; never guess, backdate, or claim success |

### Determinism evidence

A conforming implementation MUST demonstrate that repeated pre-commit evaluation of the same Command, bound evaluation time, prior stream position, projections, schemas, and Policy versions yields the same disposition, semantic Event set, lifecycle state, reservations, Approval usage, and audit linkage. After commit, idempotent redelivery MUST return the same recorded identifiers and positions. Tests that deliberately vary admission order are distinct inputs and MUST verify deterministic results for each recorded order.

### Negative-effect evidence

Tests for rejection, replay, suspension, cancellation, timeout, stale scheduling, and failed append MUST verify the absence of Tool calls, adapter dispatch, notifications, external writes, real Resource consumption, new worker activity, unauthorized Event disclosure, and unrecorded Approval usage. Logs that merely lack a success message are not sufficient; effect boundaries must be instrumented or otherwise demonstrably observed.

### Review requirement

Every kernel release MUST include a traceable conformance report identifying the specification versions tested, Policy fixtures, adversarial cases, observed Events, projection results, external-effect observations, deviations, and accountable reviewer. A deviation from this contract is a failed conformance result, not an undocumented implementation choice.
