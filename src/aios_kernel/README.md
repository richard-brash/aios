# AIOS kernel CreateTask admission slice

This package is the first behavioral AIOS kernel reference. It deterministically
admits or rejects exactly one operation: `CreateTask`, producing a proposed Task
under an active Goal Work Root. It depends on `aios_protocol` for canonical
logical records.

The core binds an injected evaluation time, coherent immutable snapshot, and
evidence-bearing governance results; evaluates the fixed kernel-contract gate
order; constructs immutable Events and audit linkage; and submits one atomic
transaction. Reference adapters under `reference/` exist only for deterministic
tests and are not production infrastructure.

CreateTask idempotency uses an explicit semantic logical identity rather than a
Python representation. It includes every caller-supplied command field except
the delivery-only envelope `message_id`, preserves typed identifiers and ordered
sequences, and canonicalizes mapping order. SHA-256 is applied to a private,
nonnormative deterministic encoding; no wire encoding is selected. The atomic
store boundary rechecks and registers this fingerprint with the Event, audit,
projection, Resource, and Approval mutations. Duplicate, conflicting, and
uncertain registrations cannot be overwritten.

The atomic store checks idempotency and stream concurrency before it invokes a
deterministic deferred transaction builder. Consequently, an exact duplicate,
conflicting fingerprint, uncertain prior registration, or concurrency conflict
creates no candidate records and allocates no disposition, audit, or Event IDs.
Only a new, concurrency-valid registration reaches the builder, which allocates
through the injected allocator and returns the complete immutable transaction.
The callback is a reference implementation technique, not a normative API.
Infrastructure failure after the builder runs may consume allocator values even
when nothing commits; this slice intentionally provides no identifier rollback.

Uncertain transaction results distinguish possible authoritative organizational
mutation, internal reconciliation metadata, and possible external domain
mutation. This slice has no external domain effects; uncertainty-before-commit
may still retain internal retry-blocking metadata.

This package is not a complete kernel and does not assign or execute Tasks. It
contains no API, database, file persistence, queue, network calls, Tool adapter,
scheduler or subscriber runtime, memory retrieval, agent, model, background
worker, authentication store, or production authorization implementation.
Importing it performs no I/O, clock access, identifier allocation, environment
inspection, thread creation, or global state mutation.

`tests/kernel/conformance_map.py` maps the 80 numbered behavioral scenarios to
the applicable `KERNEL_CONFORMANCE.md` scenario identifiers. Passing these tests
demonstrates only this narrow slice; it does not imply full behavioral,
adversarial, replay, operational, or overall kernel conformance.

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
capabilities, bootstrap, scheduling, subscriptions, Tools, memory retrieval,
networking, agents, and models. It is a foundation for those separately governed
increments, not a claim of full kernel conformance.
