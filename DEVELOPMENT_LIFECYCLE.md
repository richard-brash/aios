# AIOS Development Lifecycle

## Purpose

This document defines the canonical process by which AIOS engineering work
moves from an identified need to accepted, integrated, and completed change. It
coordinates responsibilities, evidence, decisions, and state transitions for
human participants, AI tools, and future governed AIOS workers.

It is not an architecture specification or an implementation manual. The
Constitution, accepted Architecture Decision Records (ADRs), and normative
specifications define architectural authority. [`CODEX_PLAYBOOK.md`](CODEX_PLAYBOOK.md)
defines how Codex performs work already authorized for implementation.

The lifecycle is designed for deterministic transitions, auditable decisions,
fail-closed advancement, independent validation and review, complete thin
vertical slices, and dependency-aware integration. It defines a process that
AIOS may later represent and govern without prescribing an orchestration system
today.

Executable lifecycle records, automated gate enforcement, governed-worker role
assignment, queues, and orchestration remain deferred until separately
authorized.

## Governing Rules

### Authority and precedence

The Constitution, accepted ADRs, normative specifications, and other
authoritative repository artifacts retain their established precedence. This
lifecycle controls advancement of engineering work; it cannot amend
higher-order authority. A lower-order artifact may clarify or implement an
approved decision but may not silently replace it.

An authorized implementation prompt may explicitly and narrowly override an
ordinary Implementation Engineer procedure as permitted by
`CODEX_PLAYBOOK.md`. That procedural override cannot change lifecycle state,
satisfy or skip a gate, substitute for required evidence or decision authority,
or amend higher-order authority. A task that changes an authority-bearing
artifact must itself be authorized through the applicable lifecycle and
decision process.

### Explicit, fail-closed advancement

State does not advance because work appears complete. Every transition requires
the stated evidence and an attributable decision by the authorized role, or an
objective result where the gate is mechanical. Missing evidence, authority,
validation, or acceptance keeps work in its current state or returns it to the
earliest state needed for correction.

Blocked and rejected are dispositions, not shortcuts around the lifecycle:

- **blocked** means advancement awaits named evidence, authority, dependency,
  or decision;
- **rejected** means the current output failed a gate and must return to a named
  earlier state; and
- **deferred** means the work is intentionally removed from the active slice
  with its rationale and dependency recorded.

The canonical forward path is:

```text
Discovery
  -> Architecture
  -> Architecture Decision
  -> Specification
  -> Implementation
  -> Validation
  -> Architectural Review
  -> Acceptance
  -> Integration
  -> Complete
```

Proportional changes may omit only the states explicitly permitted by Change
Classification. Every omitted state and its justification are recorded at the
next gate. Backward transitions follow the defect, not a fixed restart rule.

### Design freeze

Implementation begins only after architecture and specification are stable
enough to implement. During Implementation:

- exploration of material design alternatives stops;
- the approved design, scope, and acceptance criteria govern the work;
- new ideas and unrelated improvements become deferred work; and
- material changes return the work to Architecture, Architecture Decision, or
  Specification as appropriate.

Design freeze never requires implementing an error. Ambiguity, contradiction,
or architectural risk stops implementation and triggers an explicit backward
transition.

### Thin vertical slices and separation of responsibility

An implementation unit is the smallest coherent, complete, independently
reviewable vertical slice. It includes the behavior and evidence needed to be
safe and useful; it excludes partial infrastructure justified only by possible
future work.

Implementation, validation, architectural review, acceptance, and integration
are distinct responsibilities. One participant may perform multiple roles, but
must identify which role it is performing and may not treat one role's output
as another role's approval. Validation does not approve architecture;
architectural approval does not replace validation.

For behavior-bearing, specification, architectural, or constitutional work,
the participant who authored or implemented the candidate cannot provide its
sole architectural approval. Any exception for low-risk work must be explicit,
authorized at the Architecture Approval gate, and recorded with its rationale.

## Roles

| Role | Responsibility and authority | Required inputs | Required outputs |
|---|---|---|---|
| **Sponsor** | Owns the objective, explains why it matters, defines outcome constraints, resolves product intent, and accepts or rejects the delivered outcome. The Sponsor does not override constitutional or architectural authority. | Need, context, constraints, affected stakeholders, success intent | Problem statement, priority and scope authority, acceptance decision, approved deferrals |
| **Principal Architect** | Owns long-term consistency, constitutional alignment, boundaries, decomposition, dependency order, and architectural decisions. Authorizes architecture and design freeze. | Problem statement, governing artifacts, repository evidence, risks and alternatives | Architectural analysis, slice boundaries, dependency model, ADR or recorded decision, implementation-readiness decision |
| **Specification Author** | Converts approved architecture into normative behavior, invariants, contracts, failure semantics, and testable acceptance criteria. Cannot invent architecture. | Approved architecture and decisions, existing specifications and conventions | Normative specification or scoped amendment, acceptance criteria, conformance obligations |
| **Implementation Engineer** | Implements the approved slice without expanding scope or changing higher-order authority. Stops on material ambiguity. | Frozen design and specification, focused task, dependency state, acceptance criteria | Branch, code or documentation change, commit, PR, implementation report, deferred-work record |
| **Validator** | Objectively verifies required behavior and repository quality through tests and other reproducible checks. Reports executed and unexecuted validation exactly. Does not approve architecture. | Candidate change, validation plan, acceptance and conformance criteria | Validation evidence, failures, reproducible commands and results, completion disposition |
| **Architectural Reviewer** | Independently assesses architecture, specification compliance, boundaries, coupling, simplicity, maintainability, and needless abstraction. Does not substitute opinion for missing validation and cannot self-approve work it solely authored or implemented where independent approval is required. | Candidate diff, governing artifacts, validation evidence, direct dependency state | Review findings classified by severity, approval or request for changes, required return state |
| **Integrator** | Owns merge readiness, dependency and stacked-PR coordination, merge order, integration checks, and final integration reporting. Cannot waive failed gates. | Accepted PRs, dependency graph, validation and review evidence, repository state | Merge-readiness decision, ordered integration, updated dependency state, integration and completion report |

Where constitutional action requires an authority not represented by these
engineering roles, the Constitution determines the eligible decision-maker.
That authority must be recorded; no lifecycle role acquires it implicitly.

## Lifecycle States

### 1. Discovery

- **Purpose:** Establish the need, intended outcome, constraints, and whether
  repository change is warranted.
- **Responsible role:** Sponsor.
- **Required inputs:** Observed need, defect, opportunity, obligation, or review
  finding.
- **Permitted:** Evidence gathering, impact framing, scope hypotheses, and
  identification of affected authority and dependencies.
- **Prohibited:** Implementation, architectural commitment, or promised design.
- **Required outputs:** Proportional problem statement, desired outcome,
  constraints, initial acceptance intent, and known dependencies.
- **Exit criteria:** Sponsor confirms the problem is real, bounded enough for
  architectural analysis, and authorized to proceed.
- **Next states:** Architecture; Complete when no change is needed; deferred.
- **Stop/rejection:** Unclear objective, absent Sponsor authority, duplicate
  work, insufficient evidence, or conflict with higher-order authority.

### 2. Architecture

- **Purpose:** Determine boundaries, alternatives, dependencies, risks, and the
  smallest coherent slices.
- **Responsible role:** Principal Architect.
- **Required inputs:** Approved problem statement and governing repository
  artifacts.
- **Permitted:** Repository analysis, alternative evaluation, dependency and
  authority modeling, and slice decomposition.
- **Prohibited:** Production implementation or treating an explored option as
  approved.
- **Required outputs:** Architectural analysis, recommended design, rejected
  alternatives, risks, affected artifacts, and proposed slice order.
- **Exit criteria:** The recommendation is constitutionally compatible,
  sufficiently complete for an explicit decision, and has no hidden authority
  boundary.
- **Next states:** Architecture Decision; Discovery if scope or objective must
  change; blocked.
- **Stop/rejection:** Constitutional conflict, missing Design Authority choice,
  unsafe boundary, or unresolved material ambiguity.

### 3. Architecture Decision

- **Purpose:** Make the recommended design and boundaries attributable and
  stable.
- **Responsible role:** Principal Architect, subject to any higher required
  authority.
- **Required inputs:** Architectural analysis, alternatives, consequences, and
  identified authority.
- **Permitted:** Approval, rejection, amendment, and recording of the decision.
- **Prohibited:** Informal approval without durable evidence or silent amendment
  of higher-order documents.
- **Required outputs:** Accepted ADR when the decision is durable or
  cross-cutting; otherwise a recorded scoped decision, slice boundaries,
  dependency order, and explicit deferrals.
- **Exit criteria:** One design is approved, decision authority is attributable,
  consequences are understood, and prerequisites are named.
- **Next states:** Specification; Architecture for revision; Discovery when the
  objective changes; rejected or deferred.
- **Stop/rejection:** Missing authority, unresolved contradiction, or a decision
  too vague to specify deterministically.

### 4. Specification

- **Purpose:** Define observable behavior and completion criteria without
  reopening architecture.
- **Responsible role:** Specification Author.
- **Required inputs:** Approved architecture decision, direct dependencies, and
  existing normative vocabulary.
- **Permitted:** Define contracts, invariants, state transitions, lineage,
  failure behavior, validation obligations, and acceptance criteria.
- **Prohibited:** Runtime implementation, architectural expansion, or weakening
  authority to simplify fixtures.
- **Required outputs:** Proportional normative specification, acceptance
  criteria, conformance implications, and focused implementation boundary.
- **Exit criteria:** Behavior is unambiguous, testable, consistent with approved
  architecture, and complete enough to freeze design.
- **Next states:** Implementation after the implementation-readiness gate;
  Architecture Decision for design change; Specification rework.
- **Stop/rejection:** Untestable requirements, contradictory terminology,
  missing failure semantics, or incomplete dependency contracts.

### 5. Implementation

- **Purpose:** Realize one approved thin slice.
- **Responsible role:** Implementation Engineer.
- **Required inputs:** Frozen design, approved specification and acceptance
  criteria, correct dependency state, and focused implementation task.
- **Permitted:** In-scope code, tests, executable contracts, documentation, and
  necessary integration within the approved slice.
- **Prohibited:** Material design changes, unrelated refactoring, speculative
  infrastructure, or downstream work.
- **Required outputs:** Focused branch, coherent commits and PR, implementation
  evidence, and explicit deferrals.
- **Exit criteria:** The slice is complete against its specification, local
  self-review passes, and it is ready for independent validation.
- **Next states:** Validation; Specification or Architecture Decision when a
  defect in the frozen design is exposed; blocked.
- **Stop/rejection:** Ambiguity, unsafe design, wrong dependency, inseparable
  user work, or inability to meet an invariant within scope.

### 6. Validation

- **Purpose:** Produce objective, reproducible evidence that the candidate meets
  its defined requirements.
- **Responsible role:** Validator.
- **Required inputs:** Candidate change, required checks, acceptance criteria,
  and intended dependency state.
- **Permitted:** Tests, builds, static analysis, formatting, deterministic and
  replay checks, conformance verification, diagnostics, and diff inspection.
- **Prohibited:** Architectural approval, hiding unexecuted checks, or changing
  requirements to make validation pass.
- **Required outputs:** Exact commands, results and counts, failures, omissions,
  environment, and pass/fail disposition.
- **Exit criteria:** All mandatory checks pass and omissions, if any, are
  explicitly authorized and immaterial to acceptance.
- **Next states:** Architectural Review; Implementation for implementation
  defects; Specification or Architecture Decision for contract/design defects.
- **Stop/rejection:** Failed mandatory check, irreproducible result, incomplete
  evidence, or validation against the wrong dependency state.

### 7. Architectural Review

- **Purpose:** Independently determine whether the validated candidate remains
  architecturally sound and is the simplest complete compliant slice.
- **Responsible role:** Architectural Reviewer.
- **Required inputs:** Direct-base diff, governing artifacts, implementation
  report, and completed validation evidence.
- **Permitted:** Trace boundaries and lineage, compare specification to behavior,
  assess coupling and maintainability, and classify findings.
- **Prohibited:** Approving solely because tests pass, adding unrelated review
  scope, or silently repairing the candidate while acting as reviewer.
- **Required outputs:** Evidence-backed findings, severity, required correction
  and return state, and approval or request for changes.
- **Exit criteria:** No blocking finding remains and architectural approval is
  explicit and attributable.
- **Next states:** Acceptance; Implementation, Specification, Architecture
  Decision, or Architecture according to the earliest affected concern.
- **Stop/rejection:** Missing evidence, architecture/specification divergence,
  unsafe coupling, silent scope expansion, or unnecessary framework design.

### 8. Acceptance

- **Purpose:** Decide whether the result satisfies the authorized objective and
  acceptance criteria.
- **Responsible role:** Sponsor.
- **Required inputs:** Architecturally approved candidate, validation evidence,
  acceptance criteria, findings, and deferrals.
- **Permitted:** Accept, reject with evidence, or approve explicit nonblocking
  deferrals.
- **Prohibited:** Waiving constitutional requirements, unresolved blocking
  findings, or mandatory validation without the required authority.
- **Required outputs:** Attributable acceptance decision, accepted scope,
  disposition of findings, and authorized next state.
- **Exit criteria:** Sponsor accepts the result and all blocking findings are
  resolved.
- **Next states:** Integration; an earlier state matching the rejection cause;
  deferred.
- **Stop/rejection:** Objective not met, unacceptable tradeoff, unresolved
  blocker, or changed Sponsor intent requiring rediscovery.

### 9. Integration

- **Purpose:** Incorporate accepted work in dependency order without changing
  its approved meaning.
- **Responsible role:** Integrator.
- **Required inputs:** Accepted candidate, merge-ready PR, dependency graph,
  required checks, and integration authorization.
- **Permitted:** Base verification or retargeting, ordered merge, post-merge
  validation, dependency-state updates, and integration reporting.
- **Prohibited:** Squashing, rewriting, retargeting, merging, or deleting
  branches contrary to approved repository strategy; merging around failed
  gates.
- **Required outputs:** Integrated commit identity, updated dependency state,
  post-merge evidence, and integration report.
- **Exit criteria:** Correct revision is integrated at the correct dependency
  point, required post-merge checks pass, and downstream bases are accurately
  represented.
- **Next states:** Complete; Implementation or Validation for integration
  defect; an earlier state for material semantic change.
- **Stop/rejection:** Merge conflict that changes meaning, stale or expanded
  diff, unmet dependency, failed check, or absent merge authority.

### 10. Complete

- **Purpose:** Record that the accepted objective is integrated and no required
  lifecycle action remains.
- **Responsible role:** Integrator records completion; Sponsor owns the accepted
  outcome.
- **Required inputs:** Acceptance decision, successful integration, final
  validation evidence, resolved or deferred findings, and current dependency
  state.
- **Permitted:** Final reporting and handoff of explicitly deferred work.
- **Prohibited:** Treating merge alone as completion or silently retaining
  required corrective work.
- **Required outputs:** Completion report with final identities, evidence,
  findings disposition, dependency status, and deferred-work references.
- **Exit criteria:** All required artifacts and decisions are attributable and
  no blocking work remains.
- **Next states:** None. A later defect or new need begins a new lifecycle and
  references this completed work.
- **Stop/rejection:** Missing acceptance, failed integration evidence, unresolved
  blocker, inaccurate dependency state, or incomplete final report.

## Decision Gates

| Gate | Required evidence | Decision authority | Outcomes | Failed gate behavior |
|---|---|---|---|---|
| **Ready for Architecture** | Problem, objective, constraints, Sponsor authority | Sponsor | proceed, defer, close | Remain in Discovery |
| **Architecture Approval** | Analysis, alternatives, boundaries, dependencies, constitutional alignment | Principal Architect or higher required authority | approve, revise, reject | Return to Architecture or Discovery |
| **Specification Readiness** | Recorded decision, stable vocabulary, named slices and prerequisites | Principal Architect | authorize specification, revise | Return to Architecture Decision |
| **Implementation Readiness** | Complete specification, testable acceptance criteria, correct dependencies, frozen design | Principal Architect with Specification Author attestation | authorize implementation, revise, block | Remain in Specification or return to decision |
| **Validation Completion** | All mandatory objective checks and exact results | Validator | pass, fail, blocked | Return to the earliest defective state |
| **Architectural Approval** | Direct-base diff, governing artifacts, validation evidence, no blockers | Architectural Reviewer | approve, request changes, block | Return to named earlier state |
| **Acceptance** | Validated and architecturally approved result, criteria and findings disposition | Sponsor | accept, reject, defer | Return according to rejection cause |
| **Merge Readiness** | Accepted PR, correct base and dependency order, clean checks and diff | Integrator | authorize merge, rebase/retarget, block | Remain in Integration or return for correction |
| **Lifecycle Completion** | Integrated identity, post-merge evidence, final dependency and findings state | Integrator | complete, reopen correction | Remain in Integration or begin named correction lifecycle |

An exception to a gate must identify its authority, scope, rationale, risk, and
expiry or completion condition. The authority must own the requirement being
excepted; Sponsor preference alone cannot waive architecture, validation, or
constitutional requirements. A prompt-level procedural override is not a gate
exception. No exception may waive the Constitution.

## Revisions, Rejections, and Deferred Work

Rework returns to the earliest state that can resolve the actual defect:

- failed code or fixture behavior returns to Implementation;
- missing or contradictory behavior returns to Specification;
- invalid boundaries or authority return to Architecture Decision or
  Architecture;
- a changed objective returns to Discovery;
- stale dependency or mechanical merge failure remains in Integration unless it
  changes semantics; and
- failed objective acceptance returns to the state responsible for the gap.

After correction, all downstream gates affected by the change must run again.
Unaffected earlier evidence may be retained when its applicability is recorded.

New ideas, cleanup, speculative abstractions, unrelated refactors, and future
capabilities are recorded as deferred work with rationale, dependency, and
suggested entry state. Deferral creates no implementation authority and does
not count as completion of the deferred item.

## Stacked Pull Requests

Each stacked PR is its own lifecycle work item and targets its immediate
prerequisite branch. It must contain one independently reviewable incremental
slice and be validated against the exact intended dependency state.

The stack advances and integrates in dependency order. When an upstream PR
changes:

1. stabilize and validate the upstream correction;
2. return the immediate child to Implementation for rebase and reconciliation;
3. return it to Specification or Architecture Decision if inherited semantics
   changed materially;
4. re-run affected Validation, Architectural Review, and Acceptance gates;
5. propagate the corrected dependency one child at a time; and
6. merge only in dependency order, verifying each next base after its parent
   integrates.

Never repair a parent through a descendant, copy later work backward, validate
against synthetic filtered history, or let a child claim its parent's changes
as its own diff.

## Required Artifacts and Proportionality

Artifacts are required when they carry unique authority or evidence; otherwise
use the smallest durable record that supports the gate.

| Artifact | Requirement |
|---|---|
| Problem statement and acceptance intent | Mandatory, but may be one concise issue or prompt for small work |
| Architectural analysis | Mandatory for architectural, constitutional, cross-boundary, or materially ambiguous work; brief impact assessment is sufficient for established patterns |
| ADR | Mandatory for durable, cross-cutting, or hard-to-reverse architectural decisions; unnecessary when an accepted ADR already governs the choice |
| Slice or milestone definition | Mandatory for dependency stacks or multi-PR outcomes; optional for one isolated change |
| Normative specification | Mandatory for new or changed normative behavior; reference the existing specification when behavior is unchanged |
| Acceptance criteria | Mandatory and proportional for every change |
| Implementation prompt | Required when implementation is delegated; otherwise the accepted issue or work record may serve |
| Branch, commit, and pull request | Required for repository integration unless the repository explicitly permits a smaller path |
| Validation evidence | Mandatory for every integrated change; depth is proportional to risk |
| Architectural review | Mandatory for architectural/specification changes and behavior-bearing slices; lightweight review may suffice for non-normative documentation |
| Acceptance decision | Mandatory; may be concise for low-risk work |
| Integration report | Mandatory when dependencies, merge order, or post-merge checks matter; otherwise a final PR record may suffice |
| Deferred-work record | Required only when identified out-of-scope work must be preserved |

## Change Classification

Classification selects the shortest safe path; it never changes document
precedence or permits silent scope expansion.

| Class | Proportional lifecycle treatment |
|---|---|
| **Documentation-only, non-normative** | Discovery may be brief; Architecture, Architecture Decision, and Specification may be omitted when no authority or behavior changes. Validation, review, acceptance, and integration remain proportional. |
| **Implementation within existing architecture** | Reference existing decisions and specifications. Architecture may be an impact check and Architecture Decision may be unnecessary. Implementation through Integration remains required. |
| **Specification change** | Requires architectural impact assessment, Specification, Validation, independent Architectural Review, Acceptance, and Integration. Use Architecture Decision if boundaries or authority change. |
| **Architectural change** | Requires all states and explicit Architecture Decision. No design-freeze or independent-review shortcut. |
| **Constitutional change** | Requires all states plus the amendment authority and process defined by the Constitution. No engineering role may shorten it. |
| **Corrective change in a stack** | Enter at the earliest state implicated by the defect, then re-run every affected downstream gate and propagate dependencies in order. |
| **Urgent defect correction** | Discovery and documentation may be concise, but authority, objective validation, review, acceptance, and controlled integration remain explicit. Any emergency exception must already be authorized by higher-order rules and be recorded. |

## Implementation Prompt Boundary

This lifecycle determines what work is approved, its current state, governing
artifacts, acceptance criteria, dependencies, and whether implementation may
begin. `CODEX_PLAYBOOK.md` determines how Codex, when acting as Implementation
Engineer, performs that approved work.

An implementation prompt translates an approved lifecycle decision into one
focused task. It identifies the direct dependency, scope, invariants,
exclusions, validation, Git/PR requirements, and stopping point. It must not
reopen design, manufacture missing authority, or introduce unapproved
architectural decisions. A discovered design defect causes a backward lifecycle
transition rather than prompt-level invention.

## Standard State-Change Report

Use this lightweight record whenever work changes state:

```text
Work item:
Current state:
Completed outputs:
Evidence:
Decision:
Blockers or findings:
Next authorized state:
Deferred work:
Responsible role:
```

Omit empty optional fields only when their absence is unambiguous. The decision
and responsible role must always be attributable.

## Completion Criteria

Work is Complete only when, as applicable:

- the approved thin slice is implemented and accepted;
- required validation is complete and accurately recorded;
- architectural approval is explicit;
- integration occurred at the correct dependency point;
- post-integration evidence passes;
- findings are resolved or explicitly accepted as nonblocking and deferred;
- downstream dependency state is accurate; and
- final reporting identifies the integrated result and remaining deferred work.

Opening or merging a PR is evidence of activity, not by itself lifecycle
completion.
