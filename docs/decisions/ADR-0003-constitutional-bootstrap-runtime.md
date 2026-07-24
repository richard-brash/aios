# ADR-0003: Constitutional bootstrap runtime reference choices

## Status

Accepted for the constitutional bootstrap reference slice.

## Context

The normative specifications define a distinct pre-Organization bootstrap
protocol, a complete semantic founding set, direct constitutional admission,
atomic recording, exact-redelivery behavior, deterministic rejection of
materially competing genesis, and replay. They intentionally do not prescribe
concrete founding Event type names, Event granularity, or a stream identifier
encoding.

The runtime therefore needs narrow reference choices without turning those
choices into a normative Event vocabulary or transport contract.

## Decision

Bootstrap remains separate from `KernelRuntime` and its Organization-scoped
`RuntimeCommand`. `ConstitutionalBootstrapRuntime` accepts only a fully
constructed `BootstrapRequest`, binds one injected evaluation time, invokes a
pure constitutional evaluator, and passes only an accepted Decision to the
atomic genesis append boundary.

The reference genesis stream identity is the deterministic opaque logical value
`genesis:{organization_id}`. This is a reference-package convention, not a
required external encoding. Genesis always expects an absent or empty stream and
starts Event positions at one.

Concrete Event type names remain those proposed in `FoundingEventSet`.
`FoundingEventCoverage`, not Event names, proves that the ordered proposal
establishes Organization attributes, verified Human, Constitution, Mission,
jurisdiction, retention Policy, founding Role, active Role Assignment, founding
Decision and duty, initial Authority Grants, and audit record. One Event may
cover several semantic facts. The reference materializer wraps the approved
immutable proposal payload with recording metadata; it does not regenerate the
proposal or infer founding facts from external state.

The reference store performs, under one in-process critical section:

1. accepted-Decision/request equality;
2. existing registration comparison;
3. empty-stream concurrency validation;
4. deferred deterministic Event materialization;
5. complete-set, ordering, identity, command, Organization, and audit checks;
6. atomic publication of the Event stream and exact-redelivery registration.

The lock demonstrates one atomic boundary only and is not production or
distributed persistence.

`REJECT_MATERIAL_CONFLICT` uses a symmetric logical comparison. Equal complete
requests are exact redelivery; any material difference is a competing genesis.
The comparison has no winner-selection algorithm and uses no arrival time,
clock, randomness, iteration order, or network observation. Once a complete
genesis is recorded, it is never replaced. An uncertain precommit attempt stores
only internal quarantine metadata and no founding Events.

Replay consumes the ordered immutable founding Events only. It validates stream,
position, identity, command, audit, proposal, and terminal-completion invariants
and reconstructs the minimum founded Organization state. It does not call the
evaluator, recording Command, clock, identifier allocator, store mutation, or an
external service.

## Consequences

The slice can prove one atomic constitutional genesis without implementing a
general governance engine. Event vocabularies with different names or
granularity can conform if they provide equivalent ordered semantic coverage.
The reference in-memory store is intentionally unsuitable for production,
multi-process, or distributed concurrency.

Identifier allocation occurs only after registration and stream checks. A
materialization failure may consume injected Event identifiers even though the
store remains unchanged; identifier rollback is not introduced here.

## Rejected alternatives

Using the ordinary Organization-scoped runtime was rejected because no
Organization or ordinary Grant exists before genesis. Selecting one mandatory
Event class per founding fact was rejected because the specifications preserve
Event-vocabulary openness. Arrival-order precedence and random tie-breaking were
rejected as nondeterministic. Direct current-state insertion, partial append,
proposal regeneration, and replay through command execution were rejected as
violations of event sourcing and auditability.

## Explicit non-goals

This decision does not define production storage, distributed consensus,
general Policy evaluation, identity-proof verification infrastructure,
post-genesis Organization commands, Role management, workers, scheduling,
planning, Tools, APIs, databases, agents, or models.
