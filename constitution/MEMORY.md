# AIOS Institutional Memory Policy

**Version:** 0.0.1
**Status:** Normative

## 1. Institutional record

AIOS treats durable institutional records as the organization's memory. Model context, hidden state, chat history, and generated summaries are transient working material unless deliberately admitted as records. A record becomes usable through an attributable event and must be addressable by a stable identifier.

Material policies, authority grants, approvals, commitments, decisions, claims, evidence, incidents, actions, and outcomes must be recorded. Records distinguish observed facts, third-party assertions, inferences, forecasts, decisions, and opinions.

## 2. Provenance

Every record identifies its creator, creation time, source, acquisition method, organization, applicable goal or duty, transformations, and supporting or contradictory evidence. Derived records link to their inputs and transformation method. Imported material retains source identity and licensing or usage restrictions where relevant.

Unknown provenance is explicitly marked and lowers permissible reliance. A model citation is not evidence unless the cited source is captured or independently retrievable and verified.

## 3. Confidence and validity

Confidence expresses calibrated belief, not truth. Records use an explained confidence level and, when useful, a probability or interval. Confidence must reflect evidence quality, independence, recency, and contradiction; it may not be raised solely by repeated model agreement derived from the same source.

Validity defines the contexts and time during which a record may be relied on. Records include effective time, observed time, expiration or review time where applicable, jurisdiction or scope, and validation state: unverified, corroborated, authoritative, disputed, or invalid. High-consequence decisions require evidence proportionate to risk and a fresh validity check.

## 4. Retention

Retention follows legal duties, operational value, audit needs, contractual requirements, privacy risk, and cost. Each record class has a retention schedule and accountable owner. Records under legal hold, active investigation, unresolved commitment, or constitutional audit obligation are preserved as required.

Data minimization applies at collection and throughout retention. When detailed content is no longer justified, the organization should aggregate, redact, anonymize, or delete it while retaining only the lawful metadata needed for accountability.

## 5. Supersession and correction

Records are append-corrected, not silently rewritten. A new record may supersede an earlier one and must state why, when, by whom, and which uses are affected. The earlier record remains discoverable and marked with its status unless deletion is legally or ethically required.

Contradictory records coexist as disputed claims until resolved by evidence or authorized decision. Retrieval must prefer the currently valid record while exposing material conflicts and the supersession chain. Corrections propagate to dependent active decisions and tasks when the error could alter their outcome.

## 6. Privacy and access

Information is classified by sensitivity and accessed on least-privilege, purpose-limited terms. Collection and use must be lawful, necessary, proportionate, and consistent with consent or another valid basis. Sensitive and personal data require stronger access control, encryption where appropriate, access logging, bounded sharing, and avoidance of unnecessary model exposure.

Memory retrieval must respect the requester's organization, role, authority, purpose, and jurisdiction. The ability to search or infer a record does not authorize disclosure. Outputs should reveal the minimum information needed, and audit views may use protected references or redaction.

## 7. Deletion and redaction

Records are deleted or redacted when required by law, valid human instruction, expired retention, withdrawn lawful basis, or disproportionate risk, unless a controlling preservation obligation applies. Deletion requests require identity, authority, scope, dependency, legal-hold, and audit-impact checks.

Deletion must propagate to replicas, indexes, caches, derived datasets, and future retrieval to the extent technically and legally feasible. Backups may age out under documented controls. A minimal tombstone may record that authorized deletion occurred, without retaining the deleted content or enabling reconstruction. Deletion never rewrites history to conceal wrongdoing.

## 8. Retrieval and use

Retrieval ranks records by authority, relevance, validity, provenance, recency, and confidence—not semantic similarity alone. Responses identify the supporting records, distinguish evidence from inference, surface uncertainty and conflicts, and avoid presenting expired or superseded claims as current.

Before consequential action, the actor retrieves applicable constitutional rules, authority grants, approvals, current goal state, material evidence, relevant commitments, and unresolved incidents. Retrieval itself generates an audit event when sensitive or consequential. Records used in a decision are pinned by identifier and version so the decision can later be reconstructed.

## 9. Integrity and portability

Institutional memory must be tamper-evident, recoverable, exportable, and independent of any single model or vendor. Access, mutation, supersession, and deletion events are auditable. Backups and integrity checks are tested proportionately to criticality. The organization retains the ability to migrate its records without surrendering their semantics, provenance, or authority history.
