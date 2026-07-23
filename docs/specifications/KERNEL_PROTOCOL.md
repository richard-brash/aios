# AIOS Kernel Logical Protocol

**Specification version:** 0.0.2
**Protocol family version:** 1.0
**Status:** Normative logical contract

## 1. Purpose, scope, and principles

This document defines the canonical logical records exchanged at AIOS kernel boundaries. It specifies meaning, trust, versioning, presence, state distinctions, and observable outcomes. It does not prescribe an encoding, serialization, transport, programming language, storage system, message broker, deployment platform, or model provider. The record examples are symbolic field maps, not a required wire format.

This protocol refines [`ENTITY_MODEL.md`](ENTITY_MODEL.md), [`EVENT_MODEL.md`](EVENT_MODEL.md), [`LIFECYCLES.md`](LIFECYCLES.md), [`INVARIANTS.md`](INVARIANTS.md), [`DECISION_RECORD.md`](DECISION_RECORD.md), [`ARCHITECTURE_PRINCIPLES.md`](ARCHITECTURE_PRINCIPLES.md), [`KERNEL_CONTRACT.md`](KERNEL_CONTRACT.md), and [`KERNEL_CONFORMANCE.md`](KERNEL_CONFORMANCE.md). Those documents and the Constitution control on conflict.

Every conforming boundary MUST preserve these principles:

- every message has one stable `message_id`, stable `message_type`, and explicit version;
- every authoritative mutation is attributable to exactly one `recording_command_id`;
- recording provenance and real-world causality are separate;
- every message identifies exactly one Organization except an explicitly pre-Organization bootstrap request or non-authoritative platform-security message;
- presence states are explicit and never collapsed into an ambiguous generic null;
- caller assertions are untrusted until the kernel resolves and validates them;
- the kernel alone supplies authoritative `evaluation_time`, `stream_id`, and `stream_position`;
- acceptance, dispatch, attempt, observation, interpretation, reconciliation, and verified outcome are distinct;
- Approval is not Authority; reservation is not consumption; schedule definition is not instance materialization;
- replay traffic is mechanically distinguishable from live traffic and cannot produce live dispatch;
- duplicate delivery preserves original identity, and conflicting identity or idempotency reuse fails closed;
- every failure uses a stable machine-comparable reason code plus bounded safe detail; and
- protected content may use governed references, but attribution, provenance, integrity, classification, and audit accountability remain.

### 1.1 Protocol families

The protocol defines 20 top-level families. Subtypes within a family retain the family version and add their own record version.

| ID | Protocol family | Primary records |
|---|---|---|
| PF-01 | Command submission | `CommandSubmission` |
| PF-02 | Admission disposition | `AdmissionAccepted`, `AdmissionRejected`, `AdmissionPreviouslyAdmitted`, `AdmissionPaused`, `AdmissionEscalated` |
| PF-03 | Event record | `EventRecord` and correction, supersession, redaction, tombstone links |
| PF-04 | Event append | `AppendProposal`, `AppendCommitted`, `AppendConflict`, `AppendRejected`, `AppendUncertain` |
| PF-05 | Projection | `ProjectionQuery`, `ProjectionResponse`, `ProjectionFailure` |
| PF-06 | Replay | `ReplayRequest`, `ReplayAuthorization`, `ReplayReport`, `ProjectionComparison` |
| PF-07 | Subscription | request, authorization, delivery, acknowledgment, rejection, suspension, checkpoint |
| PF-08 | Scheduling | definition, activation, suspension, cancellation, due observation, instance materialization, missed/catch-up disposition |
| PF-09 | Tool dispatch | authorized dispatch intent, adapter receipt |
| PF-10 | Tool attempt | execution-attempt report |
| PF-11 | Tool result | external response observation, adapter interpretation, verified outcome |
| PF-12 | Reconciliation | request, evidence set, disposition |
| PF-13 | Resource | estimate, reservation, consumption, release, adjustment, limit and stop records |
| PF-14 | Approval use | reference snapshot, per-use validation, monotonic usage record |
| PF-15 | Memory | Evidence, Claim, admission, retrieval, disclosure, conflict, supersession, redaction, deletion, hold, tombstone |
| PF-16 | Audit | `AuditReference`, protected reference, trace-completeness result |
| PF-17 | Bootstrap | pre-Organization request and atomic outcome |
| PF-18 | Operational control | suspension, cancellation, timeout, retry, escalation |
| PF-19 | Version negotiation | offer, selection, rejection, migration evidence |
| PF-20 | Failure | stable reason-code record and safe detail |

## 2. Presence semantics

Every logical field has exactly one presence state. An implementation may encode these states differently but MUST preserve their distinct meaning in validation, projection, replay, audit, and disclosure.

| Presence state | Meaning | Required behavior |
|---|---|---|
| `known(value)` | Value is present and asserted or authoritative according to field trust | Validate type, source, scope, and integrity |
| `unknown` | Value should exist but is not known | MUST NOT be treated as empty, false, zero, valid, or not applicable |
| `not_yet_known` | Value is expected only after a later boundary or observation | Preserve pending state and required follow-up |
| `not_applicable` | Field has no meaning for this record subtype | Validator confirms inapplicability; caller cannot use it to avoid a required value |
| `intentionally_empty` | Applicable collection was evaluated and contains no entries | Preserve explicit empty meaning and evaluation basis |
| `withheld(classification, reference)` | Value exists but disclosure is not authorized | Preserve governed reference, classification, and accountable withholding basis |
| `redacted(tombstone_reference)` | Previously recorded value was lawfully removed or obscured | Preserve nonreconstructive tombstone and audit linkage |
| `externally_unavailable(reference)` | External source could not provide the value | Preserve external reference, failure observation, and reconciliation requirement |
| `conflicted(evidence_references)` | Material contradictory values remain unresolved | Preserve every claim and evidence relationship; do not select silently |

Omission is permitted only when the record contract marks a field prohibited or the presence state is represented separately and unambiguously. A generic null without a preserved presence state is nonconforming.

## 3. Common logical envelope

### 3.1 Trust roles

- **Caller-supplied:** asserted by the initiating boundary; untrusted until validated.
- **Kernel-bound:** supplied only by the kernel at admission or append; a caller value is prohibited or ignored and recorded as a validation failure.
- **Kernel-validated:** caller may assert it, but the kernel resolves the authoritative referenced version and may reject; it never silently replaces the assertion with a broader value.
- **Derived:** computed deterministically from admitted facts and named versions.
- **Adapter-observed:** reported as an observation with provenance; never authoritative organizational success by itself.

Payload data MUST NOT override envelope attribution, Organization, evaluation time, ordering, classification, authority, Approval, Work Root, or audit fields. Duplicate trusted fields in a payload make the message structurally invalid unless the record type explicitly defines them as nonauthoritative echoes and requires equality.

### 3.2 Envelope field contract

Applicability abbreviations are `CMD` Command, `DSP` disposition, `EVT` Event, `APP` append, `PRJ` projection, `RPL` replay, `SUB` subscription/schedule, `TLR` Tool/reconciliation, `RES` Resource/Approval, `MEM` memory/audit, `BTS` bootstrap, `OPS` operational control, and `VER` version/failure. Cells use the words `required`, `conditional`, and `prohibited`; unlisted families permit a field only when their subtype explicitly requires it.

| Field | Meaning | Supplier and validation | Applicability | Mutability and replay | Security significance |
|---|---|---|---|---|---|
| `message_id` | Globally stable identity of this logical message | Caller for request; kernel for kernel result; uniqueness validated | required: all | Immutable; historical records preserve identity; replay-control/report messages use distinct replay-mode identities and never live operational identities | Deduplication and forgery boundary |
| `message_type` | Stable unambiguous type name | Record producer; validated against selected family/type version | required: all | Immutable; historical interpretation uses recorded version | Prevents type confusion |
| `schema_version` | Logical record-type schema version | Producer; negotiation and validator constrain | required: all | Immutable; replay uses historical semantics | Prevents downgrade/reinterpretation |
| `organization_id` | Sole Organization scope | Caller assertion then kernel validation; kernel result copies validated value | required: all except pre-org BTS/platform security | Immutable; replay preserves | Primary tenancy and authority boundary |
| `initiating_actor_id` | One technical initiating Actor | Caller assertion plus invocation proof; kernel resolves | required: CMD, OPS; conditional: others; pre-org BTS resolves verified Human within transaction | Immutable; replay preserves | Attribution; not automatically decider |
| `participant_actor_ids` | Other attributable participants | Caller asserts; kernel validates each | conditional: CMD, DSP, EVT, MEM, OPS | Immutable per message; replay preserves | Collective accountability, no authority aggregation |
| `recording_command_id` | Command through which authoritative mutation was admitted | Kernel binds Events/mutations to admitted Command; caller may reference for result reports | required: EVT, APP and authoritative RES, MEM, OPS; conditional: TLR; prohibited: initial CMD | Immutable; replay preserves | Mutation provenance, distinct from cause |
| `causal_reference` | Typed cause/trigger of underlying occurrence | Caller or adapter asserts with evidence; kernel validates type/provenance | conditional: all operational families | Immutable assertion; corrections append | Prevents recording/cause conflation |
| `correlation_id` | End-to-end governed case or operation group | Caller supplies or kernel binds at bootstrap/system origin | required: CMD, DSP, EVT, TLR, SUB, OPS; conditional: others | Immutable; replay preserves | Must not authorize cross-org correlation access |
| `causation_message_id` | Immediately preceding protocol message in message-flow lineage | Producer supplies; kernel validates existence and Organization | conditional: all | Immutable; replay preserves | Flow lineage, not real-world causal proof |
| `idempotency_key` | Organization-scoped operation deduplication key | Caller supplies for mutating request; kernel scopes and compares full operation | required: CMD, BTS, materialization, retry; conditional: others | Immutable; replay does not reacquire | Cross-org isolation; conflict fails closed |
| `issued_at` | Producer-asserted issue time | Producer; kernel treats as observation, not authoritative evaluation | required: requests; conditional: reports | Immutable; replay preserves | Cannot determine authority expiry alone |
| `evaluation_time` | Single authoritative admission time | Kernel-bound only | required: DSP, EVT, APP and admitted mutations; prohibited: caller requests | Immutable; replay uses recorded value | Prevents clock manipulation and nondeterminism |
| `received_at` | Boundary-observed receipt time | Receiving boundary records as observation | conditional: all | Immutable observation; not ordering authority | Latency/audit only; external skew tolerated |
| `stream_id` | Organization authoritative Event stream | Kernel-bound | required: EVT, APP; conditional: PRJ, RPL, SUB deliveries; prohibited: caller-chosen values | Immutable; replay selects recorded stream | Prevents stream injection |
| `stream_position` | Kernel-assigned Event order | Kernel-bound | required: accepted EVT/deliveries; conditional: PRJ, RPL; prohibited: proposals/caller values | Immutable; replay preserves | Sole organization order authority |
| `expected_stream_position` | Caller/preparer concurrency precondition | Caller or kernel append planner asserts; kernel compares current | required: APP; conditional: CMD, PRJ | Immutable input; replay applies historical outcome | Prevents lost update |
| `classification` | Message/payload disclosure class | Caller asserts minimum; kernel validates and may raise, never lower without authority | required: all except negotiation; conditional: VER | Immutable for record; later reclassification Event | Disclosure and filter boundary |
| `purpose` | Specific authorized processing purpose | Caller asserts; kernel validates against Role, Grant, Policy, subscription | required: requests/retrieval/subscription; conditional: results | Immutable; replay preserves | Purpose limitation |
| `work_root` | Exactly one Goal or complete duty for Task/Action | Caller asserts; kernel validates exclusive form and current scope | required: work-related CMD, TLR, SUB, RES, OPS and consequential MEM; conditional: otherwise | Immutable for Task/Action; replay preserves | Prevents unrooted or dual-root work |
| `authority_references` | Asserted relevant Grants and chain | Caller asserts; kernel resolves current validity and scope | required: consequential CMD, TLR, RES, OPS; conditional: others | Immutable snapshot references; replay historical | Presence never proves authority |
| `policy_references` | Versions used or asserted | Caller may assert; kernel pins controlling versions | required: DSP, EVT, APP, audit; conditional: requests | Immutable once admitted; replay historical | Prevents silent current-policy reinterpretation |
| `decision_reference` | Consequential Decision and version | Caller asserts; kernel validates completeness/current applicability | required: consequential operations; conditional: others | Immutable reference; material change new Decision | Cannot be invented by kernel |
| `approval_references` | Approval IDs/versions/modes used | Caller asserts; kernel validates and records use | required: when Policy requires; conditional: others | Immutable per use; replay rebuilds monotonic usage | Approval never Authority |
| `resource_references` | Resources affected or measured | Caller/adapter asserts; kernel validates scope and state | required: consequential CMD, TLR, RES, EVT; conditional: others | Immutable facts; corrections append | Reservation separate from consumption |
| `audit_reference` | Stable audit record/segment link | Kernel derives or validates protected reference | required: authoritative consequential result; conditional: others | Immutable linkage; replay rebuilds | Missing link blocks completion |
| `payload_type` | Stable payload semantic type | Producer; validated under record type | required: payload-bearing messages | Immutable; replay historical | Blocks ambiguous payload interpretation |
| `payload_version` | Payload schema version | Producer; negotiated/validated | required: payload-bearing messages | Immutable; replay historical | Blocks schema downgrade |
| `payload` | Type-specific logical fields | Producer according to trust rules; kernel validates | conditional: all | Immutable message content; correction new message/Event | Cannot override trusted envelope |
| `integrity_reference` | Integrity proof or protected digest reference | Producer supplies; receiving authority verifies | required: EVT, APP, audit, Tool evidence, checkpoints; conditional: others | Immutable; replay verifies | Tamper evidence, not semantic authority |
| `redaction_metadata` | Withholding/redaction basis and tombstone references | Authorized governance boundary only | conditional: protected DSP, EVT, PRJ, SUB, MEM | Append-only changes; replay applies historical Events | Must not leak or erase accountability |

### 3.3 Family applicability rules

Every record definition below narrows this common table. A field is REQUIRED only when marked by the common table or subtype. Irrelevant fields MUST be `not_applicable` or absent under an unambiguous schema prohibition; they MUST NOT carry hidden meaning. Pre-Organization bootstrap uses `organization_id=not_yet_known` plus a proposed Organization identity in its payload. Platform-security telemetry is explicitly non-authoritative, uses a platform scope rather than an Organization stream, and MUST NOT be accepted as an AIOS Event.

## 4. Versioning and negotiation

Every message records:

- protocol-family version;
- record-type `schema_version`;
- `payload_version` where payload exists;
- controlling Policy version references when evaluated;
- governing specification version references; and
- migration-evidence reference if transformed.

A backward-compatible addition is optional, has an explicit presence default that cannot change existing meaning, and does not change acceptance, authority, ordering, disclosure, or lifecycle semantics for an older reader. Removing, renaming, retyping, changing requiredness, changing presence meaning, reinterpreting an enum/reason code, or changing a normative outcome is breaking and requires a new major family or record version.

`VersionOffer` lists supported family, record, and payload ranges plus specification versions. `VersionSelection` chooses one mutually supported set. `VersionRejected` uses `VER.UNSUPPORTED` or `VER.DOWNGRADE_REJECTED`. Unknown major versions fail closed. Unknown optional fields may be retained opaquely only when the selected schema explicitly permits them and proves they cannot affect normative meaning.

Standalone version negotiation is scoped to exactly one Organization and authenticated boundary. Pre-Organization negotiation is permitted only as a bounded component of `BootstrapRequest`; its selection applies only to that bootstrap transaction and creates no operational Organization or authority.

Historical Events and replay use the schema, Policy, transition rules, and specification meanings recorded for that history. Migration creates attributable evidence mapping old semantics to new projections; it MUST NOT silently reinterpret an old Event under current schemas.

## 5. Command submission family

`CommandSubmission` is an immutable request, never proof of permission or occurrence. In addition to the envelope, its payload contains:

| Field | Contract |
|---|---|
| `command_id` | Stable identity of this Command operation. Exact redelivery preserves both `command_id` and `message_id`; a permitted retry uses a new `command_id` and preserves `original_operation_id` and correlation |
| `original_operation_id` | Stable lineage identity shared by an original operation and its separately admitted retries; prohibited from merging different requested semantics |
| `operation_type` and `operation_version` | Exact requested operation; no free-text operation key |
| `target_references` | Typed entity/Resource targets and expected versions |
| `invocation_proof_reference` | Proof bound to asserted initiating Actor; not a Credential value |
| `work_root` | Exactly one Goal or duty for every Task/Action, both/neither structurally invalid |
| `asserted_authority_references` | Untrusted Grant/delegation references until kernel resolution |
| `decision_reference`, `approval_references` | Exact versions asserted for consequential/approval-gated work |
| `expected_resource_use` | Estimate per independently governed dimension |
| `reservation_request` | Maximum exposure, units, aggregation keys, and release conditions |
| `lifecycle_preconditions` | Expected entity versions, states, dependencies, and requested transition |
| `risk` and `reversibility` | Classification, restoration plan/reference, verification, window, uncertainty |
| `evidence_references` | Pinned supporting and contradictory Evidence versions |
| `result_criteria` | Typed criteria required before verified completion |
| `stop_conditions` | Budget, time, Incident, safety, evidence, and external conditions |
| `tool_request` | Tool, operation, exact bounded inputs/protected references, and result contract when applicable |

The caller may assert references only. The kernel resolves Organization, identity, Role, Grants, Policies, Work Root, Decision, Approvals, Resources, lifecycle, evidence access, and current versions. It MUST reject rather than replace an invalid assertion with a broader or different one.

## 6. Admission disposition family

All dispositions contain the original `command_id`, bound `evaluation_time`, reason-code presence, and audit reference when a valid Organization recording boundary exists.

| Disposition | Required fields | Meaning and prohibited implication |
|---|---|---|
| `accepted` | Event IDs/bindings, assigned positions, derived target versions, committed reservations, Approval-use transition, exact authorized next step | Authorizes only the recorded next step; does not imply adapter receipt, attempt, external effect, verification, success, or lifecycle completion |
| `rejected` | Stable reason code, failed gate, safe detail, Policy/invariant references, explicit zero mutation/effect assertions | Confers no authority; does not imply malicious intent or external nonoccurrence |
| `previously_admitted` | Original disposition identity, Event identities/positions, original evaluation time, idempotency match proof | Is not a new acceptance and MUST NOT repeat Event, use, reservation, schedule instance, dispatch, or delivery |
| `paused` | Unresolved state, safe holding state, owner, timeout/review condition, zero implied success | Does not authorize later automatic continuation without a newly admitted Command or defined current-state revalidation |
| `escalated` | Exact question/Decision sought, eligible Actor/Role, evidence, deadline, safe default | Nonresponse is not Approval or Authority |

## 7. Event record family

`EventRecord` is immutable and contains every field required by `EVENT_MODEL.md`, including Event identity/type/version, Organization stream/position, kernel acceptance time, initiating/participating Actors, `recording_command_id`, distinct `causal_reference`, correlation, Resources, typed result, Evidence, epistemic status, conditional confidence, entity references/versions, projection effects, Approval-use effects, audit and integrity linkage.

The Event `timestamp` is the kernel-recorded acceptance/occurrence-in-AIOS time and controls authoritative ordering only through its assigned stream position. A real-world `occurred_at`, `observed_at`, adapter time, or external-system time is a payload observation with source and uncertainty; it never replaces `timestamp`, `evaluation_time`, or `stream_position`.

`epistemic_status` is one of `deterministic`, `observed`, `asserted`, `inferred`, `predicted`, or `disputed`. Confidence is prohibited or `not_applicable` for deterministic transitions and required for inferred, predicted, uncertain observed, and disputed assertions.

Projection effects are declarative semantic effects, not executable code. Resource and Approval effects use their dedicated record semantics. Event payload fields cannot override envelope identity, attribution, Organization, order, time, Work Root, authority, Policy, or classification.

Corrections, supersession, redaction, and tombstone records reference the original Event/record, reason, authorizing Decision, effective scope, and later Event. They never mutate or reorder the original.

## 8. Event append family

`AppendProposal` is an internal logical proposal, not yet authoritative, containing:

- one Organization `stream_id` and `expected_stream_position`;
- an ordered nonempty set of proposed Event semantics without caller-chosen final positions;
- projection version/state preconditions;
- Resource reservation transitions;
- Approval-use transitions;
- authorized Tool/subscription/schedule dispatch intents;
- complete audit references; and
- one recording Command and bound evaluation time shared as required.

| Outcome | Semantics |
|---|---|
| `AppendCommitted` | Entire set assigned consecutive positions and made authoritative atomically; committed reservation/use/intent identities returned |
| `AppendConflict` | Current position/precondition differs; nothing appended or mutated; reevaluation required |
| `AppendRejected` | Validation/invariant/integrity failure; nothing appended, dispatched, reserved, consumed, or delivered |
| `AppendUncertain` | Boundary cannot prove committed or noncommitted state; no retry, release, second use, or dispatch is allowed until reconciliation by idempotency and stream inspection |

Storage uncertainty MUST NOT be represented as success or confirmed nonappend. Reconciliation returns the original `AppendCommitted` identity if found, confirmed `AppendRejected`/nonappend evidence if absent under an authoritative check, or remains uncertain and escalates.

## 9. Projection family

`ProjectionQuery` identifies Organization, projection type/version, subject, purpose, authorization, classification ceiling, requested Event position, and consistency requirement. Callers cannot request a projection that ignores later revocation/suspension for an operational decision.

`ProjectionResponse` contains source `stream_id`, last applied position, Event-history integrity reference, projection version, normative state, governed external references and reconciliation status, presence/redaction semantics, and access audit reference. `ProjectionFailure` returns a stable code for gap, unknown schema, integrity mismatch, stale state, unavailable dependency, or classification denial.

A response is not authoritative independently of its validated source history. External domain content is referenced, not fabricated or claimed reconstructed.

## 10. Replay family

`ReplayRequest` contains authorized Organization, source stream range, historical specification/schema/Policy versions, projection versions, checkpoint references, expected integrity, and `execution_mode=replay_effect_prohibited`. `ReplayAuthorization` binds requester, purpose, classification, range, side-effect guards, and permitted output.

Every replay-family message includes `traffic_mode=replay`. A record with `traffic_mode=replay` is structurally prohibited from containing a live dispatch intent, live subscription delivery, Resource mutation request, Approval-use request, schedule materialization, external write, notification, charge, retry, or compensation.

`ReplayReport` contains applied range, Event count and integrity result, checkpoint decision, reconstructed projections/references, unknown historical version failures, external-reference limitations, side-effect counter proof, and zero new authoritative Command/Event identities. `ProjectionComparison` reports semantic equivalence, permitted metadata differences, and exact divergence position.

## 11. Subscription family

`SubscriptionRequest` contains stable subscription identity, subscriber Actor/Service and invocation proof, one Organization, Event-type/subject scope, classification ceiling, purpose, filter type/version, starting cursor, delivery constraints, expiry/review, and Grant/Policy references.

Authorization produces exact scope or rejection; the kernel MUST NOT broaden a filter. `SubscriptionDelivery` contains a stable delivery identity, original Event identity and position, subscription/filter versions, redaction/classification decision, delivery attempt number, and replay/live mode. Delivery order is transport observation and does not create Event authority; source position controls. Redelivery increments attempt count but preserves Event and delivery-operation identity and creates no new Event.

Acknowledgment records delivery identity, subscriber identity, received Event identity/position, disposition, and checkpoint proposal. Rejection/suspension identifies reason and safe cursor. `CursorCheckpoint` is attributable, monotonic within the subscription, and cannot skip an unacknowledged gap without explicit Policy. Subscribers cannot mutate source Events.

## 12. Scheduling family

Distinct record types are:

- `ScheduleDefinition`: stable series identity, authorizing Actor/Decision, Work Root or governed lifecycle subject, recurrence/trigger semantics, bounds, Resources, Approval, target, catch-up Policy, cancellation and review conditions;
- `ScheduleActivated`, `ScheduleSuspended`, and `ScheduleCancelled`: lifecycle transition with recording Command, current gates, reason, and effective time;
- `ScheduleDueObserved`: timer/deadline observation with source and bound kernel evaluation time, not permission;
- `ScheduleInstanceMaterialization`: distinct stable instance/operation identity, series identity, due identity, new attributable Command, current Work Root and every revalidated gate;
- `MissedInstanceDisposition`: `skipped`, `paused`, `escalated`, or `catch_up_proposed`, never guessed execution; and
- `CatchUpDisposition`: bounded authorized instances and current Decision/Approval/Resource checks.

Each legitimate instance has a distinct identity. Duplicate delivery for the same instance preserves its identity. A schedule definition cannot provide missing Authority, Approval, Work Root, Policy, Resource, or active lifecycle state.

## 13. Tool dispatch, attempt, and result families

The Tool boundary uses seven distinct knowledge records:

| Stage | Required logical record and semantics |
|---|---|
| 1 | `AuthorizedToolDispatchIntent`: original Command, dispatch ID, adapter/Tool/operation, exact authorized scope, Work Root/Task, reservations, Approval use, deadline, request integrity, result contract; committed before live dispatch |
| 2 | `AdapterReceipt`: dispatch ID, adapter identity/proof, receipt observation time, accepted/rejected-for-execution status; no external attempt or success implication |
| 3 | `ToolExecutionAttempt`: attempt ID, dispatch ID, adapter/Tool identity, exact operation/scope, attempt observation time, external operation ID if known, request integrity, Resource measurements, uncertainty |
| 4 | `ExternalResponseObservation`: attempt/external IDs, raw protected response reference, response integrity, observed time, source, Resources, epistemic status, uncertainty and contradictory Evidence |
| 5 | `AdapterInterpretation`: adapter assertion mapping response to typed result criteria, confidence/evidence, limitations; never organizational verification |
| 6 | `ReconciliationDisposition`: kernel-admitted `verified`, `failed`, `partial`, `duplicated`, `compensated`, `disputed`, or `unresolved`, with evidence and Resource/Approval implications |
| 7 | `VerifiedOutcome`: Decision/Policy-valid result criteria, exact evidence, audit linkage, projection transition, and completion eligibility |

Every stage preserves original Command, dispatch, attempt, adapter, Tool, operation, authorized scope, request/response integrity, external operation identifier presence, observation timestamps, Resource measurements, uncertainty, and contradictions. External timestamps never choose kernel Event order.

An adapter reports observations and interpretation only. It cannot declare organizational authority, Approval validity, Decision validity, verified success, or lifecycle completion, and cannot broaden scope. External denial is an observed result, not retroactive invalidation of the kernel's earlier governance authorization.

## 14. Reconciliation family

`ReconciliationRequest` identifies uncertain subject, original Command/dispatch/attempt/append, causal observations, expected result, Resource reservation, Approval use, permitted reads, deadline, and accountable owner. Any external read requires its own authorized Tool Command.

`ReconciliationEvidenceSet` preserves all supporting and contradictory observations, integrity, versions, provenance, presence states, and external limitations. `ReconciliationDisposition` returns one typed state, projection/Resource effects, any Incident, follow-up Decision/Approval, and audit links. It never overwrites an earlier attempt or decrements Approval usage.

## 15. Resource family

Resource records use a dimension type, stable Resource ID, unit, scope/aggregation keys, amount or bounded range, effective period, authority, Work Root, and evidence. Supported dimensions include money, compute, Tool calls, data access, elapsed time, human attention, credentials, reputation exposure, and Policy-defined additions.

| Record | Meaning |
|---|---|
| `ResourceEstimate` | Attributable expected use; not reservation or consumption |
| `ReservationRequest` | Proposed bounded hold per dimension before dispatch |
| `ReservationAccepted` | Atomic committed hold linked to admission Event |
| `ReservationRejected` | No hold; stable reason and limiting dimension |
| `ConsumptionObservation` | Reported use with source, time, evidence, uncertainty; not verified accounting |
| `ConsumptionVerified` | Kernel-admitted actual use after evidence/reconciliation |
| `ReservationReleased` | Later Event releasing demonstrably unused amount; original hold remains historical |
| `ConsumptionUncertain` | Safe retained hold or Policy bound pending reconciliation |
| `ReconciliationAdjustment` | Attributable append-only correction; never silent balance rewrite |
| `ResourceLimitReached` | Dimension/scope threshold and prevented future use |
| `ResourceStopTriggered` | Affected Actor/Task/Tool/schedule suspension or escalation link |

Reservations and consumption are distinct. Where reservation is required, consumption authorization without a committed reservation is structurally invalid. Related aggregation keys prevent transaction splitting.

## 16. Approval-use family

`ApprovalReferenceSnapshot` contains Approval ID/version, Decision, mode, permitted action/Resource/risk/budget scope, `used_count`, `usage_limit` presence, effective/expiry, revocation state, conditions, review schedule, approvers, Policy, and integrity.

`ApprovalUseValidation` records current Authority separately, Decision version, every condition, material-change result, separation of duties, current bound time, remaining use, and result. A successful validation is not Authority.

`ApprovalUseRecorded` is an atomic append transition with use ID, Command, Approval version, mode, prior/next monotonic `used_count`, exact operation scope, and Event/audit references. `single_use` moves 0→1; `bounded_repeat` increments below its positive limit; `standing` records each narrowly scoped current A2 use. Usage never decrements, including uncertain external outcomes. A4 standing use and unspecified A3 standing use are invalid.

## 17. Memory family

Logical records include:

- `EvidenceSubmission`: source, acquisition, collector, observed time, provenance, integrity, classification, relevance, reliability, supports/contradicts links;
- `ClaimProposal`: proposition, claimant/source, scope, validity, epistemic status, confidence, Evidence and conflict links;
- `MemoryAdmissionRequest` and `MemoryAdmitted`: complete provenance, transformation, Work Root/duty, validity, confidence where applicable, classification, retention, owner, license, integrity, and Event;
- `MemoryAdmissionRejected`: stable reason and no institutional-record implication;
- `MemoryRetrievalRequest`: requester, purpose, Work Root/duty, authority, classification ceiling, jurisdiction, validity time, query semantics/version;
- `MemoryDisclosure`: authorized pinned Record versions, purpose, provenance, classification/redaction, validity, confidence, conflicts, supersession, and audit;
- `MemorySuperseded` and `MemoryConflictMarked`: preserve all historical Records and links;
- `MemoryRedaction`, `MemoryDeletionRequest`, `MemoryLegalHold`, and `MemoryTombstoneCreated`: exact authority, scope, dependencies, retention/hold decision, propagation, nonreconstructive tombstone, and audit.

Retrieval ranking or model output cannot change Record validity, classification, authority, or lifecycle. Unadmitted output is not institutional memory.

## 18. Audit-reference family

`AuditReference` is a stable identifier and version for a protected or visible audit segment. A consequential trace references one Work Root, recording Command, initiating/participating/deciding/approving Actors, Role, Grant/delegation, Policy, evidence, Decision, Approval uses, Tool stages, Resources, causal references, outcomes, reconciliation, metrics, and Incident as applicable.

Protected content uses `ProtectedAuditReference` with classification, authorized resolver, integrity, provenance, and safe description. `AuditCompletenessResult` lists required, present, withheld, missing, invalid, and unresolved links. Missing mandatory linkage blocks consequential completion; the protocol MUST NOT substitute human-readable narrative.

## 19. Bootstrap family

`BootstrapRequest` is explicitly pre-Organization. It contains message identity/version, `organization_id=not_yet_known`, proposed stable Organization identity, verified initiating Human and proof, constitutional owner/governor Role, founding Role Assignment, founding Decision with constitutional duty reference, initial Grants, proposed founding Event semantics, audit references, expected empty/nonexistent stream condition, and idempotency key.

`BootstrapCommitted` atomically returns the Organization, Human Actor, Role, assignment, Decision, Grants, consecutive founding Event positions, and audit identities. No component is visible operationally before the whole outcome commits. `BootstrapRejected` creates no operational Organization. `BootstrapUncertain` quarantines the proposed identity and forbids retry under a new identity until reconciliation. Exact retry returns the original outcome; conflicting reuse rejects. An Employee, model, Tool, or fictional Human body cannot be constitutional owner.

## 20. Operational-control family

- `SuspensionRequest/Applied/Rejected`: exact affected scope, Incident, stop basis, authority, evidence, immediate prevented operations, review owner, and restoration conditions;
- `CancellationRequest/Applied`: future work prevented, in-flight state, reservations, Approval use, external uncertainty, compensation/reconciliation, and audit;
- `TimeoutObserved`: deadline, expected observation, bound time, source, uncertain state, and prohibited success/failure implication;
- `RetryRequest/Disposition`: original operation identity, new attempt identity where applicable, nonexecution/idempotency/duplicate-risk evidence, current gates, limit, reservation, Decision/Approval, and reason;
- `EscalationRequest/Disposition`: exact unresolved issue, safe default, evidence, eligible Actor/Role, Decision sought, deadline, and nonresponse semantics.

Retries preserve original operation and correlation identities while receiving a distinct attempt identity. Conflicting operation reuse is rejected. Cancellation and timeout do not prove external nonexecution.

## 21. Protocol state distinctions

Unknown and uncertain states are first-class and MUST NOT collapse into success or failure.

### 21.1 Command disposition

| From | Input | To |
|---|---|---|
| `submitted` | Validated and atomically appended | `accepted` |
| `submitted` | Gate fails with recording boundary | `rejected` |
| `submitted` | Exact prior identity/key | `previously_admitted` |
| `submitted` | Safe wait required | `paused` |
| `submitted` | Accountable Decision required | `escalated` |

All disposition states are terminal for that Command identity; continuation uses a new attributable Command except exact idempotent retrieval.

### 21.2 Tool execution knowledge

`authorized → dispatched → received → attempted → observed → interpreted → reconciling → verified|failed|partial|disputed|unresolved → compensated`.

Only evidence-backed transitions may advance. Timeout may move `dispatched`, `received`, or `attempted` to `unresolved/reconciling`, never directly to failure. Adapter interpretation cannot transition to `verified` without kernel admission.

### 21.3 Event append certainty

| State | Allowed next state |
|---|---|
| `proposed` | `committed`, `conflict`, `rejected`, `uncertain` |
| `uncertain` | `committed_confirmed`, `nonappend_confirmed`, `uncertain_escalated` |
| `committed`/`committed_confirmed` | Terminal; exact retry returns same outcome |
| `conflict`/`rejected`/`nonappend_confirmed` | Terminal for proposal identity; reevaluation uses new proposal |

### 21.4 Resource reservation and consumption

`estimated → reservation_requested → reserved|reservation_rejected → consumption_observed|nonexecution_verified|consumption_uncertain → consumption_verified|released|reconciling → adjusted|limit_reached|stop_triggered`.

Reservation remains historical after release. Unknown consumption retains the safe hold or Policy bound.

### 21.5 Approval use

`referenced → validated|invalid → use_proposed → use_recorded → external_outcome_known|external_outcome_uncertain`.

`used_count` changes only with atomic `use_recorded` and never decreases. External uncertainty does not return to `validated` for reuse.

### 21.6 Schedule instance

`defined → active → due_observed → materialization_proposed → materialized|missed|paused|rejected → dispatched|cancelled|catch_up_proposed`.

Series suspension/cancellation prevents future materialization; it does not erase existing instances.

### 21.7 Subscription delivery

`authorized → delivery_proposed → delivered|delivery_failed|suspended → acknowledged|redelivered|rejected → checkpointed`.

Redelivery preserves Event and delivery-operation identity. Acknowledgment and cursor do not alter Event acceptance.

### 21.8 Replay execution

`requested → authorized → guard_verified → running → completed|integrity_failed|version_failed|effect_violation`.

No replay state permits live dispatch. `effect_violation` is a critical failure and Incident candidate.

### 21.9 Reconciliation

`requested → gathering → evidence_complete|evidence_conflicted|external_unavailable → evaluating → verified|failed|partial|duplicated|compensated|disputed|unresolved → follow_up_required|closed`.

Closure requires evidence and audit; unavailable or conflicted evidence cannot become verified by timeout.

## 22. Stable reason-code registry

Reason codes are immutable machine keys formatted `CATEGORY.SPECIFIC_CAUSE`. For every registry row, the component before the period is its explicit normative `category` field and the complete code is its stable identifier. Human-readable `safe_detail` is bounded, localizable, nonauthoritative, and MUST NOT be used for branching. Each failure record also contains `retryability` (`never`, `after_change`, `idempotent_only`, `after_reconciliation`), `reevaluation` (`no`, `allowed`, `required`), `escalation` (`none`, `conditional`, `required`), `incident` (`no`, `consider`, `required`), safe disclosure class, and conformance scenario references.

| Code | Meaning | Retryability / reevaluation | Escalation / Incident | Safe disclosure | Conformance |
|---|---|---|---|---|---|
| `INPUT.MALFORMED` | Required structure/type invalid | never / no | none / consider | Field path without protected value | CMD-002, ADV-015 |
| `INPUT.OVERSIZED` | Size/depth bound exceeded | after_change / allowed | conditional / consider | Limit class only | ADV-015 |
| `VER.UNSUPPORTED` | Family/record/payload version unknown | after_change / required | conditional / no | Supported ranges | CMD-003 |
| `VER.DOWNGRADE_REJECTED` | Offered version would weaken semantics | after_change / required | conditional / consider | Version ranges | ADV-009 |
| `IDENTITY.UNKNOWN` | Actor cannot be resolved | after_change / required | conditional / consider | Do not reveal other identities | CMD-005 |
| `IDENTITY.FORGED` | Invocation proof does not bind Actor | never / no | required / required | Minimal security detail | ADV-016 |
| `IDENTITY.SUSPENDED` | Actor operationally suspended | after_change / required | conditional / consider | Suspension reference if authorized | CMD-006 |
| `ORG.BOUNDARY_VIOLATION` | Cross-Organization reference not authorized | never / no | conditional / consider | Do not reveal target existence | CMD-004, SUB-003, ADV-019 |
| `AUTH.MISSING` | No applicable Authority Grant | after_change / required | conditional / no | Required authority class | AUT-008, AUT-014 |
| `AUTH.EXPIRED` | Grant expired at evaluation time | after_change / required | conditional / no | Grant reference if authorized | AUT-002 |
| `AUTH.REVOKED` | Grant revoked | after_change / required | conditional / consider | Revocation reference if authorized | AUT-003 |
| `AUTH.INSUFFICIENT` | Requested scope exceeds Grant | after_change / required | conditional / consider | Scope category only | AUT-005 |
| `AUTH.DELEGATION_INVALID` | Delegation expands or lacks parent right | never / no | required / consider | Chain reference, no secrets | AUT-007 |
| `POLICY.DENIED` | Controlling Policy prohibits request | after_change / required | conditional / no | Policy/version and safe clause | AUT-010 |
| `POLICY.UNAVAILABLE` | Policy cannot be evaluated reliably | after_change / required | required / consider | Dependency class only | AUT-011, ADV-009 |
| `WORK_ROOT.MISSING` | Neither Goal nor duty supplied | after_change / required | none / no | Missing field | WRT-003 |
| `WORK_ROOT.DUAL` | Goal and duty both supplied | after_change / required | none / no | Conflicting field names | WRT-004 |
| `WORK_ROOT.INACTIVE` | Goal/duty not current for new work | after_change / required | conditional / no | State if authorized | WRT-005 |
| `WORK_ROOT.INCOMPLETE` | Duty lacks mandatory component | after_change / required | none / no | Missing component names | WRT-006 |
| `DECISION.MISSING` | Consequential Decision absent | after_change / required | required / no | Decision class required | AUD-009 |
| `DECISION.INCOMPLETE` | Mandatory Decision/audit fields absent | after_change / required | required / consider | Missing field categories | AUD-006, AUD-009 |
| `APPROVAL.MISSING` | Policy requires Approval and none applies | after_change / required | required / no | Approval class required | APR-008 |
| `APPROVAL.EXPIRED` | Approval expired | after_change / required | conditional / no | Approval reference if authorized | APR-005 |
| `APPROVAL.REVOKED` | Approval revoked | after_change / required | conditional / consider | Revocation reference if authorized | APR-006 |
| `APPROVAL.EXHAUSTED` | Usage limit reached | after_change / required | conditional / no | Limit and current count | APR-002, APR-003 |
| `APPROVAL.OUT_OF_SCOPE` | Use differs materially from approved scope | after_change / required | required / consider | Scope category | APR-004, APR-012 |
| `RESOURCE.UNAVAILABLE` | Required dimension lacks capacity | after_change / required | conditional / no | Dimension and shortfall class | RES-003, RES-004 |
| `RESOURCE.EXCEEDED` | Limit/stop threshold exceeded | after_change / required | required / required | Dimension/Incident reference | RES-010, RES-011 |
| `RESOURCE.UNVERIFIED` | Availability or consumption cannot be verified | after_reconciliation / required | required / consider | Dependency and uncertainty | RES-009, ADV-012 |
| `RESOURCE.RESERVATION_CONFLICT` | Concurrent/aggregate reservation conflicts | after_change / required | conditional / consider | Aggregation class | RES-002, RES-006 |
| `LIFECYCLE.INVALID_TRANSITION` | Transition not legal from current state | after_change / required | conditional / consider | Current/requested state | LIF-002 |
| `STATE.STALE_VERSION` | Expected entity/projection version stale | after_change / required | none / no | Expected/current versions if authorized | CMD-007, ADV-003 |
| `IDEMPOTENCY.CONFLICT` | Key/identity reused for different operation | never / no | required / consider | Key reference, no other operation detail | CMD-012 |
| `STREAM.CONCURRENCY_CONFLICT` | Expected prior stream position differs | after_change / required | none / no | Expected/current position | EVT-003 |
| `APPEND.FAILED` | Append confirmed not committed due failure | idempotent_only / required | conditional / consider | Failure class | ADV-001 |
| `APPEND.OUTCOME_UNCERTAIN` | Commit/noncommit cannot be established | after_reconciliation / required | required / required | Proposal ID and uncertainty | ADV-002 |
| `SUBSCRIPTION.UNAUTHORIZED` | Subscriber lacks scope/purpose/Grant | after_change / required | conditional / consider | No protected Event metadata | SUB-002 |
| `CLASSIFICATION.DENIED` | Classification ceiling/access insufficient | after_change / required | conditional / consider | Required class without content | SUB-004, MEM-004 |
| `REPLAY.SIDE_EFFECT_VIOLATION` | Replay attempted live effect | never / no | required / required | Effect boundary and trace | RPL-010, ADV-020 |
| `TOOL.SCOPE_VIOLATION` | Adapter/request exceeds authorized scope | never / no | required / required | Scope category, protected request ref | TOL-009 |
| `ADAPTER.IDENTITY_INVALID` | Adapter proof invalid or unauthorized | never / no | required / required | Minimal identity failure | TOL-008 |
| `EXTERNAL.OUTCOME_UNKNOWN` | External result cannot be determined | after_reconciliation / required | conditional / consider | Uncertainty and operation ref | TOL-004, OPS-005 |
| `TOOL.EVIDENCE_CONTRADICTORY` | Material Tool observations conflict | after_reconciliation / required | required / consider | Evidence refs/classification | TOL-007, ADV-007 |
| `RECONCILIATION.REQUIRED` | Safe state requires reconciliation | after_reconciliation / required | conditional / consider | Subject and deadline | TOL-004, RES-009 |
| `AUDIT.LINKAGE_MISSING` | Mandatory consequential trace absent | after_change / required | required / consider | Missing link categories | AUD-009, ADV-022 |
| `BOOTSTRAP.INCOMPLETE` | Founding atomic set invalid or partial | after_change / required | required / required | Missing categories, no protected content | BST-002, BST-004 |
| `INCIDENT.SUSPENDED` | Incident control blocks operation | after_change / required | required / already linked | Incident ref if authorized | OPS-001, SCH-006 |
| `OPERATION.TIMEOUT` | Required observation absent by deadline | after_reconciliation / required | conditional / consider | Deadline and subject | OPS-005 |
| `OPERATION.CANCELLED` | Future operation cancelled | never / no | none / no | Cancellation reference | OPS-003, SCH-010 |
| `RETRY.PROHIBITED` | Retry lacks proof/idempotency/approved risk | after_change / required | required / consider | Required evidence class | OPS-007, OPS-008 |
| `GOVERNANCE.DEPENDENCY_UNAVAILABLE` | Identity/authority/classification/audit dependency unavailable | after_change / required | required / consider | Dependency class only | ADV-010, ADV-011, ADV-021, ADV-022 |
| `INTEGRITY.VERIFICATION_FAILED` | Integrity proof/checkpoint/history invalid | after_change / required | required / required | Position/reference, no protected data | ADV-008, RPL-008, RPL-009 |

Codes are never repurposed. New codes are additive within a compatible version only when old consumers can safely treat the category as failure. Human text changes do not change machine semantics.

## 23. Security and isolation requirements

The receiver MUST enforce:

1. trusted envelope fields take precedence structurally; conflicting payload echoes reject the message;
2. every typed reference resolves within the one Organization or an explicit governed cross-Organization relationship;
3. classification may be raised on validation but never downgraded by caller, filter, payload, adapter, or replay;
4. Actor, Approval, Authority, Tool-result, and adapter references require integrity-bound resolution, not identifier existence alone;
5. subscription filters are versioned, bounded predicates applied after Organization/purpose/classification authorization and cannot request hidden fields;
6. replay mode and live mode are disjoint types at the adapter boundary; live adapters reject replay traffic even if misrouted;
7. idempotency keys are scoped by Organization and operation family; equality must not reveal whether the same key exists elsewhere;
8. input size, nesting, collection count, reference count, and expansion are bounded before authoritative parsing or effect;
9. type names are stable registry values, not caller-defined aliases; ambiguous or downgraded schemas reject;
10. human-readable failure detail is bounded, classified, and never includes protected target existence, secrets, raw payloads, or cross-Organization state;
11. external clocks are observations; kernel-bound `evaluation_time` and `stream_position` control admission and order; and
12. platform-security telemetry cannot become an Organization Event or authoritative state without a later valid Command.

## 24. Conformance traceability

This matrix maps protocol families to mandatory suites in `KERNEL_CONFORMANCE.md`; it does not duplicate the 206 scenario definitions.

| Families | Primary conformance suites |
|---|---|
| PF-01 Command, PF-02 disposition | CMD, AUT, WRT, APR, RES, ADV |
| PF-03 Event, PF-04 append | EVT, CMD, APR, RES, RPL, ADV |
| PF-05 Projection | EVT, RPL, POR, MEM, ADV |
| PF-06 Replay | RPL, POR, ADV |
| PF-07 Subscription | SUB, RPL, ADV |
| PF-08 Scheduling | SCH, OPS, APR, RES, ADV |
| PF-09 Tool dispatch, PF-10 attempt, PF-11 result | TOL, OPS, AUD, RES, ADV |
| PF-12 Reconciliation | TOL, RES, OPS, AUD, ADV |
| PF-13 Resource | RES, APR, TOL, SCH, ADV |
| PF-14 Approval use | APR, CMD, SCH, TOL, ADV |
| PF-15 Memory | MEM, AUD, RPL, ADV |
| PF-16 Audit | AUD, CMD, TOL, MEM, ADV |
| PF-17 Bootstrap | BST, EVT, AUD, ADV |
| PF-18 Operational control | OPS, LIF, SCH, TOL, ADV |
| PF-19 Version negotiation | CMD, EVT, RPL, POR, ADV |
| PF-20 Failure | Every negative suite scenario and ADV |

## 25. Symbolic logical examples

These examples show logical fields and relationships. Braces and arrows are explanatory notation, not an encoding.

### 25.1 Accepted Command

`CommandSubmission { message_id=msg:cmd:41, command_id=cmd:alpha:41, original_operation_id=op:alpha:41, org=org-alpha, actor=employee-operator, work_root=goal:launch, operation=artifact.review, expected_version=7, grant=grant:a2:active, approval=not_applicable, resources={compute:2}, idempotency=alpha/review/41 }`

`AdmissionAccepted[msg:disp:41] { command=cmd:alpha:41, evaluation_time=T100, events=[evt:reserve:41@P88, evt:task-started:41@P89], next_step=employee_work, verified_outcome=not_yet_known }`

### 25.2 Rejected Command

`AdmissionRejected[msg:disp:42] { command=cmd:alpha:42, reason=AUTH.EXPIRED, failed_gate=authority, effects=intentionally_empty, safe_detail="asserted grant expired at bound evaluation time" }`

### 25.3 Exact duplicate Command

`CommandSubmission { message_id=msg:cmd:41, command_id=cmd:alpha:41, same idempotency and semantics } → AdmissionPreviouslyAdmitted { original=msg:disp:41, evaluation_time=T100, new_events=none, new_reservations=none, dispatches=none }`

### 25.4 Atomic append batch

`AppendProposal[append:51] { expected_position=P90, ordered=[reservation, approval_use, dispatch_intent], preconditions={task_version:8} } → AppendCommitted { positions=[P91,P92,P93], all_or_none=true }`

### 25.5 Tool attempt followed by unknown outcome

`AuthorizedToolDispatchIntent[dispatch:7] → AdapterReceipt[receipt:7] → ToolExecutionAttempt[attempt:7] → TimeoutObserved { response=not_yet_known } → ReconciliationDisposition { state=unresolved, approval_use_restored=false, reservation=held_safe_bound }`

### 25.6 Contradictory Tool callbacks

`ExternalResponseObservation[obs:7a, result=completed] + ExternalResponseObservation[obs:7b, result=denied] → ReconciliationDisposition { state=disputed, evidence=[obs:7a,obs:7b], verified_outcome=not_yet_known }`

### 25.7 Standing Approval use

`ApprovalUseValidation { approval=approval:standing:a2, authority=grant:a2:active, review=current, scope=matched, prior_count=12 } → ApprovalUseRecorded { use=use:13, prior=12, next=13, operation=bounded_recurring_a2 }`

### 25.8 Scheduled instance materialization

`ScheduleDueObserved[due:series9:instance4] → ScheduleInstanceMaterialization { series=series9, instance=instance4, command=cmd:schedule:instance4, actor=service-scheduler, work_root=duty:maintenance, gates=current }`

### 25.9 Classified subscription delivery

`SubscriptionDelivery[delivery:77] { subscription=sub:restricted, event=evt:alpha:P120, classification=restricted, payload=withheld(restricted,protected:evt120), redelivery_count=0 }`

### 25.10 Replay report proving zero effects

`ReplayReport[replay:3] { mode=replay, range=P0..P120, projection=equivalent, external_references=reconstructed, tool_calls=0, communications=0, charges=0, approval_mutations=0, new_events=0 }`

### 25.11 Uncertain append requiring reconciliation

`AppendUncertain[append:52] { expected=P120, proposed_event_bindings=[a,b], retry_prohibited=true } → ReconciliationRequest { inspect_stream_by_idempotency=true } → AppendCommittedConfirmed|NonappendConfirmed|UncertainEscalated`

### 25.12 Atomic bootstrap

`BootstrapRequest[bootstrap:alpha] { proposed_org=org-alpha, verified_human=human-owner-alpha, role=constitutional-owner, assignment=founding, decision=decision:founding, grants=[grant:founding], events=[organization-created,...], idempotency=bootstrap/alpha } → BootstrapCommitted { all_entities_and_events_atomic=true, operational=true }`

## 26. Protocol conformance requirements

A conforming implementation MUST demonstrate through `KERNEL_CONFORMANCE.md` that:

- every family/type/version and presence state maps to its logical contract;
- caller-controlled data cannot populate or override kernel-bound facts;
- all authoritative mutations have one recording Command and immutable Event linkage;
- live, replay, observation, and platform-security modes are structurally separated;
- exact duplicates preserve identity and conflicting reuse fails closed within Organization scope;
- append, Resource reservation, Approval use, audit linkage, and dispatch intent are atomic where required;
- Tool knowledge and append certainty preserve unknown/uncertain states;
- reason codes, not human text, drive machine behavior; and
- exports retain enough semantic and version evidence for replay and portability.

Failure to understand a type, version, presence state, reason code category, classification, integrity proof, or governed reference MUST fail closed. Protocol convenience cannot expand constitutional authority or weaken institutional accountability.
