# AIOS executable protocol contracts

This package is the Python 3.11-compatible reference expression of the logical
records in `docs/specifications/KERNEL_PROTOCOL.md`. It supplies immutable
value records, typed identifiers, explicit presence states, structural
validation, stable reason codes, and deterministic comparison helpers.

It is not a kernel, service, wire format, authorization engine, policy engine,
event store, projection builder, scheduler, Tool adapter, Resource meter,
memory search facility, or model integration. Asserted references remain
untrusted; constructing a record never proves Authority, Approval, Policy
compliance, external success, or organizational truth.

The package is downstream of the executable ontology, `KERNEL_CONTRACT.md`,
`KERNEL_CONFORMANCE.md`, and `KERNEL_PROTOCOL.md`. Future kernels may depend on
these logical contracts or implement demonstrably equivalent contracts. No
Python representation or serialization implied by it is a normative wire
encoding.

Imports are side-effect free: they do not inspect the environment, read a
clock, allocate identifiers, touch files or networks, or initialize services.
All identifiers and timezone-aware times are supplied explicitly. Protocol,
record, payload, specification, and Policy versions are separate value types;
unknown versions remain representable and are rejected only when checked
against an explicit supported-version registry.

Conformance fixtures use stable symbolic typed identifiers. Comparison helpers
may bind an expected symbolic identifier to an observed one, while continuing
to compare type, order, timestamps, reason codes, and every other normative
field. Only metadata fields explicitly permitted by the conformance
specification may be excluded.

Structural tests map to these `KERNEL_CONFORMANCE.md` suites:

| Test area | Conformance suites |
| --- | --- |
| identity, time, presence, versions | canonical fixtures; determinism; failure-closed |
| envelopes and Commands | command admission; Work Root; audit |
| authenticated admission | recording-boundary resolution; non-recorded pre-boundary denial |
| dispositions, Events, append | command admission; event ordering and idempotency |
| Tool and reconciliation records | Tool invocation and reconciliation |
| Resources and Approvals | resource governance; Approval |
| scheduling and subscriptions | scheduling and orchestration; subscription isolation |
| memory and bootstrap | memory governance; bootstrap |
| replay and comparison | replay and recovery; portability and model replacement |

These tests validate executable structural contracts only. They do not satisfy
or imply behavioral, adversarial, replay, or operational kernel conformance.

Ordinary post-genesis processing uses the immutable contracts in
`aios_protocol.admission`: an `AdmissionClaim` is resolved by the trusted
kernel `RecordingBoundaryResolver` to either `AdmissionEstablished` or
`AdmissionDenied`. Establishment proves exact Organization and initiating
Actor attribution, not authorization. Denial is non-authoritative and permits
no Organization stream, idempotency, audit, or Event effect. Bootstrap retains
its distinct reserved constitutional admission path.
