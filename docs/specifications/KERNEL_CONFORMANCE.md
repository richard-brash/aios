# AIOS Kernel Conformance Specification

**Specification version:** 0.0.2
**Status:** Normative acceptance-test contract

## 1. Purpose and scope

This document defines the minimum externally observable behavioral test suite that every AIOS kernel implementation MUST pass. It translates [`KERNEL_CONTRACT.md`](KERNEL_CONTRACT.md) and the executable ontology into deterministic acceptance scenarios without prescribing implementation technology.

Conformance testing observes submitted Commands, bound evaluation inputs, immutable Events, authoritative AIOS projections, governed external references, Resource and Approval effects, Tool dispatches, subscription deliveries, audit linkage, and the absence of prohibited effects. It MUST NOT inspect or require private model reasoning, internal source structure, storage layout, programming language, database, message transport, deployment platform, model provider, or test framework.

This specification is governed by [`ARCHITECTURE_PRINCIPLES.md`](ARCHITECTURE_PRINCIPLES.md), [`ENTITY_MODEL.md`](ENTITY_MODEL.md), [`EVENT_MODEL.md`](EVENT_MODEL.md), [`INVARIANTS.md`](INVARIANTS.md), [`LIFECYCLES.md`](LIFECYCLES.md), [`DECISION_RECORD.md`](DECISION_RECORD.md), `KERNEL_CONTRACT.md`, and the constitutional documents. A test oracle MUST apply the versions named by the test evidence.

## 2. Conformance terminology

- **Implementation under test (IUT):** the complete kernel boundary being evaluated, including any specialized services to which it delegates normative mechanics.
- **Test harness:** an external observer and fault controller that submits inputs, supplies controlled adapter and external-system behavior, captures outputs, and MUST NOT confer authority.
- **Canonical fixture:** a versioned, reusable set of stable entities, Events, projections, Policies, and controlled external observations defined by this specification.
- **Mandatory scenario:** a test whose identifier appears in Sections 12–28, Section 13.1, or the adversarial matrix. Every mandatory scenario MUST pass unless its requirement is formally inapplicable to a constitutionally valid implementation; the conformance report MUST justify and independently approve any inapplicability. The suite contains 252 catalog identifiers; a parameterized row may require multiple executions without changing that catalog count.
- **Disposition:** `accepted`, `rejected`, `previously_admitted`, `paused`, or `escalated` as defined by the kernel admission output contract.
- **Safe failure:** no unauthorized transition, disclosure, Tool dispatch, Resource or Approval mutation, success assertion, or replay effect; an attributable rejection, pause, suspension, reconciliation, Incident, or escalation is recorded where a valid recording boundary exists.
- **Exact semantic equality:** equality of every normative field and meaning after canonical normalization, regardless of serialization syntax or field order.
- **Stable ordering equality:** equality of organization stream positions and relative logical Event order. Equal timestamps do not relax order.
- **Projection equivalence:** identical normative entity identities, versions, lifecycle states, relationships, authority, Approval usage, Resource accounting, memory status, audit links, and governed external references after ignoring explicitly permitted implementation metadata.
- **Permitted implementation metadata:** nonnormative diagnostics, trace transport identifiers, storage locations, performance measures, and integrity mechanisms whose presence does not alter normative meaning, order, access, or outcome.
- **Forbidden nondeterministic output:** any change in disposition, normative Event semantics or order, projection, Resource effect, Approval use, dispatch, delivery authorization, or audit link when all normative inputs are identical.

In this specification, **Employee** means the constitutional AI Employee and excludes Human Actors. A model is a replaceable computational Resource, never an Actor, accountable decider, approver, or Authority holder.

The keywords **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

### 2.1 Conformance levels

Conformance is reported independently at these levels:

| Level | Required evidence |
|---|---|
| Document conformance | An explicit mapping from every kernel interface, state boundary, and control to the governing AIOS specification clauses and versions |
| Behavioral conformance | All mandatory deterministic and lifecycle scenarios pass with the required observable results |
| Adversarial conformance | All mandatory fault, hostile-input, isolation, concurrency, and unavailable-governance scenarios fail safely |
| Replay conformance | Every replay and recovery scenario rebuilds equivalent projections and governed references with zero external effects |
| Operational conformance | The complete evidence package is reproducible, versioned, integrity-verifiable, and independently reviewable |

Success at one level MUST NOT imply, waive, or substitute for another. An overall claim of “AIOS kernel conformant” requires all five levels for the same IUT release and specification set.

## 3. Test environment assumptions

The harness MUST provide:

- isolated IUT instances or provably resettable organization streams;
- a controllable trusted admission-time source that binds one explicit `evaluation_time` per original Command;
- controllable Tool adapters, subscription endpoints, governance-service boundaries, and at least one opaque external system;
- observable effect counters for Tool calls, external writes, communications, charges, notifications, schedule materializations, Approval uses, and Resource movements;
- fault points before, during, and after admission append and at every external boundary;
- deterministic fixture loading and export of Events, projections, audit references, and governed external references;
- classification-aware subscriber identities and two-Organization isolation;
- no ambient credentials, network access, or prior state capable of satisfying a missing fixture requirement; and
- a way to prove that replay uses effect-prohibited boundaries rather than merely omitting success logs.

The harness controls observations but MUST NOT directly edit authoritative AIOS projections. Fixtures are established by their canonical Event streams or by a separately verified bootstrap/import procedure whose resulting Event history is identical in normative semantics.

## 4. Canonical test-fixture requirements

Every fixture identifier and version is stable across runs. The canonical namespace below is illustrative and normative in meaning; an IUT MAY map identifiers to its native representation only if the evidence preserves a one-to-one stable mapping.

### 4.1 Organizations and Actors

| Fixture | Required state |
|---|---|
| `org-alpha@1` | Active Organization with complete bootstrap, current Constitution, Policies, budgets, and audit stream |
| `org-beta@1` | Active isolated Organization with distinct Policies, Resources, Events, and classifications |
| `human-owner-alpha@1` | Verified Human, constitutional owner/governor of Alpha, active founding Role and Grant |
| `human-governor-alpha-2@1` | Verified Human and member of Alpha Governing Body |
| `human-owner-beta@1` | Verified Human and constitutional owner/governor of Beta |
| `employee-alpha-router@1` | Active Employee with A1/A2 bounded authority |
| `employee-alpha-operator@1` | Active Employee with distinct Role and Tool eligibility |
| `worker-alpha-specialist@1` | Persistent Temporary Worker identity with one Sponsor, bounded purpose, Task, budget, expiry, and historical audit links |
| `service-alpha-scheduler@1` | Persistent scheduling Service Actor with narrowly scoped Grant |
| `service-alpha-adapter@1` | Authorized Tool-adapter Service Actor |
| `service-forged@1` | Unrecognized or unauthenticated adapter identity used only for rejection tests |
| `body-alpha-board@1` | Governing Body with three individually attributable Human membership/disposition slots, quorum, recusal, and voting Policy |

The fixture set MUST include active, expired, revoked, and future-dated Role Assignments. It MUST support a suspended Actor without changing identity.

Role Assignment records and their accepted Events MUST be the fixture authority for Actor-to-Role occupancy. Authority Grant records and accepted Events MUST be authoritative for issuer, recipient, and delegation edges. Governing Body membership records and accepted Events MUST be authoritative for body membership. Matching, stale, forged, and directly edited inverse collections MUST be supplied as derived-projection variants; none may independently establish eligibility or authority.

### 4.2 Authority, Policy, Work, Approval, and Resources

The fixture MUST contain:

- active, expired, revoked, future-dated, overbroad, narrowed, and delegated Authority Grants, including one valid narrowing delegation and one invalid expansion attempt;
- conflicting Policies at different precedence levels: a higher rule, a lawful lower narrowing rule, and a lower attempted expansion;
- one active Goal-rooted Work Root, one complete duty-rooted Work Root, one inactive Goal, one incomplete duty reference, and one invalid dual-root input;
- Tasks attached directly to the active Goal and complete duty without Project, Objective, or Plan, plus optional Project, Objective, and Plan references used only where they add organizational structure;
- Tasks and Actions in proposed, ready, assigned, in-progress, blocked, suspended, completed, failed, cancelled, expired where applicable, and archived states sufficient to test every legal and illegal transition;
- one valid `single_use` Approval with `used_count=0`, one exhausted single-use Approval, one `bounded_repeat` Approval one use below its limit, one exhausted bounded Approval, one current `standing` A2 Approval, one stale-review standing Approval, one expired Approval, and one revoked Approval;
- money, compute, Tool-call, data-access, elapsed-time, and human-attention Resources, each with independent units, reservations, consumption, stop thresholds, and aggregation dimensions;
- one complete consequential Decision conforming to `DECISION_RECORD.md`, plus Decisions in `governance_conditions_satisfied` and `executed` states whose current Authority, Policy, evidence, risk, Resource, or external-outcome conditions require revalidation; and
- one collective-governance Decision with individual votes or dispositions, quorum rule, current Policy versions, dissent or recusal, and derived outcome.

### 4.3 Tools, external state, memory, subscriptions, and Incident

The fixture MUST contain:

- one controllable Tool adapter with request, attempt, callback, evidence, timeout, duplicate, contradiction, denial, and reconciliation behaviors;
- one external system whose authoritative domain state and content cannot be reconstructed from AIOS replay, but whose stable references, observed versions, integrity identifiers, ownership, classification, provenance, and reconciliation state are recorded;
- classified Memory Records at public/internal and restricted levels, including conflicting Claims, material contradictory Evidence, a superseded Claim, a derived Record with input links, a legal hold, and a deletion-eligible Record;
- governed content references with later redaction, deletion, sealing, access-restriction, tombstone, and cryptographic-erasure Events, including content the harness can prove is no longer retrievable;
- authorized same-Organization subscribers, a classification-restricted subscriber, an unauthorized subscriber, and an Actor from the other Organization;
- an open Incident with credible stop conditions capable of suspending an Actor, Task, Tool, Grant, subscription, and scheduled dispatch; and
- verified checkpoints plus corrupted, stale, and mismatched checkpoint variants.

### 4.4 Fixture integrity

Every fixture export MUST include exact specification versions, stable identifiers, named `entity_revision` and business-content versions, complete initial authoritative Event streams with stream positions, expected baseline projections, Policy contents and precedence, controlled external reference manifests, integrity identifiers, and classification labels. `schema_version`, `entity_revision`, business-content version, lifecycle state, and stream position MUST NOT be conflated. Fixtures MUST NOT rely on the current wall clock, random identity generation during a test, ambient model state, or undisclosed prior Events.

### 4.5 Normative test-case format

Every mandatory scenario MUST be instantiated as a record containing all fields below. A field with no expected effect contains the explicit value `none`; it is never omitted.

| Field | Required content |
|---|---|
| Test identifier | Stable suite-prefixed identifier from this document |
| Title | Concise behavioral claim |
| Architectural requirement | Exact specification document, section, invariant, and version references |
| Initial authoritative Event stream | Fixture stream identifiers, complete positions, integrity value, and scenario-specific Event delta |
| Initial projection state | Fixture projection version and relevant entity, Approval, Resource, memory, schedule, and audit state |
| Submitted operation | Complete Command envelope, replay range, recovery operation, subscription action, or controlled fault |
| Bound evaluation time | Exact immutable time input for admission; replay uses historical times and no current-time read |
| Expected disposition | One normative disposition or replay/recovery result |
| Expected Events | Event types in exact logical order; the complete common Event envelope; every semantic field required by the applicable versioned Event-type schema; omission or explicit not-applicable treatment where permitted; absence of prohibited fields; exact semantic values for every applicable field; and stream positions relative to baseline |
| Expected projection changes | Exact normative changes or `none` |
| Expected Resource effects | Reservations, use, release, reconciliation, stop condition, or `none` |
| Expected Approval-use effects | Mode, prior and next `used_count`, state, or `none` |
| Expected Tool-dispatch behavior | Exact dispatch count and authorized request semantics, normally zero for rejection and replay |
| Expected subscription deliveries | Subscriber, Event identity, order, classification/redaction, delivery count constraints, or `none` |
| Expected audit linkage | Recording Command, Work Root, Actors, Role, Grant, Policy, evidence, Decision, Approval, Tool, Resource, causal, result, and Incident links as applicable |
| Prohibited side effects | Complete negative-effect assertions relevant to the scenario |
| Replay expectation | Expected reconstructed projection and zero-effect assertion after the scenario stream is replayed |
| Failure reason code | Stable semantic reason for nonacceptance, or `not_applicable` |

Scenario tables below state the distinguishing input and oracle. Their executable test records MUST fill every field above using canonical fixtures.

## 5. Event-stream comparison rules

Event comparison MUST use exact semantic equality for Event type, schema version, the complete common envelope, payload semantics, audit-critical references, and every semantic field applicable to that Event instance. It MUST use stable ordering equality for organization stream position and all within-Command Event order.

The oracle MUST first resolve the applicable versioned Event-type schema and validate each semantic field's classification as **required**, **optional**, **prohibited**, or **explicitly not applicable**. A prohibited field fails even when empty. An omitted optional field and an explicit not-applicable field are equivalent only when that schema expressly permits both representations with the same meaning. Empty arrays, generic results, fabricated confidence, placeholder evidence, or ceremonial `not_applicable` values MUST NOT simulate conformance. Deterministic mechanical Events MAY omit or mark epistemic status, confidence, evidence, result, or Resource references not applicable only when their schemas permit it. Consequential Events MUST include every evidence, result, Resource, and epistemic field material to accountability and interpretation.

Canonical fixtures and submitted inputs use literal stable identifiers. For a new opaque identifier allocated by the IUT, the oracle assigns an expected symbolic binding such as `event.acceptance[1]`. Separate clean runs MAY use different opaque encodings only if each binding is globally unique, occupies the exact expected logical position, preserves every expected relationship, and is reused unchanged on idempotent redelivery. An IUT MUST NOT use identifier variability to hide changed cardinality, order, causality, attribution, or audit linkage. A specification-derived or caller-supplied identifier is compared literally.

Serialization syntax, object-key order, whitespace, transport envelope, physical checksum algorithm, storage address, and nonnormative diagnostics MAY differ. Implementations MUST provide a canonical comparison view that separates these permitted metadata fields from normative fields. A test MUST fail if normalization hides a changed identifier relationship, time, version, scope, classification, order, result, or authority meaning.

Rejection Events are compared only when a valid organization and recording boundary exists. Malformed, hostile, or unattributable input MUST produce no Organization Event; non-authoritative platform security telemetry is outside Event equality and MUST be identified as such.

## 6. Projection-equivalence rules

Two projections are equivalent only when all normative entities, identifiers, named versions, lifecycle states, Work Roots, canonical relationships, Policy versions, authority and delegation state, Approval usage, Resource reservations and consumption, schedules, memory validity, supersession and governed availability, Incident controls, audit links, and governed external references are semantically equal.

Index layout, cache entries, precomputed views, inverse navigation collections, internal timestamps unrelated to normative Events, and performance metadata are ignored only if they cannot affect a later admission or disclosure. Projection comparison MUST validate canonical relationship entities, the source Event history, and last applied stream position; equal-looking projections built from conflicting canonical relationship history or corrupt, missing, reordered, or unknown Events do not pass. A derived inverse collection that conflicts with canonical state is an integrity failure, not projection equivalence.

## 7. Determinism requirements

Each deterministic scenario MUST be evaluated at least twice from the identical initial Event stream, projection, Command, bound `evaluation_time`, external observations, schemas, and Policy versions. Before commit, both evaluations MUST yield the same disposition and semantic Event set. After commit, redelivery MUST return the original identifiers and positions through idempotency.

Tests MUST NOT use current wall-clock time as an unstated oracle. Expiry boundaries use explicit times immediately before, at, and after the fixture condition. Randomness, model output, external callback order, and network results are controlled inputs recorded before they influence authoritative state. Different admission orders are different cases and MUST each have deterministic expected order.

Forbidden nondeterminism includes different acceptance, reason code, Event semantics or order, projection, Approval use, Resource reservation, dispatch count, subscriber authorization, or audit linkage under identical normative inputs.

## 8. Replay requirements

Replay MUST reconstruct equivalent authoritative AIOS projections and governed external references from the canonical stream without issuing Commands or Events or invoking Tools, models, adapters, subscriptions, timers, notifications, human workflows, external communications, charges, retries, compensation, or real Resource mutations. Historical Approval and Resource Events alter only the rebuilt projection.

Replay MUST apply later redaction, deletion, sealing, access-restriction, tombstone, and cryptographic-erasure Events to reconstruct governed availability. It MUST preserve the minimum Event identity, position, provenance, and accountability metadata required by Policy while never restoring, retrieving, or disclosing erased or inaccessible content. A historical reference is neither current disclosure authority nor proof that an external system remains reconstructable.

## 9. Failure-closed requirements

Every rejection and injected failure MUST prove the absence of unauthorized target transitions, dispatches, disclosures, Approval use, Resource consumption, success assertions, and audit fabrication. Unknown, stale, conflicting, expired, revoked, unverifiable, over-budget, unavailable-governance, or integrity-failed state MUST reject, pause, suspend, reconcile, or escalate under the narrower safe constraint.

## 10. Minimum conformance test matrix

The minimum suite contains 252 mandatory scenarios. Every scenario MUST be instantiated using the normative test-case format in Section 4.5.

| Suite | Identifier range | Mandatory scenarios | Primary contract |
|---|---|---:|---|
| Adversarial and fault injection | `ADV-001`–`ADV-022` | 22 | Safe behavior under unavailable, hostile, corrupt, delayed, duplicated, and live-effect conditions |
| Bootstrap | `BST-001`–`BST-012` | 12 | Atomic constitutional genesis and permanent bootstrap-authority containment |
| Command admission | `CMD-001`–`CMD-014` | 14 | Validation, attribution, isolation, versions, idempotency, and evaluation time |
| Authenticated admission boundary | `ADB-001`–`ADB-024` | 24 | Pre-boundary rejection, exact Organization and Actor attribution, mutation prohibition, and bootstrap separation |
| Authority and Policy | `AUT-001`–`AUT-016` | 16 | Explicit authority, delegation, precedence, and Human accountable-decider power |
| Work Root | `WRT-001`–`WRT-010` | 10 | Exclusive Goal-or-duty traceability with optional planning structures |
| Approval | `APR-001`–`APR-014` | 14 | Mode, atomic usage, separation from Authority, and concurrency |
| Resource governance | `RES-001`–`RES-012` | 12 | Pre-dispatch reservation, aggregation, independent dimensions, and reconciliation |
| Lifecycle | `LIF-001`–`LIF-012` | 12 | Legal transitions, dependencies, evidence, suspension, and durable identity |
| Scheduling and orchestration | `SCH-001`–`SCH-015` | 15 | Governed schedule admission and trigger enforcement without scheduling strategy |
| Tool and reconciliation | `TOL-001`–`TOL-012` | 12 | Authorization/attempt/result separation and adapter containment |
| Event ordering and idempotency | `EVT-001`–`EVT-010` | 10 | Immutability, organization order, causal provenance, and epistemic validity |
| Canonical relationships | `REL-001`–`REL-007` | 7 | Canonical relationship authority, inverse projection integrity, and replay rebuilding |
| Subscription isolation | `SUB-001`–`SUB-010` | 10 | Organization, purpose, classification, order, and redelivery |
| Memory governance | `MEM-001`–`MEM-012` | 12 | Provenance, admission, retrieval, conflict, retention, and derived records |
| Operations and escalation | `OPS-001`–`OPS-012` | 12 | Suspension, cancellation, timeout, retry, reconciliation, and restoration |
| Audit and Decisions | `AUD-001`–`AUD-015` | 15 | Complete consequential trace, Decision-state revalidation, and collective attribution |
| Replay and recovery | `RPL-001`–`RPL-015` | 15 | Projection equivalence, governed availability, history integrity, and zero effects |
| Portability and model replacement | `POR-001`–`POR-008` | 8 | Institutional continuity across environments and replaceable models |
| **Total** |  | **252** | All scenarios are independently mandatory |

## 11. Adversarial and fault-injection matrix

The following cross-cutting fault scenarios are mandatory. Each fault MUST also be applied to every relevant suite case where it can change the safe outcome; passing the standalone row does not waive suite-specific fault coverage.

| ID | Fault injection | Safe expected outcome |
|---|---|---|
| ADV-001 | Event append fails before commit | No authoritative Event set, projection mutation, reservation, Approval use, dispatch, or delivery; retry may use the same idempotency key |
| ADV-002 | Partial storage outage during atomic append | Complete set visible or none; never a partial transition; quarantine and Incident if atomicity cannot be established |
| ADV-003 | Stale projection supplied to admission | Reject with stale-version reason or rebuild before reevaluation; never evaluate against stale permission |
| ADV-004 | Exact message delivered twice | Original disposition returned; no duplicate Event, use, reservation, dispatch, or delivery identity |
| ADV-005 | Messages delivered out of order | Organization order enforced or gap exposed; no reordered transition application |
| ADV-006 | Tool callback delayed beyond timeout | Action remains uncertain/reconciling; no assumed failure, release, retry, or success |
| ADV-007 | Tool callbacks contradict | Preserve both observations, mark disputed, reconcile or open Incident; no silent overwrite |
| ADV-008 | Checkpoint integrity is corrupt | Discard and rebuild from verified history or fail recovery closed at exact position |
| ADV-009 | Policy evaluation boundary unavailable | Reject, pause, or escalate; no fallback Policy or permission |
| ADV-010 | Identity resolution boundary unavailable | Reject or pause; do not infer Actor from credential, session, or display name |
| ADV-011 | Authority evaluation boundary unavailable | Reject or pause; Approval, Role, Tool, or credential does not substitute |
| ADV-012 | Resource meter unavailable | No consequential dispatch; retain safe reservation or pause for reconciliation |
| ADV-013 | External system unavailable | Record failure or uncertainty as observed; no success or automatic Resource release |
| ADV-014 | External clock skew | Use bound kernel evaluation time and recorded external observation time separately; no altered expiry decision |
| ADV-015 | Hostile oversized input | Reject before organization admission or effect; no Organization Event unless valid attribution boundary is established |
| ADV-016 | Forged Actor identity | Reject without disclosure or transition; record security Incident when attributable |
| ADV-017 | Forged Approval reference | Reject; do not consume use, reserve, or dispatch; link attempted forgery if attributable |
| ADV-018 | Forged Tool result | Reject observation or mark disputed; never verify outcome or release on forged evidence |
| ADV-019 | Subscriber attempts organization escape | Deliver nothing; do not expose Event existence or protected metadata; audit denial |
| ADV-020 | Replay process has live adapters configured | Effect guard prevents all invocation; test fails critically on any attempted live effect |
| ADV-021 | Classification service unavailable | Deny retrieval and delivery; do not default to a less restrictive classification |
| ADV-022 | Audit-link builder unavailable | Consequential completion rejects or pauses; operation is not marked complete |

## 12. Bootstrap test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| BST-001 | Reserved genesis Command directly invokes the Constitution with a verified Human and complete founding set | Atomically accept Organization, Human, owner/governor Role, Role Assignment, founding Decision naming that Human as accountable decider, initial Grants, recording Command, reserved genesis Events, stream positions, and Audit Record references without requiring a preexisting organizational Grant |
| BST-002 | Append fails or exposes only part of the authoritative genesis set | No partial state is observable on clean failure; any detected partial authoritative state is quarantined as an invariant and integrity failure pending accountable review, never treated as an operational Organization |
| BST-003 | Initiating Human verification is missing or invalid | Reject with identity-verification reason; create no Organization Event |
| BST-004 | Founding set omits Role, Role Assignment, Decision, Grant, recording Command, founding Event, or Audit Record reference | Reject atomically; no component becomes active |
| BST-005 | Submit operational Command, subscription, Employee, Temporary Worker, Tool invocation, or ordinary Resource consumption while bootstrap is incomplete or as part of genesis | Reject with bootstrap-incomplete or genesis-scope reason; admit no ordinary work or effect |
| BST-006 | Redeliver exact bootstrap Command and idempotency key | Return original disposition, identifiers, stream positions, and evaluation time; do not create a second Organization or founding Event set |
| BST-007 | Competing genesis attempt uses a different Human, Organization identity, founding Decision, Grant, or other material founding data | Reject or apply the declared deterministic constitutional conflict rule; never merge partial founding claims or disturb a completed bootstrap |
| BST-008 | Name an Employee or model as constitutional owner | Reject; only verified eligible Human or lawful Governing Body may own or govern |
| BST-009 | Represent Governing Body as one fictional Human Actor | Reject; require body identity, real members, individual dispositions, quorum, and current Policy |
| BST-010 | Attempt to reuse bootstrap authority for an operational Action after establishment | Reject under ordinary authority rules; genesis is the sole preexisting-authority exception and is permanently exhausted for the Organization |
| BST-011 | Founding Decision records an AI Employee as accountable decider while a Human initiates or approves bootstrap | Reject; the verified founding Human must be the accountable decider and Approval or technical initiation cannot cure the attribution |
| BST-012 | Bootstrap uses an ordinary or unreserved Command/Event type or ambiguous classification | Reject before activation; require reserved genesis types or an equivalently explicit reserved genesis classification |

## 13. Command-admission test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| CMD-001 | Submit fully valid reversible Command with current versions and gates | Accept; append exact ordered Events, reservation, audit links, and authorized next step |
| CMD-002 | Submit malformed envelope with no valid organization or attribution boundary | Reject before admission; no Organization Event, projection, reservation, use, dispatch, or delivery |
| CMD-003 | Submit unsupported Command schema or operation version | Return a typed non-recorded pre-boundary rejection; do not resolve admission or touch an Organization namespace |
| CMD-004 | Alpha Command references Beta Actor, Resource, or Event without governed relationship | Reject without revealing Beta content or existence beyond safe denial |
| CMD-005 | Submit unknown initiating Actor | Reject; do not infer from credential, model, session, or name |
| CMD-006 | Submit Command from suspended Actor | Reject or preserve suspension; no new affected work |
| CMD-007 | Submit expected entity version older than current projection | Reject stale-version; require reevaluation and produce no target transition |
| CMD-008 | Submit exact duplicate of accepted Command | Return original disposition, Event IDs, positions, evaluation time, and audit reference |
| CMD-009 | Exact duplicate references single-use Approval already consumed by original | Return original; `used_count` remains unchanged after original use |
| CMD-010 | Exact duplicate originally reserved Resources | Return original; no second reservation or aggregation increment |
| CMD-011 | Exact duplicate originally dispatched Tool request | Return original; adapter dispatch count remains one |
| CMD-012 | Reuse idempotency key with changed payload, Work Root, or target | Reject idempotency conflict; preserve first disposition |
| CMD-013 | Redeliver original after wall clock advances beyond Grant expiry | Return original evaluation time and disposition; do not reevaluate as a new Command |
| CMD-014 | Bind same original inputs to two precommit evaluations | Produce exact semantic equality of disposition and Event set |

### 13.1 Authenticated recording-boundary test suite

This suite proves the ordinary post-genesis boundary between effect-free input handling and attributable Organization processing. Support resolution follows Model A: unsupported schema, operation, or operation version is pre-boundary. Bootstrap uses its reserved constitutional path.

| ID | Input or fault | Required observable result |
|---|---|---|
| ADB-001 | Structurally malformed ordinary input | Return a typed non-recorded rejection with no authoritative disposition, Event, audit, stream access, or idempotency effect |
| ADB-002 | Unsupported schema, operation, or operation version | Return a typed non-recorded rejection before admission resolution and with no Organization effect |
| ADB-003 | Well-formed but unresolved Organization identifier | Return `ORG.UNKNOWN` without treating identifier syntax as proof or touching an Organization namespace |
| ADB-004 | Syntactically valid Organization identifier with no authoritative completed-genesis boundary | Fail closed as a non-recorded admission denial |
| ADB-005 | Unknown or unauthenticated initiating Actor | Return a bounded non-recorded identity denial without Organization mutation |
| ADB-006 | Authentic Actor identity attributable only to another Organization | Return a non-recorded boundary or identity denial; do not search or fall back across Organizations |
| ADB-007 | Any admission denial while observing the Event-store read port | Perform no Organization stream read |
| ADB-008 | Any admission denial while observing append and audit ports | Append no Event and create no authoritative audit record |
| ADB-009 | Any admission denial while observing authoritative allocators | Allocate no authoritative disposition, Event, or Audit Record identifier |
| ADB-010 | Any admission denial while observing governance | Do not invoke Organization governance |
| ADB-011 | Any admission denial while observing domain handling | Do not invoke a domain handler |
| ADB-012 | Any admission denial while observing Organization idempotency | Inspect and create no Organization-scoped idempotency entry |
| ADB-013 | Repeat identical admission-denied input | Return an equivalent non-recorded result; do not treat it as Organization exact redelivery or mutate state |
| ADB-014 | Resolver establishes a boundary whose canonical Organization exactly matches the claim | Bind that exact Organization and its completed-genesis reference; permit later Organization processing only from this proof |
| ADB-015 | Resolver authenticates and attributes the exact claimed Actor in the established Organization | Bind that exact Actor and authentication evidence; aliases or identity substitution fail closed |
| ADB-016 | Admission succeeds but operation Authority is absent | Continue to governance, which denies independently; admission success itself grants no Authority |
| ADB-017 | Governance denies after admission success | May atomically append the specified attributable rejection and audit sequence to the proven Organization stream |
| ADB-018 | Deterministic handler rejects after admission success | May atomically append the specified attributable rejection and audit sequence to the proven Organization stream |
| ADB-019 | Exact redelivery of an attributable rejection already recorded after admission | Return the original disposition without another append, allocation, or effect |
| ADB-020 | Hostile input names an Organization that is not authoritatively resolved | Do not create that Organization stream or any record within it |
| ADB-021 | Admission-denied input names an Organization other than one with existing history | Preserve the unrelated Organization history exactly |
| ADB-022 | Bootstrap submission is presented to the ordinary resolver path | Reject before ordinary Organization processing; bootstrap remains on its reserved constitutional admission path |
| ADB-023 | Ordinary Command claims bootstrap traffic or admission basis | Reject without entering the reserved bootstrap path or mutating either namespace |
| ADB-024 | Replay authoritative Organization history | Do not invoke admission resolution, authentication, governance, Command handling, or external effects |

## 14. Authority and Policy test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| AUT-001 | Actor uses active Grant exactly within action, Resource, risk, time, and jurisdiction scope | Authority gate passes; later gates determine admission |
| AUT-002 | Grant expired before bound evaluation time | Reject expired-authority; no Approval use, reservation, or dispatch |
| AUT-003 | Grant is revoked | Reject revoked-authority and preserve prior accountable history |
| AUT-004 | Grant effective time is after bound evaluation time | Reject future-authority |
| AUT-005 | Requested action or Resource exceeds Grant scope | Reject overbroad request; do not narrow silently into a different Command |
| AUT-006 | Delegation is shorter, narrower, lower-risk, within budget, and parent permits delegation | Accept delegation when every other gate passes and preserve derivation chain |
| AUT-007 | Delegation expands action, Resource, risk, duration, budget, or delegation right | Reject; no child Grant becomes active |
| AUT-008 | Valid technical Credential and reachable Tool but no Grant | Reject missing-authority |
| AUT-009 | Lower Policy narrows a higher permitted scope | Enforce lower narrowing rule and accept only within it |
| AUT-010 | Lower Policy attempts to override constitutional or higher prohibition | Reject attempted expansion and apply higher rule |
| AUT-011 | Policy evaluation is unknown, unavailable, or returns conflicting unverifiable versions | Fail closed or escalate; no fallback to cached permissive result |
| AUT-012 | Employee attempts to complete A4 or Constitution- or Policy-reserved A3 Decision | Reject and route to eligible Human without recording Employee as accountable decider |
| AUT-013 | Conflicting Grants apply | Enforce narrower or safer constraint until eligible Human resolution |
| AUT-014 | Role is active but no applicable Grant exists | Reject; Role eligibility is not authority |
| AUT-015 | A4 or Human-reserved A3 Decision names an AI Employee as accountable decider and attaches a separately eligible Human Approval; every other gate is valid | Reject or escalate; no dispatch, Resource reservation, Approval use, or Decision state implying valid Human disposition; record the invalid attribution and prove Approval did not convert the AI-authored Decision into a Human Decision |
| AUT-016 | AI Employee researches, recommends, proposes, routes, or prepares a Human-reserved Decision; eligible Human is accountable decider and every separate Approval and other gate is valid | Accept the Decision path only with roles distinctly attributable; the AI Employee remains proposer or technical participant, not accountable decider or approver by implication |

## 15. Work Root test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| WRT-001 | Task and Action reference one active Goal only | Work Root gate passes and trace persists through Events and audit |
| WRT-002 | Task and Action reference one complete current duty only | Gate passes with duty type, mandate, owner, scope, and completion/review condition preserved |
| WRT-003 | Task omits both Goal and duty | Reject missing-work-root; create no work entity |
| WRT-004 | Task supplies both Goal and duty | Reject dual-work-root; do not choose one silently |
| WRT-005 | Goal is suspended, completed, cancelled, or archived | Reject inactive-goal for new work |
| WRT-006 | Duty omits type, governing mandate, accountable owner, scope, or condition | Reject incomplete-duty |
| WRT-007 | Requested operation falls outside Goal or duty scope | Reject root-scope-mismatch |
| WRT-008 | Existing Task Command attempts to change immutable Work Root | Reject; require a new Task with full admission |
| WRT-009 | Task attaches directly to Goal or duty without Project, Objective, or Plan; optional planning references are absent | Accept when every other gate passes; no intermediate planning structure is required |
| WRT-010 | Project or Objective is supplied as the sole claimed Work Root, or optional Project/Objective/Plan references accompany a valid Goal or duty | Reject the sole Project/Objective root; accept optional structures only as subordinate organization of an otherwise valid exclusive Goal-or-duty Work Root |

## 16. Approval test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| APR-001 | Valid `single_use` Approval accompanies authorized execution | Approval use and admission Events append atomically; `used_count` becomes one before dispatch |
| APR-002 | New Command attempts reuse of consumed single-use Approval | Reject approval-exhausted; no reservation or dispatch |
| APR-003 | `bounded_repeat` at one below positive usage limit is used | Accept one use atomically; next use at limit rejects |
| APR-004 | Standing A2 Approval is current but Actor, Grant, Policy, budget, or condition changed | Revalidate every gate; reject on any failed current condition |
| APR-005 | Approval expired at bound evaluation time | Reject expired-approval |
| APR-006 | Approval revoked | Reject revoked-approval |
| APR-007 | Approval is valid but no Authority Grant covers operation | Reject missing-authority; Approval remains unchanged |
| APR-008 | Authority covers operation but Policy requires absent Approval | Reject missing-approval |
| APR-009 | Atomic append fails while single-use transition is prepared | No Event, `used_count`, reservation, projection, or dispatch changes |
| APR-010 | External outcome is uncertain after Approval use | Preserve monotonic `used_count`; enter reconciliation; never silently restore |
| APR-011 | Standing Approval is proposed for A4 or unspecified A3 activity | Reject invalid-approval-mode |
| APR-012 | Material evidence, cost, risk, scope, Policy, or Decision version changed | Invalidate Approval and require new review |
| APR-013 | Two Commands race for final bounded use | Exactly one ordered admission consumes use; other rejects without effect |
| APR-014 | Requester self-approves A3 without narrow permitted Policy | Reject separation-of-duties violation |

## 17. Resource-governance test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| RES-001 | All Resource dimensions are available | Availability is verified and reservation Events commit before dispatch |
| RES-002 | Append fails after reservation set is computed | Neither reservation nor admission becomes authoritative |
| RES-003 | Money is below required maximum exposure | Reject insufficient-money before dispatch |
| RES-004 | Money sufficient but compute insufficient | Reject insufficient-compute; do not reserve money alone |
| RES-005 | Compute sufficient but data-access scope exceeds classification or limit | Reject excessive-data-exposure |
| RES-006 | Related commitments span Tasks, Actions, Actors, vendor, or period | Aggregate before limit evaluation |
| RES-007 | Split transactions individually fit but aggregate exceeds limit | Reject evasion and open or link Incident when material |
| RES-008 | Verified evidence proves authorized dispatch never occurred | Release reservation through later Event; preserve original reservation history |
| RES-009 | Dispatch or external execution is uncertain | Keep safe reservation or Policy-defined bound and enter reconciliation; do not assume release |
| RES-010 | Resource stop threshold is reached | Prevent new affected use and suspend or escalate governed work |
| RES-011 | Actual use exceeds reservation | Record variance, stop affected work, and emit or link `BudgetExceeded`/Incident as applicable |
| RES-012 | Human-attention budget exhausted while money remains | Reject or pause independently; money cannot substitute |

## 18. Lifecycle test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| LIF-001 | Each entity performs every transition explicitly legal from its current fixture state | Accept only with required authority, Policy, Approval, evidence, and exact next state |
| LIF-002 | Each entity attempts at least one undefined transition | Reject illegal-transition; no target version change |
| LIF-003 | Task starts while assignee, Work Root, Grant, Tool, or Approval is inactive | Reject dependency-inactive |
| LIF-004 | Completion lacks acceptance or result evidence | Reject completion; retain active or prior state |
| LIF-005 | Suspended entity attempts operational transition | Reject except authorized containment/review path |
| LIF-006 | Restoration lacks Incident review or refreshed authority required by Policy | Reject restoration |
| LIF-007 | Temporary Worker reaches earliest expiry condition | Automatically prevent new work, revoke/suspend operational access, preserve identity |
| LIF-008 | Archived Temporary Worker identity is reused | Reject identity-reuse; historical references remain resolvable |
| LIF-009 | Material Artifact changes after Approval | Create new version and invalidate or require review; never mutate approved version |
| LIF-010 | Memory correction is submitted | Append linked correction/supersession; preserve prior Record and provenance |
| LIF-011 | Organization deletion requested while active | Reject; require lawful dissolution, retention, hold, and tombstone path |
| LIF-012 | Incident closes without independent-enough review or remediation evidence | Reject closure |

## 19. Scheduling and orchestration test suite

This suite tests governed schedule admission, persistence, due-trigger materialization, timeout, expiry, cancellation, and current-state revalidation. It MUST NOT treat scheduling strategy, organizational priority selection, sequence optimization, recurrence design, planning, or Task decomposition as kernel behavior.

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| SCH-001 | Admitted schedule becomes due | Materialize one new attributable Command with scheduler Service, schedule trigger, correlation, and audit references; due observation alone is not admitted work |
| SCH-002 | Schedule lacks Work Root for a new Task or Action | Reject materialization; create no work |
| SCH-003 | Schedule exists but current Grant is missing | Reject; schedule cannot supply authority |
| SCH-004 | Actor status, Role Assignment, Policy, Authority, Work Root, Approval, Resource, lifecycle, suspension, or stop condition changed after schedule creation | Re-evaluate every current gate at materialization; reject, pause, or constrain under current rules |
| SCH-005 | Referenced Approval expired before due evaluation time | Prevent scheduled dispatch and record rejection/pause |
| SCH-006 | Work Root, Task, Actor, or Tool is suspended | Do not dispatch; preserve schedule and suspension audit state |
| SCH-007 | Two legitimate recurrence instances become due | Give each distinct Command and instance identity while retaining series link |
| SCH-008 | Same schedule instance or due trigger is delivered twice | Idempotently materialize one Command and no duplicate dispatch; preserve original identifiers, positions, and evaluation time |
| SCH-009 | Schedule was missed while unavailable | Apply explicit catch-up Policy: skip, issue bounded catch-up, or escalate; never guess |
| SCH-010 | Schedule is cancelled before future trigger | Prevent future materialization and preserve cancellation Event |
| SCH-011 | Recurrence would exceed Task, Tool, Approval, or Resource bound | Stop before new instance and escalate or review |
| SCH-012 | Timer uses skewed external time | Use bound kernel evaluation time and record external time only as observation |
| SCH-013 | Kernel receives a valid schedule without an organizational priority or optimization choice | Preserve the admitted proposal; do not invent priorities, resequence work, alter recurrence, or choose a planning strategy |
| SCH-014 | Scheduler Service technically initiates a due Command | Preserve the Service as technical initiator and the schedule's attributable Actor, Decision, Work Root, and authority references; do not infer that the Service is planner, accountable decider, or authority source |
| SCH-015 | Distinct triggers conflict or race for one bounded instance | Deduplicate when they identify the same instance; otherwise pause or reconcile under the admitted conflict rule; never silently execute twice |

## 20. Tool invocation and reconciliation test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| TOL-001 | Valid admitted Tool request commits | Dispatch exactly once only after reservation, Approval use, and authorized-intent Events append |
| TOL-002 | Admission append fails | Dispatch count remains zero |
| TOL-003 | Adapter reports only attempt | Action becomes attempted, not verified or successful |
| TOL-004 | Adapter times out | Action becomes uncertain/reconciling; no assumed failure, success, retry, release, or restored Approval |
| TOL-005 | Adapter says success without required provenance or evidence | Reject verification; preserve assertion as unverified or disputed observation |
| TOL-006 | Same callback Command is delivered twice | One outcome transition; second returns original disposition |
| TOL-007 | Callbacks report contradictory results | Preserve both, mark dispute, reconcile, and open Incident when material |
| TOL-008 | Callback is initiated by unauthorized adapter identity | Reject without outcome transition or protected disclosure |
| TOL-009 | Adapter changes operation, inputs, Resource, or scope | Reject scope mismatch; adapter cannot broaden authorized request |
| TOL-010 | External system denies operation after valid kernel authorization | Record external denial as outcome; do not retroactively label original governance admission unauthorized |
| TOL-011 | External receipt and integrity proof verify effect | Admit verified outcome linked to attempt, evidence, Resources, and causal reference |
| TOL-012 | Reconciliation read is requested without authority | Reject; reconciliation itself requires governed Tool request |

## 21. Event ordering and idempotency test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| EVT-001 | Attempt to mutate an accepted Event | Reject or detect integrity failure; original Event remains unchanged |
| EVT-002 | Correct a prior Event assertion | Append later correction Event with links; never overwrite source |
| EVT-003 | Concurrent Commands target same expected version | Assign one order; accept valid winner and reject/re-evaluate stale loser |
| EVT-004 | Events share timestamps | Preserve stream-position order; timestamp never breaks tie |
| EVT-005 | Exact duplicate Event delivery reaches projection | Apply once by stable Event identity |
| EVT-006 | Event gap is observed | Stop ordered projection or expose gap; never skip or invent Event |
| EVT-007 | Event arrives out of organization order | Buffer/recover or reject application until preceding positions are verified |
| EVT-008 | Same idempotency key has different evaluation time but identical payload | Treat as conflicting retry unless it is exact redelivery returning original bound time |
| EVT-009 | Recording Command and external causal reference differ | Preserve both fields without treating admission as external cause |
| EVT-010 | Parameterized Event applicability cases: required field missing; prohibited field present; invented placeholder for irrelevant field; valid deterministic mechanical Event whose schema permits epistemic status or confidence not applicable; valid consequential Event with every material field | Reject the first three schema/applicability violations; accept the mechanical and consequential controls; compare every applicable field exactly without requiring ceremonial values |

## 22. Canonical relationship test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| REL-001 | Actor inverse Role list claims occupancy but no canonical Role Assignment exists | Reject eligibility and fail closed; the inverse list creates no Role occupancy |
| REL-002 | Authority inverse list changes issuer, recipient, or delegation edge absent from the canonical Authority Grant history | Reject authority and report integrity failure; only the canonical Grant and accepted Events control |
| REL-003 | Governing Body member list includes an Actor absent from canonical membership records or accepted Events | Exclude the Actor from quorum and disposition eligibility; reject affected collective outcome and report integrity failure |
| REL-004 | Derived inverse collection is directly edited while canonical relationship state is unchanged | Refuse the edit as authoritative mutation; rebuild or quarantine the derived projection without changing canonical state |
| REL-005 | Replay begins with canonical Role Assignment, Grant, and Governing Body membership history and no inverse indexes | Reconstruct the inverse collections exactly for navigation without emitting new authoritative Events |
| REL-006 | Two projections look equal but arise from conflicting canonical relationship histories | Fail projection-equivalence and conformance despite equal-looking inverse collections |
| REL-007 | Inverse collections are correctly rebuilt and match canonical state | Permit their use for navigation or efficient reads while proving every eligibility and authority decision resolves to canonical relationship state |

## 23. Subscription isolation test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| SUB-001 | Authorized Alpha subscriber matches permitted type and classification | Deliver Event with stable identity, stream position, schema, and authorized payload |
| SUB-002 | Subscriber lacks active Role, Grant, purpose, or subscription | Deliver nothing and audit attributable denial |
| SUB-003 | Alpha subscriber requests Beta Events | Deliver nothing and reveal no protected Beta metadata |
| SUB-004 | Internal-only subscriber matches restricted Event type | Enforce field/classification filter; no side-channel leakage |
| SUB-005 | Same Event is redelivered | Preserve Event identity and ordering; subscriber processes idempotently |
| SUB-006 | Delivery endpoint fails | Event remains accepted and immutable; record delivery failure without source mutation |
| SUB-007 | Subscriber attempts to edit, acknowledge away, or supersede source Event | Reject mutation; any state request requires new Command |
| SUB-008 | Projection replay occurs | Produce no new live delivery and do not masquerade historical application as Event acceptance |
| SUB-009 | Cursor recovers after gap | Resume from verified position without skip, invention, or unauthorized backfill |
| SUB-010 | Filter error would expose presence of classified Event | Fail closed without existence leak; record protected control failure |

## 24. Memory governance test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| MEM-001 | Admit valid Memory Record | Preserve creator, source, acquisition, times, transformations, evidence, Work Root/duty, classification, validity, confidence, and integrity |
| MEM-002 | Model produces output not submitted through memory admission | Output remains transient and absent from institutional projections |
| MEM-003 | Authorized retrieval has a narrow declared purpose | Return only purpose-relevant, valid, authorized fields and audit retrieval |
| MEM-004 | Actor lacks restricted classification access | Deny retrieval and avoid leaking Record existence or content |
| MEM-005 | Claim is superseded | Prefer current Claim in retrieval while preserving historical identity, content, provenance, and chain |
| MEM-006 | Claims contradict | Preserve both, mark dispute and evidence relationships, do not silently merge |
| MEM-007 | High confidence lacks supporting evidence | Do not promote validity, authority, or truth; consequential reliance fails evidence gate |
| MEM-008 | Deletion requested for Record under retention or legal hold | Reject or defer deletion and audit controlling obligation |
| MEM-009 | Authorized redaction is completed | Remove protected content as permitted; retain nonreconstructive tombstone, provenance minimum, Event and audit links |
| MEM-010 | Derived Record is admitted | Link every material input and transformation method |
| MEM-011 | Model citations omit retrievable source | Do not admit citation as Evidence; mark provenance gap |
| MEM-012 | Retrieval index conflicts with source lifecycle state | Source Event-derived state controls; fail index result closed and rebuild/reconcile |

## 25. Suspension, cancellation, timeout, retry, and escalation test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| OPS-001 | Incident triggers authorized emergency suspension | Immediately prevent new affected work, preserve evidence, notify accountable Human, and link Incident |
| OPS-002 | Suspension is used to request unrelated action | Reject scope expansion; containment confers no unrelated authority |
| OPS-003 | Cancellation occurs before dispatch | Prevent dispatch, release verified unused reservation by Event, and preserve cancellation audit |
| OPS-004 | Cancellation occurs after dispatch | Stop future work but retain uncertain/in-flight effect and require reconciliation or compensation |
| OPS-005 | Timeout occurs with no external result | Record uncertainty, not failure or success; retain safe reservation and Approval use |
| OPS-006 | Retry has proof prior attempt could not effect | Admit new Command only after all current gates and new reservation pass |
| OPS-007 | Retry lacks nonexecution proof or external idempotency | Reject or require consequential Decision and Approval for duplicate-effect risk |
| OPS-008 | Retry limit or stop condition reached | Reject further retry and escalate under Policy |
| OPS-009 | Reconciliation confirms partial effect | Record partial result, actual Resources, follow-up Decision, and compensation path |
| OPS-010 | Governance state is unknown or conflicting | Pause or escalate with safe default; nonresponse grants nothing |
| OPS-011 | Restoration requested after suspension without remediation | Reject until eligible review, refreshed Grants, and constraints are recorded |
| OPS-012 | Sponsor is suspended while worker has pending work | Prevent worker's new activity and preserve accountable handoff/review state |

## 26. Audit and consequential Decision test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| AUD-001 | Complete consequential operation is reconstructed | Trace exactly one recording Command through all required Decision, authority, work, Tool, Resource, outcome, and audit links |
| AUD-002 | External observation was admitted by a recording Command | Preserve distinct `recording_command_id` and `causal_reference`; never assert Command caused external fact |
| AUD-003 | Consequential Action audit contains one Work Root | Resolve exactly one Goal or duty and reject both/neither forms |
| AUD-004 | Initiator submits Decision made by another eligible Actor | Preserve both identities and never promote initiator to decider |
| AUD-005 | Tool was attempted and later verified | Preserve separate attempt and verified outcome Events and evidence |
| AUD-006 | Decision has supporting and material contradictory evidence | Pin exact identifiers and versions available at decision time |
| AUD-007 | Governing Body makes collective Decision | Require real eligible Human members; preserve each attributable vote, dissent, consent, or recusal; verify current quorum and voting Policy; deterministically derive the body result; use no fictional Human and do not treat technical initiator as accountable decider |
| AUD-008 | Protected evidence content is restricted | Use controlled stable reference while preserving provenance, integrity, authority, and accountability |
| AUD-009 | Completion Command omits mandatory Decision or audit linkage | Reject completion; do not invent or defer linkage silently |
| AUD-010 | Lessons or result metrics are pending at decision time | Preserve explicit pending state and require follow-up condition rather than omission |
| AUD-011 | Audit builder reports success but linked Event history is corrupt | Fail audit/recovery closed; equal-looking trace does not pass |
| AUD-012 | Human-reserved Approval is collective | Verify individual authority, quorum, dispositions, and separation of duties before execution |
| AUD-013 | Decision is `governance_conditions_satisfied` but its Authority Grant expired before Action evaluation | Re-evaluate current Authority and reject or pause; Decision state and completed Approval processing do not create execution eligibility |
| AUD-014 | Decision is linked to an `executed` Action whose external result is uncertain or failed | Preserve attempt separately from uncertain or failed outcome; do not infer verified success from the Decision or `executed` state |
| AUD-015 | Previously approved Decision has materially changed Policy, evidence, risk, scope, or Resource conditions before Action | Revalidate and reject, pause, invalidate, or require new Decision/Approval as applicable; never execute automatically from prior lifecycle state |

## 27. Replay and recovery test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| RPL-001 | Replay the same complete Event sequence twice | Produce projection-equivalent outputs with identical normative state and references |
| RPL-002 | Historical stream contains Tool requests | Replay issues zero Tool or adapter calls |
| RPL-003 | Historical stream contains external communications | Replay sends zero messages, webhooks, notifications, or human requests |
| RPL-004 | Historical stream contains charges and Resource use | Replay creates zero real charges or consumption; rebuild accounting projection only |
| RPL-005 | Historical stream contains Approval uses | Replay creates no new use; rebuild historical `used_count` only |
| RPL-006 | Replay completes | Create no new authoritative Command, Event, schedule, subscriber delivery, or audit fact |
| RPL-007 | External opaque-system references exist | Reconstruct references, observations, versions, integrity, ownership, classification, provenance, and reconciliation status only |
| RPL-008 | Event history is corrupt, missing, duplicated incompatibly, or unknown-schema | Stop at exact position and fail recovery safely; do not guess through gap |
| RPL-009 | Checkpoint position or integrity mismatches Event stream | Discard and fully verify/rebuild or fail closed |
| RPL-010 | Live adapter accidentally attached during replay | Effect guard blocks invocation and emits no authoritative replay Event; conformance run records critical failure attempt |
| RPL-011 | Replay uses current wall clock rather than historical Event values | Test detects divergent expiry/state and fails conformance |
| RPL-012 | Projection matches expected state but source Event order differs | Fail history validation despite equal-looking projection |
| RPL-013 | Stream contains later redaction, deletion, sealing, restriction, or tombstone Events | Reconstruct the governed availability state and minimum lawful accountability metadata; expose no removed or restricted content |
| RPL-014 | Earlier Event references content later cryptographically erased | Preserve stable reference, Event identity, position, provenance minimum, and tombstone/erasure state; do not reproduce, retrieve, or infer erased content |
| RPL-015 | Historical Event referenced classified content under authority valid at that time | Do not treat the reference as current retrieval authority; enforce current governed availability and disclosure controls while retaining accountable metadata |

## 28. Portability and model-replacement test suite

| ID | Scenario and distinguishing input | Required observable result |
|---|---|---|
| POR-001 | Export and import Organization Event history and governed references into a clean conforming environment | Rebuild projection-equivalent state with stable identity and audit semantics |
| POR-002 | Export omits provenance, Policy version, Grant chain, or audit relationship | Reject portability claim as incomplete |
| POR-003 | Replace model implementing active Employee | Preserve Employee Actor, Role, Grants, Tasks, Work Roots, memory, budgets, and audit continuity |
| POR-004 | Replacement model claims a new identity or inherited authority | Reject; model is a Resource and cannot hold or transfer institutional authority |
| POR-005 | Model context contains unadmitted facts after replacement | Facts do not enter institutional memory or govern admission |
| POR-006 | Specialized projection or search service is replaced | Rebuild from Events; no alternate Policy, memory, authority, or lifecycle truth persists |
| POR-007 | External opaque system is unavailable after migration | Preserve governed references and unresolved reconciliation; do not fabricate domain state |
| POR-008 | Import changes serialization but preserves canonical semantics | Accept semantic equivalence when order, identities, versions, and integrity mapping remain exact |

## 29. Required evidence from a conforming test run

A conformance run MUST produce a versioned, integrity-verifiable evidence package containing:

- IUT release identity, configuration digest, enabled kernel boundaries, and declared specialized services;
- AIOS constitutional and specification versions and exact test-specification revision;
- document-conformance mapping for every normative kernel interface and responsibility;
- canonical fixture manifest, stable identifier mapping, initial Event streams, projections, Policy versions, and external-reference manifest;
- complete normative test-case records for every mandatory scenario and explicit inapplicability decision;
- submitted Commands and bound evaluation times;
- accepted and rejected Events in canonical semantic form and stable order;
- before/after authoritative projection exports and equivalence results;
- Resource reservations, consumption, releases, aggregation, and stop-condition evidence;
- Approval-use before/after evidence and concurrency results;
- adapter dispatch, external write, communication, charge, notification, and subscription-delivery counters;
- replay effect-guard evidence proving zero effects rather than absence of success logs;
- fault-injection point, timing, observed failure, safe outcome, and recovery evidence;
- audit reconstruction for every consequential scenario;
- deterministic-repeat and idempotent-redelivery comparisons;
- all deviations, failures, retries of the test itself, and unresolved observations; and
- attributable tester and independent reviewer dispositions with timestamps and integrity references.

Evidence MAY redact protected content only when stable protected references, classification, integrity, provenance, and authorized review remain sufficient to establish the tested claim.

## 30. Conditions invalidating conformance

A claimed conformance result is invalid if:

- any mandatory scenario is omitted, silently retried until passing, weakened, or marked inapplicable without documented independent approval;
- fixtures, expected results, bound times, Policy versions, or Event streams differ across compared runs without being declared distinct inputs;
- the harness or IUT uses ambient credentials, hidden state, uncontrolled current time, unrecorded external observations, or model context to satisfy a gate;
- Event comparison ignores a normative field or order, or projection comparison omits source-history validation;
- a replay test has access to live effects without an effective, observed guard;
- negative-effect evidence relies only on missing success logs rather than instrumented boundaries;
- unavailable identity, Authority, Policy, classification, Resource, audit, or integrity services are treated as permission;
- an Approval or Resource mutation occurs before or outside the atomic admission append;
- a Tool attempt, acknowledgement, timeout, cost, or unsupported assertion is accepted as verified success;
- cross-Organization or classification leakage occurs, even if the intended test outcome otherwise passes;
- a model, Tool, adapter, Credential, scheduler, or service acts as an institutional Actor or authority source;
- test-only backdoors directly mutate authoritative projections or bypass normal Command admission;
- permitted implementation metadata changes normative semantics or hides nondeterminism;
- test evidence cannot be reproduced, integrity-verified, or independently reviewed; or
- the IUT, fixture, or specifications changed after the run without a complete new conformance run.

Conformance is a property of the named IUT release, configuration, specification set, and evidence package. It is not transferable by similarity, vendor assertion, shared components, or partial test success.
