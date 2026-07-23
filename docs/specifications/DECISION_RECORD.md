# AIOS Consequential Decision Record

**Specification version:** 0.0.2
**Status:** Normative audit format

## 1. Purpose and applicability

This is the minimum standard audit format whenever AIOS makes, recommends, routes, or records a consequential Decision. A Decision is consequential when it may create a binding commitment, external effect, material cost, disclosure, rights or safety impact, production change, reputational consequence, authority change, or an outcome that is difficult or uncertain to reverse.

The record captures declared rationale and reviewable inputs. It MUST NOT require or store private model reasoning. Each identifier and evidence reference MUST resolve to the exact entity version available at decision time. Unknown, inapplicable, and not-yet-known values are distinct; a required field MUST NOT be omitted or filled with an invented value.

## 2. Required record

| Field | Minimum contract |
|---|---|
| **Decision ID** | Globally unique `decision_id`, never reused. |
| **Decision Type** | Versioned classification describing the exact class of disposition, risk class, and whether it is A0, A1, A2, A3, or A4. |
| **Organization** | Exactly one `organization_id`, plus any explicitly authorized external parties. |
| **Work Root** | Exactly one of `goal_id` or `duty_reference`, never both or neither. A duty reference identifies duty type; governing Policy, constitutional provision, Incident, compliance obligation, or maintenance mandate; accountable issuer or owner; scope; and review or completion condition. |
| **Actor** | Exactly one `initiating_actor_id`; individual `decider_actor_id` when one Actor decides; requester when different; active Role assignments; and accountable Human where required. The initiator is not automatically the decider. A model name is not sufficient. |
| **Collective Governance** | When applicable: `governing_body_id`; `participating_actor_ids`; `approver_actor_ids`; `reviewer_actor_ids`; each Human's attributable vote, consent, dissent, or recusal; current Policy versions defining eligibility, quorum, conflicts, and outcome rule; quorum result; and deterministic derivation of the collective disposition. A Governing Body is not represented as a fictional Human. Record `not_applicable` for an individual Decision. |
| **Authority** | Active `authority_grant_id`; Issuer and derivation chain; effective scope, limits, expiry, delegation, and Policy versions; precise explanation of why it covers or does not cover the Decision. |
| **Alternatives Considered** | At least the selected course, no-action or defer option, and every materially viable alternative known at the time. For each: predicted benefit, cost, risk, evidence, and reason selected or rejected. If only one alternative is known, record the search performed and limitation. |
| **Evidence Used** | Pinned identifiers and versions for supporting and material contradictory evidence; provenance, observation time, validity, classification, and relevance. Explicitly state evidence gaps and unresolved conflicts. |
| **Confidence** | Explained calibrated confidence using the approved organizational scale, with basis, uncertainty, and sensitivity to disputed assumptions. It is not authority or proof. |
| **Risks** | Affected people and Resources; legal, safety, privacy, security, financial, operational, rights, reputation, dependency, and failure risks as applicable; likelihood, impact, mitigations, residual risk, and stop conditions. |
| **Expected Benefit** | Measurable expected outcomes, beneficiaries, time horizon, evidence basis, and relationship to Goal success or the referenced duty. |
| **Expected Cost** | Money, compute, Tool calls, data exposure, elapsed time, human attention, opportunity cost, commitments, and other Resources; reservation references, uncertainty, and maximum exposure. |
| **Reversibility** | Classification and justification; restoration plan, verification method, responsible Actor, bounded cost, reversal window, and third-party reliance. If any element is absent or uncertain, classify at the higher risk. |
| **Required Approval** | Whether approval is required; constitutional or Policy basis; exact Decision sought; eligible approver or Governing Body; separation-of-duties check; proposed `approval_mode`; `usage_limit` where applicable; `used_count`; `effective_at`; `expires_at` or expiry condition; conditions; revocation triggers; review schedule where applicable; exact action, Resource, risk, and budget scope; and `approval_id` or explicit pending status. Nonresponse is never approval, and Approval remains distinct from Authority. |
| **Outcome** | `selected`, `rejected`, `deferred`, `escalated`, or `cancelled`; selected alternative; conditions; decision timestamp; resulting Command, Task, Approval, or action references. Before disposition, use `pending` rather than predicting the outcome. |
| **Follow-up Review Date** | A date or deterministic review condition, review owner, and trigger for earlier review. `not_required` is allowed only with an explicit Policy-based rationale. |
| **Result Metrics** | Named measures, baseline, target, observation period, collection method, evidence references, and actual values when available. Pending measures are explicitly marked. |
| **Lessons Learned** | Post-outcome findings: prediction accuracy, realized benefits and costs, harms or near misses, failed assumptions, evidence quality, reversibility performance, Policy or process changes, and resulting Task or Memory Record references. Before review, mark `pending`, never omit. |

The record MUST also include `created_at`, `decision_at`, current lifecycle state, `correlation_id`, `recording_command_id`, relevant `event_ids` and causal references, `task_id` and `project_id` when applicable, affected Resource and Artifact references, Tool invocation references, Incident references, record schema version, and integrity reference.

Approval modes have fixed semantics. `single_use` permits one authorized execution. `bounded_repeat` requires a positive usage limit and ends at the earliest limit, expiry, revocation, invalidation, or other condition. `standing` is permitted only for a narrowly defined recurring class of A2 activity under Policy, requires periodic review, and MUST NOT authorize A4 or unspecified A3 activity. Every use is independently attributable and checked against current Authority, Policy, budget, scope, risk, Resources, conditions, and remaining usage. Material change invalidates the Approval.

## 3. Decision process contract

1. **Frame.** Identify the exact outcome being decided, Goal or duty, affected parties, decision deadline, and constraints.
2. **Authorize.** Verify initiating and deciding Actor identities, Role, Authority Grant, Policy, reserved human powers, separation of duties, and required Approval route. For collective governance, verify each eligible Human disposition, recusals, current quorum and voting Policy, and derivation of the collective outcome.
3. **Evaluate.** Pin current evidence, expose contradictions and gaps, compare alternatives including no action, and assess benefit, cost, risk, and reversibility proportionately to consequence.
4. **Dispose.** Record one unambiguous Outcome. When authority, evidence, budget, safety, or Policy is insufficient, the valid outcomes are defer, refuse, or escalate.
5. **Approve.** Obtain every required Approval in the correct mode before execution. Material changes invalidate Approval and return the Decision to evaluation; every repeated use undergoes the independent current-state checks defined above.
6. **Execute and observe.** Link attempted and completed effects separately. Record Resource use, Tool results, affected Artifacts, uncertainty, and Incidents.
7. **Review.** At the declared date or trigger, record Result Metrics and Lessons Learned and create corrective Tasks, Memory Records, Policy proposals, or Incidents as warranted.

## 4. Immutability, correction, and supersession

The Decision as made, including pinned evidence and alternatives, is immutable. Later outcomes, metrics, and lessons append to its audit history. A factual correction MUST identify the erroneous field, reason, corrector, evidence, timestamp, and affected downstream uses without replacing the original record.

A materially revised decision creates a new `decision_id` with `supersedes_decision_id`. The new record MUST explain what changed and re-evaluate authority and approval. A superseding Decision does not retroactively authorize prior action or erase the earlier rationale.

## 5. Minimum completeness rule

The kernel MUST reject a consequential Decision Command when any required field is absent, structurally invalid, based on inaccessible evidence, or inconsistent with current authority or Policy. It MUST pause or escalate when evidence is not proportionate to risk. A syntactically complete record does not establish that the Decision is lawful, authorized, safe, or approved; all substantive checks remain mandatory.
