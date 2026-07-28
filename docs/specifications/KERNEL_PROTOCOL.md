# AIOS Kernel Logical Protocol

**Specification version:** 0.0.2
**Protocol family version:** 1.0
**Status:** Normative logical contract

## 1. Purpose, scope, and principles

This document defines the canonical logical records exchanged at AIOS kernel boundaries. It specifies meaning, trust, versioning, presence, state distinctions, and observable outcomes. It does not prescribe an encoding, serialization, transport, programming language, storage system, message broker, deployment platform, or model provider. The record examples are symbolic field maps, not a required wire format.

This protocol refines [`ENTITY_MODEL.md`](ENTITY_MODEL.md), [`EVENT_MODEL.md`](EVENT_MODEL.md), [`LIFECYCLES.md`](LIFECYCLES.md), [`INVARIANTS.md`](INVARIANTS.md), [`DECISION_RECORD.md`](DECISION_RECORD.md), [`ARCHITECTURE_PRINCIPLES.md`](ARCHITECTURE_PRINCIPLES.md), [`KERNEL_CONTRACT.md`](KERNEL_CONTRACT.md), and [`KERNEL_CONFORMANCE.md`](KERNEL_CONFORMANCE.md). Those documents and the Constitution control on conflict.

In this protocol, **Employee** means the constitutional AI Employee and excludes Human Actors. A model instance is a replaceable computational Resource, never an Actor, accountable decider, approver, or Authority holder.

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
| `not_applicable` | The selected schema classifies the field `explicitly_not_applicable` for this concrete record | Validator confirms that classification; producer cannot use it to avoid a required value or decorate an optional/prohibited field |
| `intentionally_empty` | Applicable collection was evaluated and contains no entries | Preserve explicit empty meaning and evaluation basis |
| `withheld(classification, reference)` | Value exists but disclosure is not authorized | Preserve governed reference, classification, and accountable withholding basis |
| `redacted(tombstone_reference)` | Previously recorded value was lawfully removed or obscured | Preserve nonreconstructive tombstone and audit linkage |
| `externally_unavailable(reference)` | External source could not provide the value | Preserve external reference, failure observation, and reconciliation requirement |
| `conflicted(evidence_references)` | Material contradictory values remain unresolved | Preserve every claim and evidence relationship; do not select silently |

A field schema has exactly one applicability classification for each concrete record: `required`, `optional`, `prohibited`, or `explicitly_not_applicable`. An optional field may be absent. A required field appears with `known`, `unknown`, or `not_yet_known` only when that presence state is permitted by the selected subtype; unknown is not omission. A field classified `explicitly_not_applicable` uses the defined `not_applicable` presence form only when the schema requires an explicit marker. A prohibited field MUST NOT appear, even empty or `not_applicable`. A generic null without a preserved presence state is nonconforming.

Ceremonial `not_applicable`, fabricated confidence, placeholder Evidence, generic empty results, and empty arrays used to evade required semantics are invalid. `intentionally_empty` is permitted only for an applicable collection that was actually evaluated and whose empty result is itself meaningful.

## 3. Common logical envelope

### 3.1 Trust roles

- **Caller-supplied:** asserted by the initiating boundary; untrusted until validated.
- **Kernel-bound:** supplied only by the kernel at admission or append; a caller value is prohibited or ignored and recorded as a validation failure.
- **Kernel-validated:** caller may assert it, but the kernel resolves the authoritative referenced version and may reject; it never silently replaces the assertion with a broader value.
- **Derived:** computed deterministically from admitted facts and named versions.
- **Adapter-observed:** reported as an observation with provenance; never authoritative organizational success by itself.

Payload data MUST NOT override envelope attribution, Organization, evaluation time, ordering, classification, authority, Approval, Work Root, or audit fields. Duplicate trusted fields in a payload make the message structurally invalid unless the record type explicitly defines them as nonauthoritative echoes and requires equality.

### 3.2 Envelope field contract

Applicability abbreviations are `CMD` Command, `DSP` disposition, `EVT` Event, `APP` append, `PRJ` projection, `RPL` replay, `SUB` subscription/schedule, `TLR` Tool/reconciliation, `RES` Resource/Approval, `MEM` memory/audit, `BTS` bootstrap, `OPS` operational control, and `VER` version/failure. A cell may name mechanically decidable subtype rules, but after selecting the record type, schema version, payload type/version, traffic mode, consequence class, and named subtype conditions, each field MUST resolve to exactly one of `required`, `optional`, `prohibited`, or `explicitly_not_applicable`. There is no unresolved conditional applicability state. Unlisted fields are prohibited unless the selected subtype schema explicitly classifies them otherwise.

| Field | Meaning | Supplier and validation | Applicability | Mutability and replay | Security significance |
|---|---|---|---|---|---|
| `message_id` | Globally stable identity of this logical message | Caller for request; kernel for kernel result; uniqueness validated | required: all | Immutable; historical records preserve identity; replay-control/report messages use distinct replay-mode identities and never live operational identities | Deduplication and forgery boundary |
| `message_type` | Stable unambiguous type name | Record producer; validated against selected family/type version | required: all | Immutable; historical interpretation uses recorded version | Prevents type confusion |
| `schema_version` | Logical record-type schema version | Producer; negotiation and validator constrain | required: all | Immutable; replay uses historical semantics | Prevents downgrade/reinterpretation |
| `organization_id` | Sole Organization scope and AIOS tenancy boundary | Caller assertion then kernel validation; kernel result copies validated value | required: all except pre-org BTS/platform security | Immutable; replay preserves | Primary isolation, governance, authority, and Event-ordering boundary; no separate Tenant entity or `tenant_id` |
| `initiating_actor_id` | One technical initiating Actor | Caller assertion plus invocation proof; kernel resolves | required: CMD, OPS; BTS requires verified founding Human; other subtype schemas resolve optional or prohibited | Immutable; replay preserves | Attribution; not automatically decider |
| `participant_actor_ids` | Other attributable participants | Caller asserts; kernel validates each | optional only for CMD, DSP, EVT, MEM, OPS subtypes that admit participants; prohibited otherwise | Immutable per message; replay preserves | Collective accountability, no authority aggregation |
| `recording_command_id` | Command through which authoritative mutation was admitted | Kernel binds Events/mutations to admitted Command; caller may reference for result reports | required: EVT, APP and authoritative RES, MEM, OPS; Tool/result subtype schema resolves required or optional; prohibited: initial CMD | Immutable; replay preserves | Mutation provenance, distinct from cause |
| `causal_reference` | Typed cause/trigger of underlying occurrence | Caller or adapter asserts with evidence; kernel validates type/provenance | required when the subtype records a caused/observed occurrence; explicitly_not_applicable for independently initiated internal Command; prohibited where no causal semantics exist | Immutable assertion; corrections append | Prevents recording/cause conflation |
| `correlation_id` | End-to-end governed case or operation group | Caller supplies or kernel binds at bootstrap/system origin | required: CMD, DSP, EVT, TLR, SUB, OPS; other subtype schemas resolve optional or prohibited | Immutable; replay preserves | Must not authorize cross-org correlation access |
| `causation_message_id` | Immediately preceding protocol message in message-flow lineage | Producer supplies; kernel validates existence and Organization | required when a declared message-flow predecessor exists; explicitly_not_applicable for independently originated messages; prohibited when lineage is not represented | Immutable; replay preserves | Flow lineage, not real-world causal proof |
| `idempotency_key` | Actor- and operation-family-scoped mutation deduplication key within one Organization | Caller supplies for mutating request; kernel scopes and compares material operation semantics | required: mutating CMD, BTS, materialization, retry; optional for explicitly idempotent read subtypes; prohibited otherwise | Immutable; replay does not reacquire | Cross-Actor/Organization isolation; conflict fails closed |
| `issued_at` | Producer-asserted issue time | Producer; kernel treats as observation, not authoritative evaluation | required: requests; optional: reports whose schema permits producer time; prohibited otherwise | Immutable; replay preserves | Cannot determine authority expiry alone |
| `evaluation_time` | Single authoritative admission time | Kernel-bound only | required: DSP, EVT, APP and admitted mutations; prohibited: caller requests | Immutable; replay uses recorded value | Prevents clock manipulation and nondeterminism |
| `received_at` | Boundary-observed receipt time | Receiving boundary records as observation | optional only when the receiving-boundary subtype records it; prohibited otherwise | Immutable observation; not ordering authority | Latency/audit only; external skew tolerated |
| `stream_id` | Single authoritative Organization Event stream for post-genesis organizational state | Kernel-bound | required: EVT, APP and stream-bound PRJ/RPL/SUB delivery; prohibited: caller-chosen or non-stream subtypes | Immutable; replay selects recorded stream | Prevents stream injection and independent authoritative entity streams |
| `stream_position` | Kernel-assigned Event order | Kernel-bound | required: accepted EVT and Event deliveries; optional for PRJ/RPL reports naming a position; prohibited: proposals/caller values | Immutable; replay preserves | Sole organization order authority |
| `expected_stream_position` | Authoritative Organization-stream append precondition | Caller or kernel append planner asserts; kernel compares current Organization position | required: APP and post-genesis mutating subtype; optional for eligible CMD/PRJ reads; prohibited otherwise | Immutable input; replay applies historical outcome | Prevents lost update; entity preconditions cannot replace it |
| `classification` | Message/payload disclosure class | Caller asserts minimum; kernel validates and may raise, never lower without authority | required: all except negotiation; VER subtype resolves required or prohibited | Immutable for record; later reclassification Event | Disclosure and filter boundary |
| `purpose` | Specific authorized processing purpose | Caller asserts; kernel validates against Role, Grant, Policy, subscription | required: requests, retrieval, subscription; optional for permitted results; prohibited otherwise | Immutable; replay preserves | Purpose limitation |
| `work_root` | Exactly one active Goal or complete duty for Task/Action | Caller asserts; kernel validates exclusive form and current scope | required: Task/Action and their work-related CMD/TLR/SUB/RES/OPS records; optional for consequential MEM when schema permits; prohibited for Project/Objective/Plan as root | Immutable for Task/Action; replay preserves | Prevents unrooted, dual-root, or invalid-kind work |
| `authority_references` | Asserted relevant Grants and chain | Caller asserts; kernel resolves current validity and scope | required: consequential CMD, TLR, RES, OPS; optional for explicitly nonconsequential governed subtypes; prohibited otherwise | Immutable snapshot references; replay historical | Presence never proves authority |
| `policy_references` | Named Policy content versions used or asserted | Caller may assert; kernel pins controlling versions | required: DSP, consequential EVT/APP, audit and evaluated governance result; optional for eligible requests; prohibited otherwise | Immutable once admitted; replay historical | Prevents silent current-policy reinterpretation |
| `decision_reference` | Consequential Decision identity and `decision_content_version`/`entity_revision` | Caller asserts; kernel validates completeness/current applicability | required: consequential operations; optional for schema-permitted linkage; prohibited otherwise | Immutable reference; material change new Decision | Cannot be invented by kernel |
| `approval_references` | Approval IDs, named revisions, and modes used | Caller asserts; kernel validates and records use | required when controlling Policy requires Approval; optional only where schema permits relevant non-use references; prohibited otherwise | Immutable per use; replay rebuilds monotonic usage | Approval never Authority |
| `resource_references` | Resources affected or measured | Caller/adapter asserts; kernel validates scope and state | resolved by Event/record subtype: required when material, optional when relevant, explicitly_not_applicable when meaningless and declared, prohibited when forbidden | Immutable facts; corrections append | Reservation separate from consumption |
| `audit_reference` | Stable audit record/segment link | Kernel derives or validates protected reference | required: authoritative consequential result and other subtype-mandated records; optional where schema permits; prohibited otherwise | Immutable linkage; replay rebuilds | Missing link blocks completion |
| `payload_type` | Stable payload semantic type | Producer; validated under record type | required: payload-bearing messages | Immutable; replay historical | Blocks ambiguous payload interpretation |
| `payload_version` | Payload schema version | Producer; negotiated/validated | required: payload-bearing messages | Immutable; replay historical | Blocks schema downgrade |
| `payload` | Type-specific logical fields | Producer according to trust rules; kernel validates | required for payload-bearing subtype; prohibited for payloadless subtype | Immutable message content; correction new message/Event | Cannot override trusted envelope |
| `integrity_reference` | Integrity proof or protected digest reference | Producer supplies; receiving authority verifies | required: EVT, APP, audit, Tool evidence, checkpoints; optional for subtype-permitted protected references; prohibited otherwise | Immutable; replay verifies | Tamper evidence, not semantic authority |
| `redaction_metadata` | Withholding/redaction basis and tombstone references | Authorized governance boundary only | required for redacted/withheld/tombstone subtype; optional for protected subtype that permits it; prohibited otherwise | Append-only changes; replay applies historical Events | Must not leak or erase accountability |

### 3.3 Family applicability rules

Every record definition below resolves the common rules for its concrete subtype. The selected schema publishes a mechanically evaluable applicability map; validation MUST reject an unresolved field, a missing required field, a present prohibited field even when empty, and a presence value inconsistent with its classification. Optional absence and `explicitly_not_applicable` are distinct. Pre-Organization bootstrap classifies `organization_id` as `explicitly_not_applicable` and carries the proposed stable Organization identity in its payload. Platform-security telemetry is explicitly non-authoritative, uses a platform scope rather than an Organization stream, and MUST NOT be accepted as an AIOS Event.

## 4. Versioning and negotiation

Every message records:

- `protocol_family_version`;
- record-type `schema_version`;
- `payload_version` where payload exists;
- referenced entity `entity_revision` where concurrency or exact state matters;
- explicitly named business-content version such as `decision_content_version` or Artifact content version;
- controlling `policy_content_version` references when evaluated;
- governing `specification_version` references;
- migration-evidence reference if transformed.

These dimensions are never interchangeable. Lifecycle state is not a version, and Organization `stream_position` is ordering rather than entity or schema revision. A field named only `version` is prohibited where more than one dimension could apply.

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
| `target_references` | Typed entity/Resource targets and explicitly named expected `entity_revision`, business-content version, or stream precondition |
| `invocation_proof_reference` | Proof bound to asserted initiating Actor; not a Credential value |
| `work_root` | Exclusive union of one active Goal reference or one complete duty reference for every Task/Action; both, neither, Project-only, and Objective-only forms are structurally invalid |
| `planning_references` | Optional subordinate Project, Objective, and Plan references; absence is valid and none is a Work Root |
| `asserted_authority_references` | Untrusted Grant/delegation references until kernel resolution |
| `decision_reference`, `approval_references` | Exact named content versions and `entity_revision` values asserted for consequential/approval-gated work |
| `expected_resource_use` | Estimate per independently governed dimension |
| `reservation_request` | Maximum exposure, units, aggregation keys, and release conditions |
| `lifecycle_preconditions` | Expected entity versions, states, dependencies, and requested transition |
| `risk` and `reversibility` | Classification, restoration plan/reference, verification, window, uncertainty |
| `evidence_references` | Pinned supporting and contradictory Evidence versions |
| `result_criteria` | Typed criteria required before verified completion |
| `stop_conditions` | Budget, time, Incident, safety, evidence, and external conditions |
| `tool_request` | Tool, operation, exact bounded inputs/protected references, and result contract when applicable |

Milestone 3 delegated capability Commands remain ordinary `CommandSubmission`
records and use the authenticated recording-boundary contract. Their selected
operation schema requires a canonical Task reference and exact requested
capability. Only after admission, governance resolves the same-Organization
Temporary Worker enrollment, active Role Assignment and Role, pinned source
Authority Grant evidence, accepted nonterminal Task, exact capability
allowlisting, and unconsumed deterministic Resource ceiling. No Worker-specific
admission family, Work Item identifier, wildcard capability, or alternate Event
stream is permitted. The complete profile is defined in
[`GOVERNED_WORK_DELEGATION.md`](GOVERNED_WORK_DELEGATION.md).

### 5.1 ActivateRole subtype

The sole ordinary Role activation operation has `operation_type=ActivateRole`, `operation_version=1.0`, `payload_type=ActivateRolePayload`, and `payload_version=1.0`. Its typed payload contains exactly:

- `role_id`: the stable `RoleId` of the target Role; and
- `expected_entity_revision`: a positive integer naming the exact Role projection revision expected by the caller.

No lifecycle reason, requested state, Organization identity, Actor identity, timestamp, authority assertion, Decision, Approval, idempotency key, or Organization stream position is duplicated in this payload. The requested transition is fixed by the operation contract.

`target_references` MUST contain exactly one `EntityReference` with `entity_type=Role`, the same `role_id`, and `expected_version` equal to `expected_entity_revision`. `lifecycle_preconditions` MUST declare `current_state=draft` and `requested_state=active`. The ordinary Command envelope supplies exactly one `organization_id`, initiating Actor, asserted Authority references, and idempotency key; the ordinary runtime Command context supplies the expected Organization stream position. A mismatched payload, target, lifecycle precondition, or revision is malformed.

The authenticated admission boundary MUST first prove completed genesis and exact Organization and initiating-Actor attribution. After that proof, the Role domain precondition MUST establish an existing Role in `draft` and a matching Role revision from the same bound Organization history used for append. Governance MUST require at least one asserted Grant reference and validate current authority whose action scope includes `role.activate` for the exact Role and Organization. Role activation is Authorized: it has no intrinsic Decision or Approval requirement, but every Decision, Approval, Policy, risk, or separation-of-duties condition independently applicable under higher rules remains mandatory. Governance evaluation remains outside the Role domain transition.

ActivateRole rejection uses the existing stable reason registry: malformed payload, target, or lifecycle precondition uses `INPUT.MALFORMED`; unsupported operation, record, or payload version uses `VER.UNSUPPORTED`; Organization mismatch uses `ORG.BOUNDARY_VIOLATION`; missing, insufficient, invalid, or unavailable governance uses the applicable `AUTH.*`, `POLICY.*`, `DECISION.*`, `APPROVAL.*`, or `GOVERNANCE.DEPENDENCY_UNAVAILABLE` code; a nonexistent Role or any source state other than `draft`, including the already-active founding Role, uses `LIFECYCLE.INVALID_TRANSITION`; mismatched Role revision uses `STATE.STALE_VERSION`; stale Organization position uses `STREAM.CONCURRENCY_CONFLICT`; and conflicting idempotency reuse uses `IDEMPOTENCY.CONFLICT`. Protocol validation precedes governance, governance precedes domain transition evaluation, and none of these failures emits `RoleActivated`.

Exact redelivery uses the existing `(organization_id, initiating_actor_id, operation_family, idempotency_key)` scope bound to complete material Command semantics. It returns the original disposition, identifiers, positions, and evaluation time and appends no new Event. A new Command for an already-active Role is not exact redelivery and receives the lifecycle rejection above. The expected Organization stream position remains the authoritative append precondition; `expected_entity_revision` is an additional domain precondition and cannot authorize a write against a stale Organization position.

The caller may assert references only. The kernel resolves Organization, identity, Role, Grants, Policies, Work Root, Decision, Approvals, Resources, lifecycle, evidence access, and current versions. It MUST reject rather than replace an invalid assertion with a broader or different one.

### 5.2 Authenticated recording-boundary contract

`RecordingBoundaryResolver` is the capability-neutral trusted admission port for ordinary post-genesis Commands. It performs no authorization and has no Organization Event-store, idempotency, audit, handler, or append capability. It accepts one immutable `AdmissionClaim` containing exactly:

- `message_id` and `command_id`, binding the resolution to one Command attempt;
- the claimed stable `organization_id` and `initiating_actor_id` copied from the Command;
- the Command's `invocation_proof_reference`; and
- the admission-claim `schema_version`.

The resolver returns the closed union `AdmissionEstablished | AdmissionDenied`.

`AdmissionEstablished` contains the bound claim message and Command identities; the exact canonical Organization and initiating Actor identifiers; immutable Organization-genesis, Actor-identity, invocation-proof, and authentication-evidence references; and the admission-mechanism reference, mechanism version, and result schema version. The Organization MUST exist with completed genesis as an authoritative ordinary recording boundary. The Actor MUST exist as a stable Actor identity and be attributable within that exact Organization, and the trusted mechanism MUST authenticate the invocation proof for that Actor and Command attempt. The result MUST exactly equal the submitted Organization, Actor, Command, message, and proof references. Aliases, display names, email addresses, usernames, external account identifiers, or cross-Organization fallback do not canonicalize a Command identity; a mismatch fails closed.

Only the trusted injected resolver supplies `AdmissionEstablished` to kernel orchestration. It is an authentication and attribution proof, never an Authority Grant, Role Assignment, Policy result, Approval, Decision, or capability. Domain handlers do not inspect it. Governance consumes its canonical Actor and evidence references while independently evaluating permission.

`AdmissionDenied` contains the claim message and Command identities, one stable admission reason code, `failed_gate` (`organization_boundary`, `attribution_authentication`, or `admission_dependency`), bounded `safe_detail`, optional non-authoritative diagnostic facts, and schema version. It contains no authoritative Organization audit or disposition identity and does not prove that the claimed Organization exists. `ORG.UNKNOWN`, `IDENTITY.UNKNOWN`, `IDENTITY.FORGED`, `IDENTITY.SUSPENDED`, `ORG.BOUNDARY_VIOLATION`, and `GOVERNANCE.DEPENDENCY_UNAVAILABLE` are the permitted admission-resolution causes. External detail for unresolved Organizations and identities MUST be equivalently bounded so it does not disclose another Organization or Actor; authorized internal diagnostics MAY retain the more specific code without becoming Organization history.

The ordinary admission sequence uses support-resolution **Model A**. Effect-free validation first checks object/envelope shape, immutable attribution fields, identifier encoding, unknown/forbidden fields, payload decodability, and whether schema, operation, and version are supported. `INPUT.MALFORMED` and `VER.UNSUPPORTED` at this stage are pre-boundary results and MUST NOT invoke the resolver or touch an Organization namespace. The resolver runs next. Only `AdmissionEstablished` permits Organization stream read, expected-position comparison, Organization-scoped idempotency, attributable context construction, governance, handling, authoritative identifier allocation, or recording.

The kernel MAY bind one evaluation time before resolution through its injected effect-free Clock. Pre-boundary failure has optional evaluation time but no authoritative disposition ID, Event ID, Audit Record ID, domain Event, recorded Event, or audit record. It creates and inspects no Organization idempotency entry. Repeated denial is another non-recorded attempt, not exact redelivery. Authentication-provider anti-replay or nonce controls are outside Organization idempotency and are neither represented nor weakened here.

After establishment, the admitted context contains the original immutable Command, canonical Organization and Actor identities, immutable admission proof, bound evaluation time, and prior Organization Events. Governance evaluates authorization; the domain handler evaluates deterministic domain semantics. A later governance or handler denial MAY append an attributable atomic rejection/audit sequence. A stale expected position returns a concurrency conflict without appending through that stale position; append failure cannot claim a durable rejection; idempotency conflict preserves the original registration; invalid history fails closed. Exact redelivery applies only to a previously recorded attributable disposition.

Bootstrap remains on PF-17's reserved pre-Organization constitutional path and does not invoke `RecordingBoundaryResolver`. Ordinary Commands cannot select bootstrap traffic or admission basis. Replay consumes authoritative history and MUST NOT invoke admission resolution or authentication.

### 5.3 Executable source Authority Grant proof

Milestone 3 uses the immutable, capability-neutral
`SourceAuthorityGrantClaim` and `SourceAuthorityGrantProof` records to prove the
source of a later Task's attenuated authority. This proof is not an admission
mechanism, an Authority Grant lifecycle API, or an authorization decision.
`SourceAuthorityGrantResolver` is a read-only trusted boundary that resolves
authoritative Grant evidence only after `AdmissionEstablished` has bound the
canonical Organization and Actor. Caller assertions in the claim cannot create
or replace that attribution.

The claim binds one Command, canonical Organization, source Grant, grantor,
authorized subject Actor, exact purpose, exact finite capability request, one
Resource ceiling, deterministic completion condition, evaluation time, and
schema version. The successful proof binds those facts to an active source
Grant; its parent Grant and delegation basis; exact permitted and prohibited
capability sets; the Grant Resource ceiling; an affirmative delegation right;
the effective time and evaluated lifecycle state; Grant entity revision; and
the authoritative Event, Organization-stream position, integrity, and evidence
references from which the proof is derived.

Capability tuples MUST be nonempty where authority is requested, duplicate-free,
lexically ordered, and composed only of exact `CapabilityId` values. Wildcards,
namespace patterns, and implicit capability discovery are invalid. Requested
capabilities MUST be a subset of the permitted set and disjoint from the
prohibited set. The sole Milestone 3 Resource dimension is
`accepted_delegated_capability_execution`; containment requires the same
`ResourceId` and unit and a positive requested integer limit no greater than the
source Grant limit. The proof carries no consumption state.

Constitutional purpose is descriptive rather than a policy language. Therefore
this contract permits only exact normalized purpose equality; it does not infer
semantic containment from prose. The deterministic Task termination condition
must likewise equal the condition authorized by the source Grant. The proof is
constructible only for a Grant recorded active and effective at its bound
evaluation time and whose authoritative evidence expressly permits delegation.
Suspended, expired, revoked, future-effective, malformed, unverifiable, or
cross-Organization evidence fails closed for a new action.

Consumers validate in this order: record shape and version; canonical
Organization; Grant identity and immutable evidence; grantor and subject;
lifecycle and effective time; exact purpose and affirmative delegation basis;
exact capability containment; Resource containment; then complete downstream
Task attenuation. Failure uses the existing stable `INPUT.*`, `VER.*`,
`ORG.*`, `AUTH.*`, `RESOURCE.*`, `GOVERNANCE.*`, or `INTEGRITY.*` reasons in a
typed `SourceAuthorityGrantDenied`; no new reason family is introduced.

An accepted execution records the exact proof and evidence lineage used at its
decision point. Replay validates that immutable recorded proof and MUST NOT call
the resolver, consult current Grant state or policy, reinterpret ambient time,
or perform external identity lookup. Later suspension, expiry, revocation, or
policy change governs new actions only and cannot invalidate an already
accepted historical execution.

Every mutating `CommandSubmission` has an idempotency scope containing at least `(organization_id, initiating_actor_id, operation_family, idempotency_key)`. It also binds `original_operation_id` and the canonical semantic digest or equivalent exact comparison of every material operation field. Exact redelivery returns the original disposition, identifiers, stream positions, evaluation time, Resource effects, Approval-use result, and dispatch identity. Conflicting reuse preserves the first registration, fails closed, and discloses no other Actor's operation or key use.

Decision-bearing Commands use `GovernanceRoleAttribution`: `proposer_actor_ids`, `recommender_actor_ids`, `accountable_decider`, `approver_actor_ids`, `technical_recorder_actor_id`, `initiating_actor_id`, optional `governing_body_disposition`, and individually attributable participation records. Technical initiation, proposal, recommendation, recording, deciding, and Approval are distinct even when one eligible Actor fills several roles.

For every A4 and Constitution- or Policy-reserved A3 Decision, `accountable_decider` resolves either to one eligible Human Actor or a valid `GoverningBodyDisposition`. An AI Employee MAY research, recommend, propose, prepare, route, or technically record, but MUST NOT occupy that accountable-decider field. A separate Human Approval does not convert an AI-authored Decision into a Human Decision. Operational Decisions validly delegated to an AI Employee remain representable.

`GoverningBodyDisposition` contains stable body identity; authoritative membership snapshot references; individually attributable eligible Human vote, consent, dissent, abstention, and recusal records; each member's authority basis; named quorum-rule version; named voting-Policy version; deterministic derived result; accountable body disposition; and separate technical initiator. A body MUST NOT be encoded as one fictional Human.

## 6. Admission disposition family

All attributable dispositions contain the original `command_id`, bound `evaluation_time`, reason-code presence, and audit reference when a valid Organization recording boundary exists. A pre-boundary `RuntimeRejected` or equivalent typed result has a reason code, failed gate, bounded safe detail, optional evaluation time, absent authoritative disposition identity, no domain or recorded Events, and no authoritative audit record.

For a Decision-bearing Command, every disposition also preserves the submitted and validated `GovernanceRoleAttribution` or the precise role-validation failure. Acceptance MUST NOT collapse proposer, recommender, accountable decider, approver, technical recorder, Governing Body, or initiating Actor into one generic author field.

| Disposition | Required fields | Meaning and prohibited implication |
|---|---|---|
| `accepted` | Event IDs/bindings, assigned positions, derived target versions, committed reservations, Approval-use transition, exact authorized next step | Authorizes only the recorded next step; does not imply adapter receipt, attempt, external effect, verification, success, or lifecycle completion |
| `rejected` | Stable reason code, failed gate, safe detail, Policy/invariant references, explicit zero mutation/effect assertions | Confers no authority; does not imply malicious intent or external nonoccurrence |
| `previously_admitted` | Original disposition identity, all identifiers and Event positions, original evaluation time, Resource effects, Approval-use result, dispatch identity, and idempotency match proof | Is not a new acceptance and MUST NOT repeat Event, use, reservation, schedule instance, dispatch, or delivery |
| `paused` | Unresolved state, safe holding state, owner, timeout/review condition, zero implied success | Does not authorize later automatic continuation without a newly admitted Command or defined current-state revalidation |
| `escalated` | Exact question/Decision sought, eligible Actor/Role, evidence, deadline, safe default | Nonresponse is not Approval or Authority |

## 7. Event record family

`EventRecord` is immutable. It contains the complete common Event envelope and every semantic field required by the selected Event-type `schema_version` and `payload_version`; optional fields appear only where allowed; prohibited fields do not appear; and explicit `not_applicable` appears only when that schema classifies the field `explicitly_not_applicable`. A prohibited field fails validation even when empty.

Event-type schemas classify Resource references, supporting Evidence, result, epistemic status, confidence, projection effects, Approval-use effects, and other semantic fields independently. They are not universally required. Deterministic mechanical Events MAY omit or explicitly mark semantically meaningless fields not applicable when their schemas permit it. Consequential Events MUST contain every Evidence, result, Resource, and epistemic field material to accountability and interpretation. Missing required fields, ceremonial markers, fabricated confidence, placeholder Evidence, generic empty results, and evasive empty collections fail with the applicable Event reason code.

Consequential Decision and Action Event schemas require `GovernanceRoleAttribution` sufficient to preserve the distinct initiating, participating, proposing/recommending, accountable-deciding, approving, and technical-recording roles, including the full Governing Body disposition reference when applicable.

`RoleActivated` has Event `schema_version=1.0` and payload version `1.0`. Its payload contains exactly `role_id`, `prior_lifecycle_state=draft`, `lifecycle_state=active`, `prior_entity_revision`, and `entity_revision`, where the resulting revision equals the positive prior revision plus exactly one. The Event envelope supplies Organization, initiating Actor, recording Command, correlation, evaluation time, authoritative Organization `stream_id` and `stream_position`, classification, integrity, and audit linkage; its causal Command reference MUST equal that recording Command. Applicable Authority, Policy, Decision, Approval, and authenticated-admission evidence remains in governed envelope/audit references and MUST NOT be copied into the domain payload. The Event identifies the resulting Role revision in its entity reference and creates no Assignment, Grant, or other Role fact.

The Event `timestamp` is the kernel-recorded acceptance/occurrence-in-AIOS time and controls authoritative ordering only through its assigned stream position. A real-world `occurred_at`, `observed_at`, adapter time, or external-system time is a payload observation with source and uncertainty; it never replaces `timestamp`, `evaluation_time`, or `stream_position`.

When applicable, `epistemic_status` is one of `deterministic`, `observed`, `asserted`, `inferred`, `predicted`, or `disputed`. Confidence is omitted or explicitly not applicable for deterministic transition facts as selected by schema and required for inferred, predicted, uncertain observed, and disputed assertions. Confidence never creates authority or truth.

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

Every post-genesis entity mutation uses the one Organization stream. A Role-affecting proposal therefore carries the Organization `stream_id` and `expected_stream_position`, plus any Role identity, current state, and `entity_revision` required as domain preconditions. Those domain preconditions MUST be evaluated against the same Organization history used for append and MUST NOT act as an independent Role-stream authorization. Role Events receive consecutive Organization positions alongside Events for other contained entities.

| Outcome | Semantics |
|---|---|
| `AppendCommitted` | Entire set assigned consecutive positions and made authoritative atomically; committed reservation/use/intent identities returned |
| `AppendConflict` | Current position/precondition differs; nothing appended or mutated; reevaluation required |
| `AppendRejected` | Validation/invariant/integrity failure; nothing appended, dispatched, reserved, consumed, or delivered |
| `AppendUncertain` | Boundary cannot prove committed or noncommitted state; no retry, release, second use, or dispatch is allowed until reconciliation by idempotency and stream inspection |

Storage uncertainty MUST NOT be represented as success or confirmed nonappend. Reconciliation returns the original `AppendCommitted` identity if found, confirmed `AppendRejected`/nonappend evidence if absent under an authoritative check, or remains uncertain and escalates.

## 9. Projection family

`ProjectionQuery` identifies Organization, projection type, projection-definition version, response `schema_version`, subject, purpose, authorization, classification ceiling, requested Event `stream_position`, and consistency requirement. Callers cannot request a projection that ignores later revocation/suspension for an operational decision.

`ProjectionResponse` contains source `stream_id`, last applied `stream_position`, Event-history integrity reference, projection-definition version, response `schema_version`, normative state with named `entity_revision`/business-content versions, governed external references and reconciliation status, presence/redaction semantics, and access audit reference. `ProjectionFailure` returns a stable code for gap, unknown schema, integrity mismatch, stale state, unavailable dependency, or classification denial.

A response is not authoritative independently of its validated source history. External domain content is referenced, not fabricated or claimed reconstructed.

Entity projections, including Role projections and filtered Event views, MUST be reproducible from the authoritative Organization stream. They MAY support entity-focused navigation and validation but MUST NOT expose or imply a separate authoritative per-entity Event history.

Role projection replay MUST validate every Organization Event envelope, supported type and version, payload contract, identity, stream, contiguous position, integrity, and disposition/audit lineage before advancing the projection. Unknown Event types, unsupported versions, malformed Events, and inconsistent history fail closed without returning a partially advanced authoritative projection. A recognized non-Role Event may be traversed only after that common validation.

`RoleActivated` is authoritative only within one complete ordered `CommandAccepted(ActivateRole v1) -> RoleActivated -> AuditLinked` sequence. The acceptance MUST identify the supported ActivateRole operation and version. All three Events MUST retain the same Organization, initiating Actor, recording Command, correlation, evaluation time, and audit identity; the activation causal Command reference MUST equal the recording Command and the activation MUST identify the same stable Role and its exact prior state and revision. `AuditLinked` MUST contain the immutable authenticated-admission evidence snapshot and that snapshot MUST bind the same canonical Organization, initiating Actor, and recording Command as the complete accepted sequence. An orphan activation, acceptance for another operation or version, mismatched Organization, Actor, recording Command, correlation, audit identity, or admission evidence, duplicated activation under one acceptance, incomplete sequence, or inconsistent audit link is corrupt history and MUST fail replay closed. This is the activation counterpart of the accepted CreateRole lineage already required for `RoleCreated`; neither domain Event is self-authorizing.

Role replay consumes the complete canonical Organization history, not a filtered Role-only history. Complete recognized accepted CreateTask transactions, accepted CreateRole transactions, and attributable rejection transactions MAY appear before, between, or after activation transactions; replay MUST validate their supported canonical disposition, domain, and audit lineage and traverse them without changing Role state. Pre-boundary rejections are non-authoritative and cannot appear in that history. Unknown, unsupported, malformed, or causally inconsistent Events are never projection-neutral and MUST fail replay closed.

When folding a valid `RoleActivated` sequence, replay MUST locate the Role by stable `role_id`, require the same Organization, current state `draft`, exact `prior_entity_revision`, and `entity_revision=prior_entity_revision+1`, then change only lifecycle state and entity revision. It MUST reject an activation for a nonexistent Role; an active, suspended, retired, archived, or otherwise non-draft Role; a mismatched prior or resulting revision; a duplicate or contradictory activation; or a mismatched Organization, stream, schema, payload version, or Event order. Replay performs no governance, Command handling, allocation, clock access, append, persistence mutation, or external effect.

An ordinary `ActivateRole` Command targeting the genesis-derived founding Role encounters the same already-active lifecycle rejection as any other active Role. Genesis history remains authoritative and MUST NOT be reinterpreted as an ordinary activation.

Canonical relationship protocol is implemented within PF-05 Projection and PF-16 Audit rather than as a new top-level family:

- `CanonicalRelationshipSnapshot` identifies relationship kind, canonical entity/Event references, named revisions/positions, Organization, subjects, effective state, and integrity;
- `InverseProjectionResponse` identifies its canonical source set and last applied stream position and declares itself derived and nonauthoritative;
- `RelationshipIntegrityComparison` compares canonical edges with inverse navigation edges without permitting the inverse to create truth;
- `RelationshipConflict` reports stale, forged, directly edited, missing, or conflicting inverse state and fails affected eligibility/authority closed; and
- `InverseProjectionRebuilt` proves replay-derived reconstruction from canonical entities and Events without authoritative mutation.

Role Assignment is authoritative for Actor-to-Role occupancy; Authority Grant for issuer, recipient, parent, child, and delegation edges; and Governing Body membership records and accepted Events for membership. An inverse list cannot create Role eligibility, Authority, delegation rights, membership, or voting eligibility. Equal-looking projections with conflicting canonical histories are not equivalent.

## 10. Replay family

`ReplayRequest` contains authorized Organization, source stream range, historical `specification_version`, record `schema_version`, `payload_version`, named business-content versions, Policy versions, projection versions, checkpoint references, expected integrity, and `execution_mode=replay_effect_prohibited`. `ReplayAuthorization` binds requester, purpose, current classification/disclosure authority, range, side-effect guards, and permitted output.

Every replay-family message includes `traffic_mode=replay`. A record with `traffic_mode=replay` is structurally prohibited from containing a live dispatch intent, live subscription delivery, Resource mutation request, Approval-use request, schedule materialization, external write, notification, charge, retry, or compensation.

`ReplayReport` contains applied range, Event count and integrity result, checkpoint decision, reconstructed projections/references, governed availability state, unknown historical version failures, external-reference limitations, side-effect counter proof, and zero new authoritative Command/Event identities. `ProjectionComparison` reports semantic equivalence, permitted metadata differences, canonical relationship comparison, and exact divergence position.

Replay applies later redaction, deletion, sealing, access restriction, tombstone, cryptographic erasure, and reclassification Events. `GovernedAvailabilitySnapshot` preserves minimum lawful Event identity, stream position, provenance, integrity reference, classification history, accountability metadata, and nonreconstructive tombstone/erasure state. Replay MUST NOT restore erased content, retrieve inaccessible content, disclose currently restricted content, treat historical access as current disclosure authority, or pretend to reconstruct an opaque external system. Historical schema and payload semantics govern Event interpretation; current disclosure and governance controls govern present access.

## 11. Subscription family

`SubscriptionRequest` contains stable subscription identity, subscriber Actor/Service and invocation proof, one Organization, Event-type/subject scope, classification ceiling, purpose, filter type/version, starting cursor, delivery constraints, expiry/review, and Grant/Policy references.

Authorization produces exact scope or rejection; the kernel MUST NOT broaden a filter. `SubscriptionDelivery` contains a stable delivery identity, original Event identity and position, subscription/filter versions, redaction/classification decision, delivery attempt number, and replay/live mode. Delivery order is transport observation and does not create Event authority; source position controls. Redelivery increments attempt count but preserves Event and delivery-operation identity and creates no new Event.

Acknowledgment records delivery identity, subscriber identity, received Event identity/position, disposition, and checkpoint proposal. Rejection/suspension identifies reason and safe cursor. `CursorCheckpoint` is attributable, monotonic within the subscription, and cannot skip an unacknowledged gap without explicit Policy. Subscribers cannot mutate source Events.

## 12. Scheduling family

Scheduling strategy, priority selection, sequence optimization, recurrence design, planning, and Task decomposition are outside the kernel protocol. PF-08 governs schedule admission, persistence, activation, suspension, cancellation, due observation, trigger deduplication, materialization, timeout, expiry, missed-run handling under declared Policy, and current-state revalidation. The kernel MUST NOT invent priorities, reorder work, alter recurrence strategy, or choose planning strategy.

Distinct record types are:

- `ScheduleDefinition`: stable series identity, proposing/planning Actor references, authorizing accountable Decision, technical recorder, Work Root or governed lifecycle subject, recurrence/trigger semantics supplied by the organization, bounds, Resources, Approval, target, catch-up Policy, cancellation and review conditions;
- `ScheduleActivated`, `ScheduleSuspended`, and `ScheduleCancelled`: lifecycle transition with recording Command, current gates, reason, and effective time;
- `ScheduleDueObserved`: timer/deadline observation with source and bound kernel evaluation time, not permission;
- `ScheduleInstanceMaterialization`: distinct stable instance/operation identity, series identity, due identity, new attributable Command, scheduler Service as technical initiator, original proposer/decider/approval references, current Work Root, and every revalidated gate;
- `MissedInstanceDisposition`: `skipped`, `paused`, `escalated`, or `catch_up_proposed`, never guessed execution; and
- `CatchUpDisposition`: bounded authorized instances and current Decision/Approval/Resource checks.

Each due schedule produces a new attributable Command before work or dispatch. Materialization revalidates current Actor status, Role Assignment, Authority, Policy, Work Root, Approval, Resources, lifecycle, suspension, Incident controls, and stop conditions. Each legitimate instance has a distinct identity. `ScheduleTriggerDisposition` binds series, due identity, instance identity, and Actor-scoped idempotency: exact duplicate triggers return the original materialization; conflicting triggers deduplicate, pause, or reconcile and never execute twice. A schedule cannot provide or preserve missing, expired, revoked, stale, exhausted, or cancelled authority or conditions. A scheduler Service is only the technical initiator, not automatically planner, accountable decider, approver, or authority source.

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

`ApprovalReferenceSnapshot` contains Approval ID and `entity_revision`, Decision ID and `decision_content_version`, mode, permitted action/Resource/risk/budget scope, `used_count`, `usage_limit` presence, effective/expiry, revocation state, conditions, review schedule, approvers, named Policy content versions, and integrity.

`ApprovalUseValidation` records current Authority separately, Decision `decision_content_version` and `entity_revision`, every condition, material-change result, separation of duties, current bound time, remaining use, and result. A successful validation is not Authority.

`ApprovalUseRecorded` is an atomic append transition with use ID, Command, Approval `entity_revision`, mode, prior/next monotonic `used_count`, exact operation scope, and Event/audit references. `single_use` moves 0→1; `bounded_repeat` increments below its positive limit; `standing` records each narrowly scoped current A2 use. Usage never decrements, including uncertain external outcomes. A4 standing use and unspecified A3 standing use are invalid.

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

Protected-reference and memory lifecycle records carry `GovernedAvailabilitySnapshot` links so later sealing, access restriction, reclassification, deletion, redaction, tombstone, or cryptographic erasure changes availability without rewriting accepted history. A resolver MUST enforce current disclosure authority and MUST NOT return content merely because an older Event or audit record referenced it.

Retrieval ranking or model output cannot change Record validity, classification, authority, or lifecycle. Unadmitted output is not institutional memory.

## 18. Audit-reference family

`AuditReference` is a stable identifier with explicit `schema_version`, audit `entity_revision` or named content version, and integrity for a protected or visible audit segment. A consequential trace references one Work Root, recording Command, initiating and participating Actors, proposer/recommender, accountable decider, approvers, technical recorder, Role Assignment, Grant/delegation, Policy versions, Evidence, Decision, Approval uses, Tool stages, Resources, causal references, outcomes, reconciliation, metrics, and Incident as applicable.

`DecisionGovernanceSnapshot` records Decision lifecycle state separately from `ExecutionEligibilityEvaluation`. The latter records bound evaluation time and current Actor/Role Assignment, Authority, Policy, Approval, Work Root, Resource, evidence-validity, risk/scope, lifecycle, suspension, Incident, and stop-condition results. `governance_conditions_satisfied` does not imply current eligibility. `executed` links an attempted Action and does not imply verified external success. Material changes after Decision or Approval require a fresh evaluation and may reject, pause, invalidate, or escalate.

`DecisionOutcomeLink` preserves authorization, dispatch, attempt, observation, adapter interpretation, reconciliation, failure, partial, disputed, and verified states separately. It can represent an attempted Action with uncertain, failed, partial, or disputed outcome without changing the historical Decision disposition.

Protected content uses `ProtectedAuditReference` with classification, authorized resolver, integrity, provenance, and safe description. `AuditCompletenessResult` lists required, present, withheld, missing, invalid, and unresolved links. Missing mandatory linkage blocks consequential completion; the protocol MUST NOT substitute human-readable narrative.

## 19. Bootstrap family

`BootstrapRequest` is explicitly pre-Organization and declares `admission_basis=constitution_direct`, `genesis_exception=sole_preexisting_authority_exception`, and a reserved genesis Command type and Event types or equivalently explicit reserved classification. It contains message/family/schema versions; proposed stable Organization identity; verified initiating Human and proof; that Human as accountable decider for the founding Decision; constitutional owner/governor Role; founding Role Assignment; founding Decision with complete constitutional duty; initial Authority Grants; genesis recording Command; complete proposed founding Event set; Audit Record references; expected nonexistent/empty stream condition; Actor-scoped genesis idempotency identity; and deterministic competing-genesis conflict rule.

`BootstrapCommitted` atomically returns the Organization, Human Actor, Role, Role Assignment, founding Decision, Grants, recording Command, consecutive founding Events/positions, Audit Record identities, original evaluation time, and `genesis_exception_exhausted=true`. No component is visible operationally before the whole outcome commits. `BootstrapPreviouslyAdmitted` is the exact-retry outcome and returns the original complete disposition, identifiers, positions, evaluation time, and integrity linkage without creating a second founding set.

`BootstrapRejected` creates no operational Organization. `BootstrapUncertain` records an integrity state, quarantines the proposed identity, prohibits blind retry and competing identity establishment, requires reconciliation, and prevents any partial state from being used operationally. A materially different or competing genesis attempt rejects with a stable code or follows the declared deterministic constitutional rule without merging founding claims.

Bootstrap structurally prohibits ordinary operational work, Employee or Temporary Worker creation, subscriptions, Tool invocations, ordinary Resource consumption, ambiguous/unreserved genesis types, AI accountable-decider attribution, and reuse of genesis authority after establishment. A model, Tool, Employee, or fictional Human body cannot occupy the verified founding Human or accountable-decider field.

## 20. Operational-control family

- `SuspensionRequest/Applied/Rejected`: exact affected scope, Incident, stop basis, authority, evidence, immediate prevented operations, review owner, and restoration conditions;
- `CancellationRequest/Applied`: future work prevented, in-flight state, reservations, Approval use, external uncertainty, compensation/reconciliation, and audit;
- `TimeoutObserved`: deadline, expected observation, bound time, source, uncertain state, and prohibited success/failure implication;
- `RetryRequest/Disposition`: original operation identity, new attempt identity where applicable, nonexecution/idempotency/duplicate-risk evidence, current gates, limit, reservation, Decision/Approval, and reason;
- `EscalationRequest/Disposition`: exact unresolved issue, safe default, Evidence, eligible accountable-decider Actor or Governing Body, proposer/recommender, technical initiator/recorder, separately required approvers, Decision sought, deadline, and nonresponse semantics.

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

`defined → active|suspended|cancelled → due_observed → trigger_deduplicated|trigger_conflicted|materialization_proposed → materialized|missed|paused|rejected|reconciling → dispatched|cancelled|catch_up_proposed`.

Series suspension/cancellation prevents future materialization; it does not erase existing instances. Exact trigger redelivery preserves the original instance and disposition; conflict never silently produces a second execution.

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

The initial registry contains 66 immutable machine keys formatted `CATEGORY.SPECIFIC_CAUSE`. For every registry row, the component before the period is its explicit normative `category` field and the complete code is its stable identifier. Human-readable `safe_detail` is bounded, localizable, nonauthoritative, and MUST NOT be used for branching. Each failure record also contains `retryability` (`never`, `after_change`, `idempotent_only`, `after_reconciliation`), `reevaluation` (`no`, `allowed`, `required`), `escalation` (`none`, `conditional`, `required`), `incident` (`no`, `consider`, `required`), safe disclosure class, and conformance scenario references.

| Code | Meaning | Retryability / reevaluation | Escalation / Incident | Safe disclosure | Conformance |
|---|---|---|---|---|---|
| `INPUT.MALFORMED` | Required structure/type invalid | never / no | none / consider | Field path without protected value | CMD-002, ADV-015 |
| `INPUT.OVERSIZED` | Size/depth bound exceeded | after_change / allowed | conditional / consider | Limit class only | ADV-015 |
| `VER.UNSUPPORTED` | Family/record/payload version unknown | after_change / required | conditional / no | Supported ranges | CMD-003 |
| `VER.DOWNGRADE_REJECTED` | Offered version would weaken semantics | after_change / required | conditional / consider | Version ranges | ADV-009 |
| `IDENTITY.UNKNOWN` | Actor cannot be resolved | after_change / required | conditional / consider | Do not reveal other identities | CMD-005 |
| `IDENTITY.FORGED` | Invocation proof does not bind Actor | never / no | required / required | Minimal security detail | ADV-016 |
| `IDENTITY.SUSPENDED` | Actor operationally suspended | after_change / required | conditional / consider | Suspension reference if authorized | CMD-006 |
| `ORG.UNKNOWN` | Claimed Organization cannot be resolved as an authoritative completed-genesis boundary | after_change / required | conditional / consider | Generic boundary unavailable; do not disclose existence | ADB-003, ADB-004, ADB-020 |
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
| `WORK_ROOT.INVALID_KIND` | Project, Objective, or another non-Goal/non-duty type claimed as Work Root | after_change / required | none / no | Invalid kind only | WRT-010 |
| `DECISION.MISSING` | Consequential Decision absent | after_change / required | required / no | Decision class required | AUD-009 |
| `DECISION.INCOMPLETE` | Mandatory Decision/audit fields absent | after_change / required | required / consider | Missing field categories | AUD-006, AUD-009 |
| `DECISION.ACCOUNTABLE_DECIDER_INVALID` | Human-reserved disposition lacks eligible Human/body accountable decider | after_change / required | required / consider | Required decider class, no protected member data | AUT-015, BST-011 |
| `DECISION.CURRENT_CONDITIONS_INVALID` | Historical Decision state no longer satisfies current execution conditions | after_change / required | conditional / consider | Changed condition categories | AUD-013, AUD-015 |
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
| `EVENT.FIELD_APPLICABILITY_INVALID` | Required/optional/not-applicable semantics are missing, unresolved, or simulated by placeholder | after_change / required | conditional / consider | Field path and applicability class only | EVT-010 |
| `EVENT.PROHIBITED_FIELD` | Field prohibited by selected Event schema is present, even empty | after_change / required | conditional / consider | Field path only | EVT-010 |
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
| `BOOTSTRAP.INCOMPLETE` | Proposed founding set is incomplete before authoritative commit | after_change / required | required / consider | Missing categories, no protected content | BST-004 |
| `BOOTSTRAP.GENESIS_TYPE_INVALID` | Command/Event type or classification is not reserved unambiguous genesis | after_change / required | required / consider | Required genesis class | BST-012 |
| `BOOTSTRAP.GENESIS_SCOPE_INVALID` | Genesis includes ordinary work/effects or reuses exhausted exception | never / no | required / required | Prohibited scope category | BST-005, BST-010 |
| `BOOTSTRAP.IDENTITY_QUARANTINED` | Proposed identity has uncertain or partial authoritative genesis state | after_reconciliation / required | required / required | Quarantine identity only | BST-002 |
| `BOOTSTRAP.COMPETING_GENESIS` | Materially different founding attempt conflicts with registered genesis | never / no | required / required | Conflict class, no other founding data | BST-007 |
| `INCIDENT.SUSPENDED` | Incident control blocks operation | after_change / required | required / already linked | Incident ref if authorized | OPS-001, SCH-006 |
| `OPERATION.TIMEOUT` | Required observation absent by deadline | after_reconciliation / required | conditional / consider | Deadline and subject | OPS-005 |
| `OPERATION.CANCELLED` | Future operation cancelled | never / no | none / no | Cancellation reference | OPS-003, SCH-010 |
| `RETRY.PROHIBITED` | Retry lacks proof/idempotency/approved risk | after_change / required | required / consider | Required evidence class | OPS-007, OPS-008 |
| `GOVERNANCE.DEPENDENCY_UNAVAILABLE` | Identity/authority/classification/audit dependency unavailable | after_change / required | required / consider | Dependency class only | ADV-010, ADV-011, ADV-021, ADV-022 |
| `INTEGRITY.VERIFICATION_FAILED` | Integrity proof/checkpoint/history invalid | after_change / required | required / required | Position/reference, no protected data | ADV-008, RPL-008, RPL-009 |
| `RELATIONSHIP.INTEGRITY_CONFLICT` | Derived inverse relationship conflicts with canonical entity/Event state | after_change / required | required / required | Relationship kind and protected canonical ref | REL-001–REL-006 |
| `CONTENT.GOVERNED_UNAVAILABLE` | Current governed availability forbids or cannot provide referenced content | after_change / required | conditional / consider | Tombstone/classification state, never content | RPL-013, RPL-015 |
| `CONTENT.CRYPTOGRAPHICALLY_ERASED` | Referenced content was cryptographically erased and is nonreconstructive | never / no | conditional / consider | Erasure/tombstone reference, never content | RPL-014 |
| `SCHEDULE.TRIGGER_CONFLICT` | Trigger conflicts with registered instance or materialization identity | after_reconciliation / required | conditional / consider | Series/instance reference if authorized | SCH-015 |

Codes are never repurposed. New codes are additive within a compatible version only when old consumers can safely treat the category as failure. Human text changes do not change machine semantics.

## 23. Security and isolation requirements

The receiver MUST enforce:

1. trusted envelope fields take precedence structurally; conflicting payload echoes reject the message;
2. every typed reference resolves within the one Organization or an explicit governed cross-Organization relationship;
3. classification may be raised on validation but never downgraded by caller, filter, payload, adapter, or replay;
4. Actor, Approval, Authority, Tool-result, and adapter references require integrity-bound resolution, not identifier existence alone;
5. subscription filters are versioned, bounded predicates applied after Organization/purpose/classification authorization and cannot request hidden fields;
6. replay mode and live mode are disjoint types at the adapter boundary; live adapters reject replay traffic even if misrouted;
7. mutating idempotency keys are scoped by Organization, initiating Actor, and operation family and bind the original operation identity and material semantics; equality must not reveal another Actor's or Organization's registration;
8. input size, nesting, collection count, reference count, and expansion are bounded before authoritative parsing or effect;
9. type names are stable registry values, not caller-defined aliases; ambiguous or downgraded schemas reject;
10. human-readable failure detail is bounded, classified, and never includes protected target existence, secrets, raw payloads, or cross-Organization state;
11. external clocks are observations; kernel-bound `evaluation_time` and `stream_position` control admission and order; and
12. platform-security telemetry cannot become an Organization Event or authoritative state without a later valid Command; and
13. ordinary Organization stream access, Organization idempotency, authoritative audit, and identifier allocation require an exact `AdmissionEstablished` proof bound to the Command attempt.

## 24. Conformance traceability

This matrix maps all 20 protocol families to the final 277 mandatory scenarios across 19 suites in `KERNEL_CONFORMANCE.md`; it does not duplicate their definitions. The authenticated recording-boundary contract is part of PF-01 Command and PF-02 disposition. PF-05 and PF-16 implement the canonical relationship records and PF-03 supplies their accepted Event history, together covering REL.

| Families | Primary conformance suites |
|---|---|
| PF-01 Command, PF-02 disposition | ADB, CMD, AUT, WRT, APR, RES, AUD, BST, ADV |
| PF-03 Event, PF-04 append | EVT, CMD, APR, RES, REL, RPL, ADV |
| PF-05 Projection | EVT, REL, RPL, POR, MEM, ADV |
| PF-06 Replay | RPL, REL, MEM, POR, ADV |
| PF-07 Subscription | SUB, RPL, ADV |
| PF-08 Scheduling | SCH, OPS, AUT, WRT, APR, RES, LIF, AUD, ADV |
| PF-09 Tool dispatch, PF-10 attempt, PF-11 result | TOL, OPS, AUD, RES, ADV |
| PF-12 Reconciliation | TOL, RES, OPS, AUD, ADV |
| PF-13 Resource | RES, APR, TOL, SCH, ADV |
| PF-14 Approval use | APR, CMD, SCH, TOL, ADV |
| PF-15 Memory | MEM, AUD, RPL, ADV |
| PF-16 Audit | AUD, REL, CMD, TOL, MEM, RPL, ADV |
| PF-17 Bootstrap | BST, AUT, EVT, AUD, ADV |
| PF-18 Operational control | OPS, LIF, SCH, TOL, ADV |
| PF-19 Version negotiation | CMD, EVT, RPL, POR, ADV |
| PF-20 Failure | Every negative suite scenario and ADV |

## 25. Symbolic logical examples

These examples show logical fields and relationships. Braces and arrows are explanatory notation, not an encoding.

### 25.1 Accepted Command

`CommandSubmission { message_id=msg:cmd:41, command_id=cmd:alpha:41, original_operation_id=op:alpha:41, organization_id=org-alpha, initiating_actor_id=employee-operator, invocation_proof_reference=proof:41, work_root=Goal(goal:launch), planning_references=absent_optional, operation_family=artifact, operation_type=artifact.review, expected_entity_revision=7, grant=grant:a2:active, approval_references=absent_optional, resources={compute:2}, idempotency_key=review/41 }`

`AdmissionAccepted[msg:disp:41] { command=cmd:alpha:41, evaluation_time=T100, events=[evt:reserve:41@P88, evt:task-started:41@P89], next_step=employee_work }` (a verified external outcome field is prohibited on acceptance).

### 25.2 Rejected Command

`AdmissionRejected[msg:disp:42] { command=cmd:alpha:42, reason=AUTH.EXPIRED, failed_gate=authority, effects=intentionally_empty, safe_detail="asserted grant expired at bound evaluation time" }`

### 25.3 Exact duplicate Command

`CommandSubmission { organization_id=org-alpha, initiating_actor_id=employee-operator, operation_family=artifact, idempotency_key=review/41, command_id=cmd:alpha:41, same material semantics } → AdmissionPreviouslyAdmitted { original=msg:disp:41, evaluation_time=T100, event_ids=[evt:reserve:41,evt:task-started:41], positions=[P88,P89], resource_effects=original, approval_use=original, dispatch_identity=none }`

The same textual key used by `employee-router` has a distinct Actor scope and reveals nothing about `employee-operator`; reuse by `employee-operator` with different material semantics returns `IDEMPOTENCY.CONFLICT` while preserving the original registration.

### 25.4 Atomic append batch

`AppendProposal[append:51] { expected_position=P90, ordered=[reservation, approval_use, dispatch_intent], preconditions={task_version:8} } → AppendCommitted { positions=[P91,P92,P93], all_or_none=true }`

### 25.5 Tool attempt followed by unknown outcome

`AuthorizedToolDispatchIntent[dispatch:7] → AdapterReceipt[receipt:7] → ToolExecutionAttempt[attempt:7] → TimeoutObserved { response=not_yet_known } → ReconciliationDisposition { state=unresolved, approval_use_restored=false, reservation=held_safe_bound }`

### 25.6 Contradictory Tool callbacks

`ExternalResponseObservation[obs:7a, result=completed] + ExternalResponseObservation[obs:7b, result=denied] → ReconciliationDisposition { state=disputed, evidence=[obs:7a,obs:7b], verified_outcome=not_yet_known }`

### 25.7 Standing Approval use

`ApprovalUseValidation { approval=approval:standing:a2, authority=grant:a2:active, review=current, scope=matched, prior_count=12 } → ApprovalUseRecorded { use=use:13, prior=12, next=13, operation=bounded_recurring_a2 }`

### 25.8 Scheduled instance materialization

`ScheduleDueObserved[due:series9:instance4] → ScheduleInstanceMaterialization { series=series9, instance=instance4, command=cmd:schedule:instance4, initiating_actor_id=service-scheduler, technical_role=scheduler_only, accountable_decider=human-ops-owner, work_root=Duty(maintenance), revalidated=[actor,role_assignment,authority,policy,work_root,approval,resources,lifecycle,suspension,incident,stop_conditions] }`

### 25.9 Classified subscription delivery

`SubscriptionDelivery[delivery:77] { subscription=sub:restricted, event=evt:alpha:P120, classification=restricted, payload=withheld(restricted,protected:evt120), redelivery_count=0 }`

### 25.10 Replay report proving zero effects

`ReplayReport[replay:3] { mode=replay, range=P0..P120, projection=equivalent, external_references=reconstructed_only, governed_availability=reconstructed, tool_calls=0, communications=0, charges=0, approval_mutations=0, new_events=0 }`

### 25.11 Uncertain append requiring reconciliation

`AppendUncertain[append:52] { expected=P120, proposed_event_bindings=[a,b], retry_prohibited=true } → ReconciliationRequest { inspect_stream_by_idempotency=true } → AppendCommittedConfirmed|NonappendConfirmed|UncertainEscalated`

### 25.12 Atomic bootstrap

`BootstrapRequest[bootstrap:alpha] { admission_basis=constitution_direct, genesis_type=reserved, proposed_org=org-alpha, verified_human=human-owner-alpha, accountable_decider=human-owner-alpha, role=constitutional-owner, assignment=founding, decision=decision:founding, duty=constitution:establish, grants=[grant:founding], recording_command=cmd:genesis:alpha, events=[genesis.organization_created,...], audit=audit:genesis:alpha, expected_stream=nonexistent, idempotency=bootstrap/alpha } → BootstrapCommitted { all_entities_and_events_atomic=true, genesis_exception_exhausted=true, operational=true }`

### 25.13 Event applicability controls

- Valid mechanical: `EventRecord[type=RoleAssignmentActivated] { common_envelope=complete, epistemic_status=not_applicable(schema_permitted) }`; confidence, Evidence, and result are absent because this schema prohibits them.
- Valid consequential: `EventRecord[type=ActionOutcomeObserved] { common_envelope=complete, resources=[resource:compute], evidence=[evidence:receipt], result=partial, epistemic_status=observed, confidence=known(organization_scale:0.8) }`.
- Missing required: `ActionOutcomeObserved { evidence=absent } → EVENT.FIELD_APPLICABILITY_INVALID`.
- Prohibited present: `RoleAssignmentActivated { confidence=known(1.0) } → EVENT.PROHIBITED_FIELD`.
- Ceremonial placeholder: `ActionOutcomeObserved { evidence=[], result="generic", confidence=1.0 } → EVENT.FIELD_APPLICABILITY_INVALID`.

### 25.14 Human accountable decider

Accepted: `GovernanceRoleAttribution { proposer=employee-analyst, recommender=employee-analyst, accountable_decider=human-governor, approver=human-reviewer, technical_recorder=employee-router }` with independently valid Decision and Approval.

Rejected: `GovernanceRoleAttribution { accountable_decider=employee-analyst, approver=human-governor, decision_class=A4 } → DECISION.ACCOUNTABLE_DECIDER_INVALID`; the Approval does not cure the Decision.

### 25.15 Bootstrap retry, conflict, and quarantine

`exact BootstrapRequest[bootstrap:alpha] → BootstrapPreviouslyAdmitted { original_disposition, identifiers, positions, evaluation_time }`; `different founding Human or data → BOOTSTRAP.COMPETING_GENESIS`; `accountable_decider=employee-founder → DECISION.ACCOUNTABLE_DECIDER_INVALID`; `unreserved type → BOOTSTRAP.GENESIS_TYPE_INVALID`; `uncertain partial append → BootstrapUncertain { proposed_org=quarantined, retry=after_reconciliation }`.

### 25.16 Canonical relationship authority

`CanonicalRelationshipSnapshot { kind=role_occupancy, source=RoleAssignment:ra7@entity_revision3 } + InverseProjectionResponse { actor_roles=[role-operator,role-forged] } → RelationshipConflict { reason=RELATIONSHIP.INTEGRITY_CONFLICT, eligibility=fail_closed }`.

### 25.17 Direct Work Roots and optional planning

Valid: `TaskSubmission { work_root=Goal(goal:launch), project/objective/plan=absent_optional }` and `TaskSubmission { work_root=Duty(type=maintenance, mandate=policy:ops, owner=human-ops, scope=backup, completion=verified), project/objective/plan=absent_optional }`. Invalid: `TaskSubmission { work_root=Project(project:launch) } → WORK_ROOT.INVALID_KIND`.

### 25.18 Duplicate schedule trigger

`ScheduleDueObserved[due:9] → materialization[instance:9]`; exact redelivery returns the original instance and Command, while a conflicting trigger binding returns `SCHEDULE.TRIGGER_CONFLICT` and pauses or reconciles without dispatch.

### 25.19 Replay after cryptographic erasure

`Event[P40 references protected:artifact7] → CryptographicErasure[P90, tombstone=tomb:artifact7] → ReplayReport { reference=protected:artifact7, availability=erased, availability_reason=CONTENT.CRYPTOGRAPHICALLY_ERASED, tombstone=tomb:artifact7, content=prohibited_absent, current_disclosure=false, external_system_reconstructed=false }`.

### 25.20 Decision-state revalidation

`DecisionGovernanceSnapshot { state=governance_conditions_satisfied, authority_at_decision=grant:a3 } + ExecutionEligibilityEvaluation { current_authority=expired } → DECISION.CURRENT_CONDITIONS_INVALID`; `Decision { state=executed } + ActionOutcome { state=disputed }` remains attempted and disputed, never verified success.

### 25.21 Collective Governing Body

`GoverningBodyDisposition { body=board:alpha, membership_snapshot=members@P120, human_dispositions=[vote:h1:consent,vote:h2:dissent,vote:h3:recusal], eligibility_bases=[...], quorum_rule=quorum:v3, voting_policy=policy:board:v8, derived_result=accepted, technical_initiator=service-recorder }`; no fictional Human represents the body.

## 26. Protocol conformance requirements

A conforming implementation MUST demonstrate through `KERNEL_CONFORMANCE.md` that:

- every family/type/version and presence state maps to its logical contract;
- caller-controlled data cannot populate or override kernel-bound facts;
- all authoritative mutations have one recording Command and immutable Event linkage;
- live, replay, observation, and platform-security modes are structurally separated;
- exact duplicates preserve the original disposition, identifiers, positions, evaluation time, Resource/Approval effects, and dispatch identity; conflicting reuse fails closed within the Organization/initiating-Actor/operation-family scope;
- append, Resource reservation, Approval use, audit linkage, and dispatch intent are atomic where required;
- Tool knowledge and append certainty preserve unknown/uncertain states;
- reason codes, not human text, drive machine behavior; and
- exports retain enough semantic and version evidence for replay and portability.

Failure to understand a type, version, presence state, reason code category, classification, integrity proof, or governed reference MUST fail closed. Protocol convenience cannot expand constitutional authority or weaken institutional accountability.
