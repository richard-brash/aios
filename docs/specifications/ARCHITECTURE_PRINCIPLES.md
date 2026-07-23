# AIOS Architecture Principles

**Specification version:** 0.0.2
**Status:** Normative implementation constraints

## 1. Purpose

These principles constrain every implementation of the AIOS kernel and its surrounding services. They specify enduring architecture properties, not technologies. An implementation MAY choose its internal mechanisms, but it MUST demonstrate these properties through observable contracts and tests. Where principles appear to conflict, constitutional precedence, human safety, lawful conduct, least privilege, and preservation of evidence control.

## 2. Events are immutable

Accepted Events MUST be append-only. Correction, reversal, supersession, redaction, and deletion are expressed as later Events; original history is never silently rewritten.

**Why:** Immutable facts make attribution, dispute resolution, tamper detection, recovery, and chronological reconstruction possible. Mutable history lets operational power rewrite accountability.

## 3. State is derived from Events

Durable state MUST be a deterministic projection of the ordered Event stream. Caches, indexes, snapshots, conversations, model context, external systems, and administrative views are not independent sources of truth.

**Why:** One authoritative history prevents contradictory state and allows projections to be rebuilt, verified, migrated, and replaced.

## 4. The kernel is deterministic

For the same valid Event sequence and specification versions, the kernel MUST derive the same state and decisions about transition validity. Time, randomness, model inference, network results, Tool results, and external observations enter the kernel only as recorded inputs. Replay MUST produce no external effects.

**Why:** Determinism is necessary for audit, testing, recovery, incident analysis, and reliable authority enforcement. Nondeterminism at the governance boundary makes past behavior irreproducible.

## 5. Models are replaceable

No organizational identity, authority, Policy, Goal, Task, Memory Record, or audit meaning may depend on a particular model, provider, prompt, session, or context window. Model outputs are proposals or evidence-bearing observations until admitted by governed Commands and Events.

**Why:** Models change, fail, lose context, and differ across providers. The Organization must retain continuity, control, and portability through replacement.

## 6. Memory is institutional

Durable organizational knowledge MUST reside in governed Memory Records with provenance, confidence, validity, classification, retention, conflict, and supersession semantics. Chat history, hidden state, and model recollection are transient unless deliberately admitted.

**Why:** Institutions require shared, reviewable, correctable knowledge that survives individual Actors and models. Untracked recollection cannot support accountable action.

## 7. Identity is persistent

Actors, Organizations, Goals, Tasks, Grants, Decisions, Events, records, and Artifacts MUST use stable identifiers that are never reassigned. Actor identity MUST be separate from roles, credentials, models, and sessions.

**Why:** Persistent identity preserves attribution and continuity across role changes, credential rotation, model replacement, archival, and lawful deletion.

## 8. Authority is explicit

Every consequential action MUST be evaluated against an active, scoped Authority Grant and current Policy. Silence, access, capability, credentials, urgency, past behavior, confidence, and Approval alone MUST NOT be interpreted as authority.

**Why:** Explicit grants turn constitutional limits into enforceable boundaries and make delegation, expiry, revocation, and accountability inspectable.

## 9. Least privilege governs all access and action

Actors, Tools, Credentials, subscriptions, memory retrieval, and Resources MUST receive only the actions, data, duration, budget, and reach necessary for their purpose. Delegation must narrow or preserve constraints and never expand them.

**Why:** Restricting reachable effects reduces accidental harm, compromise impact, privacy exposure, resource loss, and authority escape.

## 10. Auditability is a first-class outcome

Every consequential operation MUST produce a reconstructable trace from Goal or duty and originating Command through Actor, Role, authority, Policy, evidence, Decision, Approval, Tool, Resource effects, Events, and result. Protected content may use controlled references, but required accountability cannot disappear.

**Why:** Humans can govern autonomous work only when they can establish what happened, why, under whose authority, at what cost, and with what outcome.

## 11. Asynchronous by default

Coordination between kernel, Employees, Tools, humans, and services SHOULD occur through Events and subscriptions. Components MUST tolerate delay, redelivery, partial failure, independent availability, and explicit timeout. Synchronous interaction MAY be used within a bounded operation but MUST NOT erase Event or authority boundaries.

**Why:** Organizational work is long-running and crosses unreliable human and technical boundaries. Asynchrony supports resilience, pacing, review, and independent evolution without treating immediate response as success.

## 12. Humans retain constitutional authority

The system MUST route A4 and constitutionally reserved A3 Decisions to eligible Humans, preserve meaningful review, and provide suspension, appeal, and amendment mechanisms. AI recommendations may inform but MUST NOT impersonate or substitute for accountable human disposition.

**Why:** Law and the Constitution reserve ownership, fiduciary accountability, amendments, and material human-impact powers to Humans. Automation cannot confer those powers on itself.

## 13. Small composable services

Services SHOULD have narrow responsibilities, explicit versioned contracts, independently testable failure behavior, and least-privilege access. No service should become an alternate source of authority, identity, memory, or state truth. Composition occurs through governed Commands, Events, and typed references.

**Why:** Narrow boundaries reduce hidden coupling and blast radius and allow capabilities to be replaced without replacing constitutional semantics.

## 14. The kernel owns orchestration

The kernel MUST own Command admission, identity attribution, Policy and authority evaluation, lifecycle transition validation, event ordering, idempotency, resource enforcement, approval gating, subscription authorization, and audit linkage. The kernel MUST NOT own domain reasoning or silently perform Employee work.

**Why:** Central ownership of governance semantics prevents each worker or Tool from interpreting constitutional boundaries differently, while keeping the kernel small and deterministic.

## 15. Employees own work

Employees, not the kernel, are accountable institutional Actors for planning, evidence gathering, proposals, Task execution, Tool selection within eligibility, result assessment, and escalation. Model instances assist an Employee but do not replace its identity or accountability.

**Why:** Separating governed orchestration from accountable work avoids a monolithic agent and preserves clear responsibility when models or Tools change.

## 16. Organizations own Policy

Each Organization MUST adopt, version, and govern the Policies applied within its sovereignty boundary. Lower Policies may narrow but never override applicable law, lawful human governance, the Constitution, or the Authority and Memory policies. Policy changes are attributable Events and never retroactively legitimize unauthorized acts.

**Why:** Organizations require lawful autonomy over mission and operations while a fixed precedence prevents local convenience from defeating foundational constraints.

## 17. Evidence precedes confidence

Consequential Decisions MUST pin evidence and material contradictions before relying on confidence. Confidence MUST be explained, calibrated, and treated separately from validity and authority.

**Why:** Fluent output and repeated model agreement can be wrong or share one source. Evidence permits verification; confidence alone does not.

## 18. Reversibility precedes consequence

The architecture SHOULD stage, preview, isolate, rate-limit, and verify work so that effects remain reversible where practicable. If bounded restoration cannot be demonstrated, the action MUST be classified at the higher risk and receive the corresponding authority and Approval.

**Why:** Reversibility reduces harm and creates room for learning, while honest higher-risk classification prevents optimistic assumptions from bypassing oversight.

## 19. Failure is explicit and safe

Unknown state, ambiguity, conflicting instructions, missing evidence, stale versions, uncertain effects, budget exhaustion, expired authority, Policy evaluation failure, and integrity failure MUST produce refusal, pause, reconciliation, suspension, or escalation rather than guessed success. Attempts and verified outcomes are separate facts.

**Why:** Autonomous systems encounter partial failure routinely. Failing closed preserves safety and avoids compounding an uncertain effect.

## 20. Resources are governed independently

Money, compute, Tool calls, data access, elapsed time, human attention, reputation, credentials, and other scarce or sensitive Resources MUST each support scope, reservation, consumption, monitoring, and stop conditions. Related commitments MUST be aggregated.

**Why:** A monetary limit alone cannot constrain privacy exposure, compute waste, human burden, or transaction splitting.

## 21. Privacy and provenance survive composition

Every service boundary MUST preserve organization, purpose, classification, provenance, source restrictions, validity, authority, and audit references. Derived records and Artifacts MUST link their material inputs. Retrieval and disclosure MUST be purpose-limited and least-privileged.

**Why:** Decomposing work must not strip the context needed to use data lawfully, evaluate claims, or reconstruct decisions.

## 22. Portability is a governance property

Organizations MUST be able to export and migrate identities, Events, Policies, Grants, Memory Records, provenance, Artifacts, and audit relationships without surrendering their meaning or history. Technology-specific details MUST remain subordinate to stable domain contracts.

**Why:** Sovereignty and institutional continuity cannot depend on one vendor, model, storage product, or service arrangement.

## 23. Conformance requirement

An implementation conforms only if it can demonstrate, with deterministic and adversarial tests, that:

- unauthorized, stale, expired, revoked, over-budget, and invalidly approved Commands fail closed;
- replay reconstructs equivalent state without external effects;
- model replacement preserves identity, authority, memory, and audit continuity;
- suspension prevents new affected work and preserves evidence;
- every consequential operation is reconstructable using `DECISION_RECORD.md`;
- deletion and redaction obey retention, legal-hold, provenance, and tombstone rules; and
- failures cannot bypass organization, authority, Policy, resource, or human-reserved boundaries.

Passing a test suite does not permit deviation from the Constitution or the normative contracts in this specification.
