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
