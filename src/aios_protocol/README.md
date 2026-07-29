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

Milestone 3 source-Grant attenuation starts with the immutable contracts in
`aios_protocol.authority`. A `SourceAuthorityGrantClaim` asks a read-only
trusted boundary to prove one exact, Organization-bound use; a
`SourceAuthorityGrantProof` binds that use to active authoritative Grant
evidence, exact finite capabilities, affirmative delegation, and one comparable
source-Resource ceiling. A distinct `TaskResourceBound` identifies the Task
Budget while retaining exact source-Resource, dimension, and unit lineage.
These records neither administer Grants nor authorize or
execute a capability. Historical replay validates the recorded proof without
calling its resolver or consulting mutable current state.

Temporary Worker eligibility uses the immutable contracts in
`aios_protocol.temporary_worker`. Enrollment preserves the existing Temporary
Worker Actor identity and pins same-Organization Worker, Sponsor, source-Grant,
purpose, and first-worker bounds. Closed transition claims and accepted proofs
bind lifecycle revisions, prior transition evidence, Organization-stream and
audit lineage, and terminal-Task evidence for completion. The pure evaluator
port neither grants authority nor performs identity lookup, governance,
persistence, clock access, or capability execution.

## Constitutional bootstrap contracts

Organization genesis uses `BootstrapEnvelope`, whose traffic mode is explicitly
pre-Organization and which has no `organization_id`. It must not be represented
by `CallerEnvelope`, `CommandSubmission`, or a runtime Command because those
contracts require an already-existing Organization boundary.

The bootstrap family separates four logical stages:

1. `BootstrapRequest` supplies the verified founding Human, complete Organization
   attributes, constitutional duty, founding Role and active Role Assignment,
   Human-decided founding Decision, bounded initial Authority Grants, reserved
   genesis recording Command, audit references, and complete proposed Event set.
2. `BootstrapProposal` pins that complete proposed result without recording it.
3. `BootstrapAcceptedDecision` or `BootstrapRejectedDecision` records the typed
   constitutional admission disposition; acceptance is not durable genesis.
4. `BootstrapCommitted` records the complete atomic result, while
   `BootstrapPreviouslyAdmitted` and `BootstrapUncertain` preserve exact retry or
   quarantine semantics.

`FoundingEventSet` preserves the proposed logical order and
`FoundingEventCoverage` maps every required founding fact to a proposal key.
Concrete Event granularity and type strings remain explicit reserved-genesis
protocol data because the normative specifications do not mandate one encoding
or Event-name vocabulary. One Event may establish several facts, but missing
coverage cannot construct a valid set.

These are immutable structural records only. They do not verify Human identity,
evaluate constitutional eligibility, resolve competing genesis, allocate IDs or
stream positions, append Events, create an Organization projection, or execute
bootstrap. Those behaviors remain the responsibility of a later kernel slice.
