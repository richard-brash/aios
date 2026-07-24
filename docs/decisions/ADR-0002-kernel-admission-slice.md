# ADR-0002: CreateTask kernel admission slice

## Status

Accepted for the first behavioral reference slice.

## Context

AIOS has technology-neutral ontology, kernel, conformance, and protocol
specifications plus executable structural protocol contracts. The next useful
step is to prove one end-to-end kernel behavior without prematurely building a
general kernel or selecting production infrastructure.

## Decision

Implement one Python 3.11-compatible, standard-library-only admission slice for
`CreateTask`. It creates one proposed Task under an existing active Goal Work
Root. Every other operation, Duty Work Root, Tool request, or initial Task state
fails closed. The slice consumes `aios_protocol` records rather than duplicating
them.

### Why CreateTask

CreateTask crosses identity, Organization, Work Root, Decision, Authority,
Policy, Approval, Resource, lifecycle, audit, Event, idempotency, concurrency,
and projection boundaries while ending before assignment or execution. It is
therefore the smallest operation that demonstrates meaningful governance and
authoritative state without external effects.

### Functional core and imperative shell

Admission binds one immutable Command, one authoritative evaluation time, one
coherent snapshot generation, and evidence-bearing gate results. Gate evaluation
and Event construction are deterministic and mutation-free. The only mutation
boundary is one call carrying the complete `KernelTransaction` to the atomic
append port.

### Port boundaries

The core depends on narrow protocols for a Clock, authoritative identifier
allocator, coherent snapshot reader, separate structured governance evaluators,
and atomic append store. Evaluators return pass, deny, unavailable, or
indeterminate results with reason code, evidence, versions, guidance, and audit
facts; booleans are insufficient. Missing evaluator configuration fails closed.

### Evaluation time and identifiers

The Clock supplies one explicit timezone-aware evaluation time. Core code never
reads a wall clock. The allocator supplies disposition, audit, and Event IDs.
Core code contains no random, UUID, counter, or time-derived allocation.
Exhaustion fails before append with a safe internal failure.

### Event-store abstraction and atomic recording

The store receives expected Organization stream position, ordered Events,
disposition, audit record, idempotency registration, projection input, Resource
transitions, and Approval-use transitions as one transaction. Confirmation,
concurrency conflict, validation failure, append failure, and uncertain outcome
remain distinct. Acceptance and rejection Events share their audit record. No
projection, reservation, Approval use, or idempotency record becomes visible on
a confirmed precommit failure.

### Idempotency and optimistic concurrency

Idempotency is scoped by Organization, initiating Actor, operation family, and
key. `semantic_command_identity` defines equivalence as an immutable logical
value containing every caller-supplied CreateTask field except the envelope
`message_id`, which identifies delivery rather than the requested operation.
Typed identifiers and presence values retain their types; mappings are ordered
by canonical logical key; normatively ordered sequences retain their order. A
nonnormative length-prefixed internal encoding is hashed with SHA-256. This
encoding is an implementation detail, not a wire format or cross-language
serialization contract.

An exact duplicate returns `PreviouslyAdmitted` with the original disposition
identity, time, Event IDs, and result and allocates nothing. Conflicting reuse
returns `IDEMPOTENCY.CONFLICT` without replacing the original registration. An
uncertain prior outcome blocks retry until reconciliation. Preflight inspection
is advisory. The store checks the registration under its atomic lock before
stream concurrency validation and mutation, then registers the fingerprint in
the same commit as Events, audit, projection, Resources, and Approval use.
Existing authoritative registrations are never overwritten.

Uncertain results separately report whether authoritative organizational state
may have changed, whether internal reconciliation-safety metadata was recorded,
and whether external domain mutation may have occurred. The reference slice has
no external effects, so the last value is always false. For uncertainty before
commit, an internal retry-blocking registration may exist even though no
authoritative Event or Task state changed.

### Organization isolation

The bound snapshot resolves the Organization of the Actor, Goal, Decision,
Grants, Approvals, and Resources. Any mismatch rejects with bounded detail that
does not disclose the foreign Organization. Idempotency keys are scoped by
Organization and Actor as well as operation family and key.

### Gate order and failure closure

Granular gates preserve the normative `KERNEL_CONTRACT.md` order: structural
parse; operation/schema version; Organization; identity; idempotency; Authority;
Policy; Work Root; Decision and Approval; target/lifecycle/concurrency and
Incident suspension; Resources; final invariant; identifier allocation; Event
and audit construction; atomic append. Split gate names retain precise audit
evidence without changing the governing logical sequence. The first decisive
failure stops later evaluation. Unavailable and indeterminate governance never
become permission.

### Projection rebuilding

The Task projection is derived from sequential authoritative `TaskCreated`
Events and contains identity, Organization, title, purpose, proposed state, Goal,
Decision, initiating Actor, creation Command/Event/time, entity version, and
classification. Rebuild starts at zero, validates Event ordering, performs no
allocation or clock read, and compares replayed state against—never beneath—the
stored projection.

### Reference adapters

FixedClock, DeterministicIdentifiers, configured evidence-bearing evaluators,
BoundSnapshotReader, and InMemoryStore exist only as deterministic test adapters.
The store uses one in-process lock and fault injection to demonstrate atomic
semantics. This is not production persistence and the lock is not a distributed
concurrency strategy.

## Rejected alternatives

A generalized admission engine was rejected as excess scope. A web or CLI API,
database, file persistence, queue, dependency-injection framework, policy
language, external Tool, and model integration were rejected because none is
needed to prove this behavior. Wall-clock defaults, UUIDs, permissive evaluators,
boolean gates, direct projection writes, and separate audit or reservation
commits were rejected because they undermine determinism, evidence, or atomicity.

## Explicit non-goals

This is not a complete or production kernel. It does not create or execute Goals,
Organizations, Actors, governance records, schedules, subscriptions, memory, or
Tools. It does not assign or execute Tasks. It provides no API, database, queue,
networking, credentials, authentication store, agent, model, worker, background
task, distributed transaction, multi-process locking, or production retry.

## Before production use

AIOS still requires production identity and governance services, durable Event
and audit storage, integrity and authentication mechanisms, distributed
concurrency and recovery, reconciliation operations, projection versioning,
Resource and Approval implementations, security hardening, observability,
operational controls, migrations, and the remaining behavioral, adversarial,
replay, and operational conformance suites.
