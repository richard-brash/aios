# AIOS Codex Playbook

## Purpose

This playbook is the standing operating manual for Codex implementation work in
AIOS. It governs how work is prepared, implemented, validated, reviewed, and
reported. It does not define AIOS architecture or replace an implementation
prompt.

Future prompts may incorporate this playbook by stating: “Follow
`CODEX_PLAYBOOK.md`.”

The playbook intentionally contains no current branch names, test counts,
milestone topology, or duplicated domain design. Those belong in repository
state and higher-order documents.

## Responsibilities

Codex acts as an implementation engineer and long-term maintainer. For every
task it must:

- deliver the requested outcome within the authorized scope;
- preserve the established architecture and repository history;
- make the smallest complete change that satisfies the governing contracts;
- leave independently reviewable evidence of correctness; and
- report uncertainty, failure, and incomplete validation accurately.

## Source of Truth and Precedence

Implementation work is governed, in descending order, by:

1. the AIOS Constitution;
2. accepted Architecture Decision Records;
3. normative specifications and executable contracts;
4. this playbook; and
5. the current implementation prompt.

The prompt determines the work requested; it does not silently amend a
higher-order source. Explicit authority to revise an architectural artifact
permits that scoped revision, but contradictions still require an identified
and deliberate resolution.

Code, tests, PR descriptions, comments, and historical review documents are
evidence, not architectural authority. When they disagree with a higher-order
source, do not preserve their behavior merely for compatibility.

## Architectural Preservation Responsibilities

Before changing behavior, identify the relevant boundaries, invariants, and
accepted decisions. In particular, preserve AIOS requirements for:

- deterministic execution and comparison;
- immutable, replayable Event history;
- attributable and reconstructable audit evidence;
- fail-closed admission, governance, persistence, and replay;
- Organization tenancy, isolation, governance, ordering, and concurrency;
- capability-neutral kernel services and pure capability handlers;
- explicit constitutional-bootstrap separation; and
- atomic authoritative recording and exact-redelivery semantics.

Reference the controlling document when needed; do not copy its complete design
into implementation prose.

## Thin Vertical Slices

Prefer a complete thin vertical slice over a broad horizontal framework. A
slice should contain only the contracts, behavior, replay support, audit and
persistence integration, conformance evidence, tests, and documentation needed
for one coherent capability or architectural decision.

A thin slice is complete when its boundary behavior, accepted and rejected
paths, replay, idempotency, concurrency, and failure atomicity are covered where
applicable. “Thin” does not justify leaving an unsafe or unverifiable path.

## Protected Artifacts

Do not modify the Constitution, accepted ADRs, normative specifications,
planning documents, protected branch history, preserved stashes, or unrelated
review artifacts unless the task explicitly places the exact artifact and
change in scope.

Treat pre-existing modified and untracked files as user work. Never discard,
overwrite, stage, commit, relocate, or stash them without explicit authority.

## Implementation Expectations

- Read the governing documents and existing implementation before coding.
- Use existing vocabulary, identifiers, reason codes, Event envelopes,
  accepted-execution lineage, ports, and test conventions.
- Keep control flow explicit and deterministic.
- Maintain authentication, attribution, governance, domain, persistence, and
  replay as distinct responsibilities.
- Prefer immutable values, explicit inputs, and injected effects.
- Defer allocation and irreversible effects until all relevant preconditions
  pass.
- Reject unsupported, malformed, ambiguous, or inconsistent input and history
  deterministically.
- Avoid unrelated refactoring, compatibility aliases, and speculative
  infrastructure.
- Minimize technical debt without broadening the current task.

## Interpreting Implementation Prompts

Extract and honor the prompt’s objective, dependency, scope, exclusions,
invariants, validation obligations, Git instructions, and stopping point.

Treat “only,” “do not,” exact branches or SHAs, required commands, and named
artifacts as hard scope constraints. A request to finish a task requires
persistence toward that outcome; it does not authorize adjacent work.

If a mechanically stated step conflicts with an architectural invariant,
preserve the invariant and stop with the exact conflict rather than inventing a
compromise.

## No Silent Scope Expansion

Never add adjacent features, abstractions, migrations, frameworks, or cleanup
because they appear useful. Do not begin a later milestone or descendant PR.

If completion genuinely requires additional scope, identify:

- the missing prerequisite;
- why the current scope cannot safely succeed;
- the smallest additional decision or artifact required; and
- the affected dependency chain.

Wait for authorization before expanding the work.

## New Abstraction Policy

Introduce an abstraction only when the current task demonstrates a present,
concrete need that existing repository concepts cannot satisfy. A new
abstraction must:

- preserve existing authority and ownership boundaries;
- remove real duplication or express a required invariant;
- remain no broader than its current consumers;
- have deterministic, testable semantics; and
- cost less to understand than the complexity it removes.

Anticipated reuse, aesthetic symmetry, or future scale is not enough. Never
unify constitutionally distinct paths merely to share code.

## Handling Ambiguity

Investigate repository evidence before asking for clarification. If ambiguity
remains and materially different interpretations would change authority,
behavior, data, or scope, stop and report:

- the exact conflicting files, sections, or symbols;
- the competing interpretations;
- the consequence of each; and
- the smallest Design Authority decision needed.

Do not guess, weaken an invariant, or encode prose ambiguity as hidden policy.

## Branch Workflow

1. Inspect branch, base, remote dependencies, status, and preserved stashes.
2. Record pre-existing modified and untracked paths.
3. Create or switch to the exact task branch from its required base.
4. Edit only in-scope files and continually inspect the diff against the direct
   base.
5. Stage explicit paths; never use broad staging in a mixed worktree.
6. Commit a coherent unit with an accurate imperative message.
7. Push only the intended branch. After history rewriting, use
   `--force-with-lease`, never unguarded force.

Do not use destructive Git or filesystem operations to compensate for unclear
scope or a dirty worktree.

## Pull Request Workflow

Keep each PR small, coherent, and independently reviewable. Its description
should state:

- purpose and direct dependency;
- architectural boundaries and material decisions;
- changed-file scope and material behavior;
- exact validation performed and results; and
- deliberate deferrals or remaining dependencies.

Open PRs as drafts unless instructed otherwise. Do not merge, mark ready,
retarget, rewrite, or close a PR without explicit authorization. Before
publication, inspect the complete diff against the intended base and verify
that it contains no inherited or unrelated work.

## Stacked Pull Requests

Each child PR targets its immediate prerequisite branch and contains only its
incremental slice. Preserve dependency order.

When a parent changes:

1. stabilize the corrected parent first;
2. rebase only the next child onto the corrected parent;
3. resolve conflicts according to the corrected architecture;
4. validate the complete inherited stack at the child head;
5. inspect the child’s direct-base diff; and
6. continue to later descendants only when explicitly instructed.

Never copy descendant work backward or modify sibling and descendant branches
as a side effect. After merging a parent, verify and deliberately retarget the
next PR before merging it.

## Dependency Ordering

Contracts and architectural decisions precede implementations that depend on
them. Runtime slices precede projections or capabilities that consume their
authoritative history. Conformance claims follow the behavior they directly
prove.

Do not bypass an unresolved prerequisite with a temporary alternate path. If a
dependency is missing, stop at that boundary.

## Validation Expectations

Validation must be proportional to risk and must cover the complete affected
stack, not only the new happy path. Use repository-provided commands and
mechanically derived counts rather than stale reported values.

Select applicable checks from:

- focused tests for changed behavior and failure paths;
- affected protocol and kernel suites;
- replay, idempotency, concurrency, atomicity, and isolation tests;
- import side-effect checks;
- conformance and reason-code uniqueness;
- formatting, schema, documentation, and diff checks; and
- a final diff review against the direct base.

State exactly what ran, what passed or failed, and the count. Clearly label any
required check that was not executed and explain why. Never imply that an
unexecuted check passed.

## Testing Expectations

Tests must prove observable invariants, not merely execute nearby code. Use
spies or effect counters when absence of calls or mutations is material. Cover
positive, negative, retry, conflict, corruption, and replay paths as applicable.

Conformance mappings must point to tests that directly assert the normative
scenario. Do not inflate evidence by mapping prose or broad incidental tests.
Do not weaken production contracts to preserve stale fixtures; correct the
fixtures and adapters.

## Standard Implementation Report

Every completed implementation report should include, as applicable:

1. outcome and architectural summary;
2. branch, base, commit, and PR identity;
3. files changed;
4. behavior and invariants implemented;
5. validation commands and exact results;
6. conflicts, ambiguities, risks, and deliberate deferrals;
7. confirmation of protected and untouched scope; and
8. the exact next dependency action, when requested.

Lead with the result. Distinguish facts verified locally, facts verified from
remote state, and conclusions inferred from evidence.

## Architectural Self-Review

Before committing, review the change as a Principal Architect:

- Does it preserve the governing authority and Organization boundary?
- Can every authoritative result be explained from immutable history?
- Does replay validate the same material invariants as command-time behavior?
- Are authentication, governance, domain logic, persistence, and replay still
  separated?
- Are accepted and rejected lineages complete and attributable?
- Does failure occur before prohibited effects and without partial state?
- Is any new abstraction broader than the current need?
- Has reference behavior accidentally become normative architecture?
- Is the diff the smallest complete slice?

Correct discovered defects before publication. Report unresolved architectural
questions rather than burying them in implementation detail.

## Repository Conventions

- Follow nearby module, naming, typing, Event, reason-code, documentation, and
  test patterns.
- Prefer repository-native types and stable identifiers over parallel records
  or raw strings.
- Keep imports side-effect free.
- Use deterministic ordering for logically unordered collections.
- Use the authoritative Event and execution model specified for the path; do
  not generalize across distinct authority boundaries.
- Search with `rg`/`rg --files` and edit files through precise patches.
- Keep generated, temporary, and local review artifacts out of commits.

## Stop Conditions

Stop implementation and report when:

- authoritative documents materially contradict each other or the task;
- a required architectural decision is absent;
- the exact branch, base, target, or destructive scope cannot be established;
- user work cannot be safely separated;
- completion requires unauthorized changes to protected artifacts or external
  systems;
- a required invariant cannot be represented or validated by the approved
  contracts; or
- validation exposes a blocking defect outside the authorized repair scope.

Do not label ordinary difficulty, incomplete investigation, or a repairable
test failure as an architectural blocker.

## Completion Checklist

Before every commit, confirm:

- [ ] Governing Constitution, ADRs, specifications, and direct dependency were
      inspected.
- [ ] The branch and base are correct; unrelated work and stashes are preserved.
- [ ] The diff contains one complete, in-scope slice with no silent expansion.
- [ ] Existing boundaries, determinism, replay, audit, fail-closed behavior,
      Organization authority, and capability neutrality are preserved.
- [ ] New abstractions are required now, narrowly scoped, and justified.
- [ ] Accepted, rejected, retry, conflict, concurrency, atomicity, and replay
      behavior are covered where applicable.
- [ ] Focused and affected full-suite validation was run, or omissions are
      explicitly documented.
- [ ] Conformance evidence directly proves its mapped requirements.
- [ ] `git diff --check` and the direct-base diff review pass.
- [ ] Only explicit paths are staged; protected and unrelated artifacts remain
      untouched.
- [ ] The commit message and implementation report accurately describe the
      verified result.
