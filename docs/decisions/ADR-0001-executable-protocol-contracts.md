# ADR-0001: Executable protocol contracts

## Status

Accepted for the reference contracts package.

## Context

The executable ontology, kernel contract, conformance specification, and kernel
protocol define technology-neutral behavior and logical records. Future kernel
implementations need a small executable reference that makes structurally
impossible states rejectable without prematurely implementing governance or
selecting an operating architecture.

## Decision

AIOS will maintain a dependency-free Python package named `aios_protocol` as a
reference executable contract. It defines immutable logical records, typed
identifiers, explicit presence states, stable protocol enumerations and reason
codes, safe structural validation, and deterministic conformance comparison.
It performs no admission, authorization, Policy, lifecycle, execution, storage,
projection, replay, scheduling, subscription, accounting, retrieval, or model
behavior.

### Python-version policy

The repository established no older Python baseline. The package therefore
targets Python 3.11 and later and avoids features that would unnecessarily raise
that floor. The supported floor may change only through a later decision and
must not silently reinterpret historical record versions.

### Dependency policy

The package and tests use only the Python standard library. `unittest` is
adequate for deterministic structural tests, so pytest and validation
frameworks are not introduced. A future dependency requires an ADR showing
substantial clarity or correctness benefit. Web frameworks, ORMs, database
drivers, queues, model SDKs, and cloud SDKs are outside this package.

### Immutable logical-record approach

Records use frozen, slotted dataclasses. Collection inputs are copied into
tuples, frozensets, or recursively frozen mappings during construction, so
callers cannot mutate records indirectly. Constructors validate only structural
invariants.

### Identifier representation

Important identity classes use distinct validated string value types. Runtime
type distinction prevents accidental interchange where practical. Identifiers
are always caller- or future-kernel-supplied; this package never allocates or
randomizes them.

### Time representation

Times are timezone-aware `datetime` values. Naive times are rejected. Record
construction never consults a clock or supplies default timestamps. External
timestamps remain observations; only a future kernel supplies authoritative
evaluation and Event ordering values.

### Presence-semantics representation

Known, unknown, not-yet-known, not-applicable, intentionally empty, withheld,
redacted, externally unavailable, and conflicting states are distinct immutable
values. `None` is reserved for true optional absence. Withheld and redacted
states carry governed references, never protected content.

### Validation boundary

Validation rejects malformed types, invalid exclusivity, prohibited field
ownership, unsafe state claims, and internally inconsistent records. It does
not authenticate Actors or adapters, resolve references, evaluate Authority,
Policy, Approval, Resources, or lifecycle state, or verify external outcomes.
Failures use safe implementation-only validation codes and may map to a
normative protocol reason code.

### Trusted and caller-asserted fields

Narrow envelope types make field ownership explicit. Caller messages cannot
contain authoritative evaluation time, stream position, Event order, or trusted
attribution. Payloads cannot override trusted envelope fields. Event-store,
kernel, adapter, subscriber, and replay-controller observations have distinct
record families. A caller's reference is an assertion, never proof of validity.

### Deterministic comparison strategy

Comparison recursively normalizes immutable logical values without choosing a
serialization. Normatively ordered sequences remain ordered. Symbolic identifier
bindings are explicit and type-sensitive. Timestamps, identifiers, reason codes,
and ordering remain compared. Only explicitly permitted implementation metadata
may be excluded.

### Serialization neutrality

Python classes are a reference expression, not a wire encoding. The contract
does not privilege JSON, YAML, Protobuf, Avro, HTTP, RPC, or any transport.
Other implementations conform through equivalent logical semantics and the
governing conformance suites.

## Rejected alternatives

Unstructured dictionaries were rejected because they permit ambiguous presence,
identifier interchange, payload overrides, and invalid state combinations.
A third-party validation framework was rejected because the standard library is
sufficient and adds less coupling. Generated wire schemas were rejected because
they would select serialization semantics. A working kernel skeleton was
rejected because it would blur structural contracts with governance behavior.
Automatic UUIDs and timestamps were rejected as nondeterministic and as an
improper transfer of authoritative allocation into the contracts layer.

## Consequences

Protocol fixtures become concise and mechanically comparable. Invalid structural
claims fail early and safely. Future implementations gain an executable reference
without being required to use Python internally or on the wire. The package is
deliberately unable to establish whether a structurally valid operation should
be admitted or whether an external action succeeded; behavioral conformance
still requires a kernel and the full conformance suite.

## Explicit non-goals

This decision does not implement a kernel, production service, API, database,
queue, adapter, scheduler, agent, model call, network protocol, serialization,
authentication, authorization, Policy evaluation, Resource accounting, Event
storage, projection, replay execution, Tool execution, or memory retrieval. It
does not claim that passing structural tests proves behavioral kernel
conformance.
