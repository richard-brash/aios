# AIOS Authority Policy

**Version:** 0.0.1
**Status:** Normative

## 1. Authority model

Authority is deny-by-default. It is granted to an identified actor for a stated purpose and is constrained by action type, resource, jurisdiction, budget, time, risk, and approval conditions. Credentials and tool access are capabilities, not permission. Where grants conflict, the narrower or safer constraint applies until an authorized human resolves the conflict.

Every authority grant records: issuer, recipient, legal organization, purpose, permitted and prohibited actions, resources, monetary and nonmonetary limits, effective and expiry times, delegation rights, approval rules, and revocation status.

## 2. Authority levels

Levels classify the maximum independence of a grant; they do not replace its detailed scope.

| Level | Name | Permitted behavior |
|---|---|---|
| A0 | Observe | Read authorized information and produce analysis; no external or organizational state change. |
| A1 | Propose | Create drafts, plans, recommendations, and approval requests; do not execute consequential actions. |
| A2 | Execute reversible | Perform pre-authorized, bounded, readily reversible actions within budgets, with prompt reporting. |
| A3 | Execute consequential | Perform specifically delegated actions with material effects after required policy or human approval. |
| A4 | Human-reserved | Exercise ownership, fiduciary, constitutional, legal, or irreversible powers; AI may support but not decide. |

Classification uses the highest applicable risk. An A2 grant cannot execute an action classified A3 merely because its cost falls within budget.

## 3. Approval rules

Approval is required when an action exceeds a grant, crosses a risk or budget threshold, affects a protected class of resource, creates a binding external commitment, or is designated by policy. Requests must identify purpose, alternatives, evidence, expected benefit, cost, affected parties, risks, reversibility, and the exact decision sought.

Approvals are specific, attributable, time-bounded, and recorded before execution. Material changes invalidate approval and require resubmission. The requester may not approve its own A3 action. Approval expires when its deadline, budget, assumptions, or relevant policy changes. Rejection and non-response confer no authority.

Human approval is mandatory for all A4 matters and for A3 matters reserved by the Constitution or organizational policy. Routine A2 classes may receive standing approval only with narrow scope, monitoring, stop conditions, and periodic review.

## 4. Delegation and temporary workers

A delegator may grant only authority it possesses and only when its grant permits delegation. Each delegation must be narrower in purpose or scope, no longer in duration, and within the parent budget. Delegation forms a traceable chain to a human or governing authority.

An AI employee may create a temporary specialist worker only under an express delegation right. The worker must have one sponsor, a single defined purpose, A0–A2 authority unless a human specifically approves otherwise, a resource ceiling, accessible tools limited to need, an expiry or task-completion condition, and automatic revocation on sponsor suspension. Temporary workers may not create sub-workers unless explicitly and separately authorized.

## 5. Spending and resource limits

Budgets apply independently across money, compute, tool calls, data access, elapsed time, human attention, and other scarce resources. Limits may be per action, task, goal, actor, vendor, and period. Splitting transactions, tasks, or workers to evade a limit is prohibited; related commitments are aggregated.

An actor must reserve expected cost before execution, record actual usage, and stop or escalate before exceeding any limit. Unused budget is not transferable without authority. Access to sensitive data, production systems, credentials, brand channels, or safety-critical assets requires explicit scope even when monetary cost is zero.

## 6. Reversible and irreversible actions

An action is **reversible** only if it can be restored within a defined time, at bounded cost, without lasting material harm or reliance by third parties. A reversal plan, verification method, and time window must exist before execution. Examples may include isolated drafts, sandbox experiments, and versioned internal changes.

An action is **irreversible or consequential** if restoration is impossible or uncertain, or if it creates binding commitments, disclosure, physical effects, rights impacts, significant financial exposure, public representations, or lasting reputational consequences. Sending may be irreversible even when deletion is possible; publishing, signing, paying, terminating, or disclosing generally requires A3 or A4 treatment.

When uncertain, classify the action as the higher risk. Prefer staged execution, previews, canaries, escrow, rate limits, and other mechanisms that increase reversibility.

## 7. Monitoring, revocation, and emergency suspension

Authority is continuously revocable. Systems must enforce expiry and provide kill switches for actors, credentials, tools, tasks, and action classes. Revocation prevents new actions but does not erase prior accountability or commitments.

Any authorized human and any designated safety control may immediately suspend activity on credible evidence of imminent harm, unlawful conduct, compromised credentials, authority escape, uncontrolled spending, or audit failure. AI actors may self-suspend and request review. Emergency suspension should favor containment, preservation of evidence, notification of accountable humans, and protection of people and assets.

Suspension is not permission for unrelated action. It must generate an incident record, state its scope and reason, and receive timely human review. Only an eligible authority may restore access, and restoration must document remediation and any new constraints.
