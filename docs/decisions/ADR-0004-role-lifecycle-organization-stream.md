# ADR-0004: Role lifecycle and Organization stream authority

**Status:** Accepted

## Context

The ontology listed Role lifecycle states without defining the legal initial transition for ordinary post-genesis creation. The architecture also required monotonic ordering within an Organization but did not state explicitly whether contained entities could have independent authoritative streams. Some prospective implementation language additionally used tenancy terminology that could be read as requiring a separate Tenant entity.

These ambiguities could produce incompatible implementations of the first ordinary Role capability.

## Decisions

1. An ordinary post-genesis Role is created only through `[nonexistent] -> draft`. Ordinary creation cannot establish `active`; activation is a separate governed action. The founding Role established during constitutional bootstrap remains a distinct genesis case.
2. All authoritative post-genesis Events for Organization-contained entities, including Role Events, append to one monotonically ordered Organization stream. Entity identity and `entity_revision` support derived entity projections and domain preconditions, but no per-Role stream is authoritative. The expected Organization stream position is the authoritative append concurrency boundary.
3. The Organization is the AIOS tenancy, isolation, governance, and Event-ordering boundary. The domain model has no separate Tenant entity or `tenant_id`.

## Rationale

Draft-first creation separates structural definition from operational activation and prevents creation from implicitly enabling authority. A single Organization stream preserves deterministic organization-wide order, atomic admission, replay, and audit without premature cross-stream coordination. Using Organization as the canonical boundary avoids duplicating identity and governance scope without an approved need.

## Rejected alternatives

### Starting Roles as active

Rejected because creation would implicitly activate organizational capability or authority and weaken fail-closed governance.

### Authoritative per-Role streams

Rejected because they would violate Organization-wide monotonic ordering or duplicate authoritative history, and would require cross-stream atomicity or distributed coordination prematurely.

### Separate Tenant entity

Rejected because it duplicates the current Organization boundary without an approved domain need.

## Consequences

- Future ordinary CreateRole handling must create only `draft` Roles and append its Event to the Organization stream.
- Role identity, state, and revision are reconstructed as projections of Organization history.
- Role-specific state preconditions may be checked, but cannot replace or override the expected Organization stream position.
- Bootstrap remains a reserved pre-Organization genesis path and its founding Role is not recreated.
- Physical partitioning remains possible only when it preserves one authoritative Organization order and atomicity semantics.

## Migration implications

The current executable runtime already uses Organization-scoped ordinary streams and defines no Tenant domain identifier, so no existing runtime migration is required. The later CreateRole slice must not introduce an authoritative Role stream or Tenant identifier. Its projection input may require a narrow Role-specific representation, but that is deferred with the capability implementation.
