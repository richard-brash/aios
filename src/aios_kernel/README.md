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
