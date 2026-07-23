# AIOS Core Ontology

**Version:** 0.0.1
**Status:** Normative vocabulary

This ontology defines the stable concepts that AIOS implementations exchange through events and institutional records. Identifiers are durable; models, prompts, interfaces, and storage technologies are replaceable.

## Entities

### Organization

A governed unit with a mission, human ownership or governing body, policies, assets, membership, and institutional record. An organization contains roles, goals, resources, and records, and is the boundary within which authority is interpreted.

### Actor

An attributable participant capable of proposing or performing an action. Actor kinds include **Human**, **AI Employee**, **Temporary Worker**, and **Service**. Every actor has an identity, lifecycle state, and one or more role assignments; no action is attributed merely to a model name.

### Role

A named set of duties, expected capabilities, and eligible authority. A role does not itself confer unlimited permission: an active **Role Assignment** binds an actor to a role, while an **Authority Grant** defines what it may actually do.

### AI Employee and Temporary Worker

An **AI Employee** is a persistent role-bearing actor whose continuity is institutional. A **Temporary Worker** is a purpose-specific actor sponsored by an authorized AI employee or human, with explicit authority, budget, and expiry. A **Model** may implement either actor but is not the actor's identity or source of authority.

### Mission, Goal, Plan, and Task

A **Mission** declares the organization's enduring purpose. A **Goal** is an authorized desired outcome linked to the mission or a governance duty. A **Plan** orders proposed tasks and dependencies for a goal. A **Task** is an assignable unit of work with inputs, expected outputs, acceptance criteria, state, and resource bounds.

### Event

An immutable, timestamped assertion that something was proposed, decided, attempted, observed, or changed. Events are the primary coordination mechanism. Each event identifies its type, issuer, subject, correlation and causation links, payload, and provenance. Conversations may produce events but are not themselves the system of record.

### Action and Decision

An **Action** is an attempted state change by an actor using zero or more tools. It records risk, reversibility, authority, inputs, and outcome. A **Decision** selects or rejects a proposed course using evidence and policy; it records the decider, rationale, confidence, and required approvals.

### Authority Grant, Delegation, and Approval

An **Authority Grant** permits specified actions over specified resources under constraints. A **Delegation** is an authority grant derived from a delegator's existing authority. An **Approval** is a recorded authorization for a particular proposal or bounded class of action; it is not a general role or capability.

### Policy and Constitution

A **Policy** is a versioned rule governing decisions or actions. The **Constitution** is the highest internal policy. Policies have issuers, scope, effective periods, and supersession links.

### Resource, Budget, Tool, and Credential

A **Resource** is something controlled or consumed, including money, compute, data, time, human attention, reputation, and physical assets. A **Budget** bounds resource use for an actor, goal, task, or period. A **Tool** exposes capabilities for observation or action. A **Credential** enables access but never independently grants authority.

### Evidence and Claim

A **Claim** is a proposition the organization may rely on. **Evidence** supports or contradicts a claim and carries provenance, collection time, relevance, and reliability. Confidence describes belief; validity describes when and where a claim may be used.

### Institutional Record and Audit Record

An **Institutional Record** is a durable, governed representation of a fact, claim, policy, decision, commitment, or outcome. An **Audit Record** is the append-only reconstruction layer connecting actors, events, authority, evidence, actions, resources, and results. Audit records may reference protected content without exposing it broadly.

### Proposal, Approval Request, and Incident

A **Proposal** describes a contemplated decision or action, including purpose, evidence, risk, cost, and reversibility. An **Approval Request** routes a proposal to an eligible approver and records disposition and conditions. An **Incident** records actual or suspected harm, policy breach, control failure, or near miss and initiates containment and review.

## Core relationships and invariants

- An Organization **adopts** one Mission and versioned Policies, and **owns or controls** Resources and Institutional Records.
- A Human **owns or governs** an Organization; an AI Employee **serves** it.
- An Actor **occupies** a Role through a Role Assignment and **acts under** an Authority Grant.
- A Goal **advances** a Mission; a Plan **serves** a Goal; a Task **implements** a Plan or directly serves a Goal.
- A Task **is assigned to** an Actor, **consumes** a Budget, and may **invoke** a Tool.
- An Event **is emitted by** an Actor or trusted Service, **refers to** entities, and **causes or correlates with** later Events.
- A Decision **evaluates** a Proposal against Evidence and Policy; an Approval **authorizes** a bounded Action.
- An Action **must trace to** a Goal or governance duty, Actor, Authority Grant, and triggering Event.
- A Delegation **derives from** another Authority Grant and cannot exceed its scope or duration.
- An AI Employee **sponsors** each Temporary Worker and remains accountable for its bounded activity.
- An Institutional Record **is supported by** provenance and may **supersede** another record without destroying history.
- An Incident **may suspend** an Actor, Tool, Credential, Authority Grant, Task, or Action class pending review.

Entity state changes occur through recorded events. References use stable identifiers. Deletion or redaction may remove protected content, but the system retains the minimum lawful tombstone needed to preserve integrity and explain that a record changed.
