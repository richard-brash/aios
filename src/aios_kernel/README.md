# AIOS ordinary kernel runtime

This package supplies the authenticated ordinary-command kernel boundary and a
deterministic `CreateTask` capability. `CreateTaskCommand` is a `RuntimeCommand`;
the public execution path is `KernelRuntime.execute`. There is no independent
CreateTask admission or persistence API.

CreateTask idempotency uses an explicit semantic logical identity rather than a
Python representation. It includes every caller-supplied command field except
the delivery-only envelope `message_id`, preserves typed identifiers and ordered
sequences, and canonicalizes mapping order. SHA-256 is applied to a private,
nonnormative deterministic encoding; no wire encoding is selected. The atomic
store boundary rechecks and registers this fingerprint with the Event and audit
batch. Exact and conflicting registrations cannot be overwritten.

The runtime store checks idempotency and stream concurrency before it invokes a
deterministic deferred transaction builder. Consequently, an exact duplicate,
conflicting fingerprint, or concurrency conflict
creates no candidate records and allocates no disposition, audit, or Event IDs.
Only a new, concurrency-valid registration reaches deferred materialization,
which allocates through the injected allocator and returns the complete batch.
The callback is a reference implementation technique, not a normative API.
Infrastructure failure after the builder runs may consume allocator values even
when nothing commits; this slice intentionally provides no identifier rollback.

An accepted CreateTask execution records, atomically and in Organization order:
`CommandAccepted`, `TaskCreated`, `DecisionLinked`, `WorkRootLinked`, and
`AuditLinked`. Governance or handler rejection after admission records
`CommandRejected` and `AuditLinked`. Both paths retain the validated immutable
`AdmissionEvidenceSnapshot`; pre-boundary rejection records nothing.

This package is not a complete kernel and does not assign or execute Tasks. It
contains no API, database, file persistence, queue, network calls, Tool adapter,
scheduler or subscriber runtime, memory retrieval, agent, model, background
worker, authentication store, or production authorization implementation.
Importing it performs no I/O, clock access, identifier allocation, environment
inspection, thread creation, or global state mutation.

Focused kernel tests map observable runtime behavior to the applicable
`KERNEL_CONFORMANCE.md` scenarios. Passing them demonstrates only this narrow
slice; it does not imply full operational or overall kernel conformance.

## Capability-neutral runtime skeleton

`aios_kernel.runtime` supplies the minimum forward runtime boundary without
adding a business capability. Its explicit execution sequence is:

1. validate structure, live traffic, schema, operation, and operation version
   without Organization effects (support-resolution Model A);
2. pass the exact immutable `AdmissionClaim` to the injected trusted
   `RecordingBoundaryResolver`;
3. after `AdmissionEstablished`, bind its canonical Organization and Actor,
   then read history, inspect Organization/Actor-scoped idempotency, and check
   the expected Organization position;
4. invoke authorization governance and then the deterministic handler; and
5. atomically record acceptance/domain/audit Events or an attributable
   rejection/audit sequence through deferred materialization.

Malformed or unsupported input and `AdmissionDenied` return a typed
non-recorded rejection. They read no Organization stream, inspect no
Organization idempotency state, allocate no authoritative identifier, and
invoke neither governance nor handling. A syntactically valid identifier is not
boundary proof. Establishment binds completed genesis, exact stable Organization
and Actor identities, invocation proof, and immutable authentication evidence.
It authenticates attribution but grants no Authority; governance remains the
separate authorization boundary. Handlers receive canonical identities but no
authentication-provider evidence.

Future capability handlers implement `CommandHandler` and return immutable
`DomainEventProposal` values. They do not assign Event identity or ordering and
must not perform kernel governance. Time and identifiers come from the existing
`Clock` and `IdentifierAllocator` ports; the runtime contains no defaults or
ambient service lookup. Handler registration is an explicit constructor value.
Accepted and attributable rejected outcomes record their audit identity, outcome,
immutable facts, and a frozen snapshot of the validated admission proof in
`AuditLinked`, so history retains the canonical Organization and Actor,
invocation-proof binding, referenced authentication evidence, and admission
mechanism identity and version without persisting provider internals or secret
material. Pre-boundary rejection remains non-authoritative and has no audit
record or admission-evidence snapshot.
An append race returns before the builder runs and therefore cannot allocate IDs
or overwrite accepted history.

Runtime exact redelivery is scoped by the admitted canonical Organization,
admitted Actor, operation family, and idempotency key. Its semantic fingerprint
includes all material ordinary Command facts, including
`invocation_proof_reference`, while excluding only delivery `message_id`.
Admission denial never registers or inspects this state. Atomic append rechecks
both idempotency and the authoritative Organization position before invoking the
deferred builder, so duplicates, conflicts, and append races cannot allocate or
partially record authoritative data. Bootstrap remains on its distinct reserved
pre-Organization constitutional path and never uses this ordinary resolver.

`replay` folds an already ordered Event stream through a supplied pure
`ProjectionReducer`. It neither submits Commands nor invokes handlers,
governance evaluation, adapters, or other effects. The in-memory runtime store
under `reference/` is deterministic test support only.

This skeleton deliberately defers complete governance implementations,
production persistence, projection catalogs, domain
capabilities, scheduling, subscriptions, Tools, memory retrieval,
networking, agents, and models. It is a foundation for those separately governed
increments, not a claim of full kernel conformance.

## Constitutional bootstrap runtime

`aios_kernel.bootstrap_runtime` is a separate pre-Organization path; it does not
register a handler in the ordinary Organization-scoped `KernelRuntime`. Its
fixed sequence is:

1. reject non-`BootstrapRequest` input before constitutional evaluation;
2. bind one timezone-aware evaluation time from the injected Clock;
3. validate protocol, schema, reserved-genesis, direct-Constitution, founding
   Human, Role Assignment, duty, Organization attributes, initial Grants, and
   semantic Event coverage;
4. preserve the request as a `BootstrapProposal` and produce a typed accepted or
   rejected constitutional Decision;
5. compare the complete candidate against any registered attempt;
6. for a new accepted candidate on an empty stream, invoke deferred Event
   materialization through the injected identifier allocator;
7. atomically publish the entire ordered founding Event set and exact-redelivery
   registration, or publish neither;
8. reconstruct `FoundedOrganizationState` solely from the recorded Events.

The reference stream identity is deterministically derived from the proposed
Organization identifier. Exact request redelivery returns the original committed
outcome and allocates or appends nothing. A material difference is a competing
genesis and fails closed. Precommit uncertainty quarantines the identity using
internal reconciliation metadata without publishing founding Events.

The proposed Event type strings form a non-normative reference vocabulary.
Runtime acceptance depends on `FoundingEventCoverage` and matching immutable
payload facts, not those names. This permits different conforming vocabularies
and Event granularity without weakening founding completeness.

`replay_genesis` validates ordered, single-genesis history and reconstructs the
Organization, verified Human, Constitution, Mission, jurisdiction, retention
Policy, founding Role and Assignment, founding Decision and duty, initial
Grants, audit identity, recording Command, request integrity, and completion.
Replay obtains no time or identifiers and invokes neither evaluation nor
recording.

Every committed founding Event also carries the same immutable
`CommittedGenesisEvidence`: supported protocol versions, direct-Constitution
basis, exhausted genesis exception, request/proposal/Decision integrity
references, reserved recording Command, semantic coverage, and per-Event
declarations. The atomic reference store runs `replay_genesis` against the
candidate batch before publication. Command-time acceptance and replay therefore
enforce the same history-owned constitutional relationships without consulting
the submitted request, evaluator, exact-redelivery registration, or mutable
store state. Concrete reference Event names remain non-normative; the recorded
declarations and semantic coverage bind the vocabulary used by that history.

This slice still does not provide production identity verification, general
governance or Policy infrastructure, production persistence, distributed
consensus, reconciliation execution, or any ordinary post-genesis Organization
capability.
