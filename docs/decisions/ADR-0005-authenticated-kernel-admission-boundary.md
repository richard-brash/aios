# ADR-0005: Authenticated kernel admission boundary

- Status: Proposed
- Date: 2026-07-27

## Context

An ordinary Command can name an Organization and initiating Actor, but those
claims do not prove that an authoritative Organization recording boundary
exists or that the invocation is attributable to that Actor within it. Recording
a rejection before proving both facts would let hostile input create history in
a caller-selected Organization namespace. Authentication and attribution must
also remain distinct from later authorization and governance.

## Decision

Ordinary post-genesis Commands use a trusted, capability-neutral
`RecordingBoundaryResolver`. It receives an immutable `AdmissionClaim` and
returns the closed result `AdmissionEstablished | AdmissionDenied`.

`AdmissionEstablished` exactly binds the submitted Command, message,
Organization, initiating Actor, and invocation proof to canonical stable
identities, completed Organization genesis, Actor identity evidence,
authentication evidence, and a versioned admission mechanism. It proves that
authoritative Organization attribution is established; it grants no Authority.
Aliases, display names, and cross-Organization fallback cannot canonicalize a
Command claim.

`AdmissionDenied` is typed, immutable, bounded, and non-authoritative. Before
establishment the kernel reads no Organization stream, inspects or creates no
Organization idempotency registration, allocates no authoritative disposition,
Event, or Audit Record identifier, invokes no Organization governance or domain
handler, and appends nothing. Evaluation time may be read from the injected
Clock because that is effect-free.

Schema, operation, and operation-version support resolution follows Model A:
it occurs effect-free before recording-boundary resolution. Unsupported input
therefore returns a non-recorded rejection. After establishment, governance and
domain handling remain independent stages. Their attributable rejections may be
recorded atomically under the existing kernel rules. Organization-scoped exact
redelivery begins only for a previously recorded attributable disposition.

Bootstrap retains its reserved pre-Organization constitutional admission path.
It neither uses nor weakens the ordinary resolver, and ordinary Commands cannot
select bootstrap admission.

## Rationale

Syntactic identifier validity is not existence or authenticity proof. An
explicit trusted boundary makes the mutation permission testable without
selecting an identity provider, transport, or storage technology. Model A
minimizes hostile-input effects and follows parse-before-effect admission order.
Starting Organization idempotency only after admission prevents untrusted
claims from creating governed state while preserving authoritative redelivery
semantics after attribution exists.

## Rejected alternatives

- Treat well-formed Organization and Actor identifiers as proof. This permits
  caller-selected authoritative namespaces and forged attribution.
- Use authorization success as authentication. This conflates identity proof
  with permission and makes denial attribution circular.
- Record every rejection in the claimed Organization. This creates authority
  and history before the recording boundary exists.
- Resolve unsupported operations after admission. This adds avoidable trusted
  Organization processing for inputs that can be rejected effect-free.
- Unify bootstrap with ordinary admission. Genesis is the reserved exception
  that establishes the first Organization boundary and cannot require it first.
- Define a production identity provider or Actor-to-Role membership model.
  Those choices are outside this contract and would introduce later-milestone
  semantics.

## Consequences

PR #8 must inject the resolver, create claims only after effect-free support
validation, and distinguish non-recorded pre-boundary rejection from existing
attributable rejection. Its descendants must then be rebased and revalidated in
dependency order. Adapters must prove completed Organization genesis, exact
stable Actor attribution, invocation authentication, and versioned evidence,
but remain free to choose provider and storage mechanisms. Replay never invokes
the resolver. Production authentication, transport security, anti-replay,
external hostile-input telemetry, Role Assignment, and capability authorization
remain deferred.
