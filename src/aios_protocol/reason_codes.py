"""Executable form of the 65 normative KERNEL_PROTOCOL reason codes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Retryability(str, Enum):
    NEVER = "never"
    AFTER_CHANGE = "after_change"
    IDEMPOTENT_ONLY = "idempotent_only"
    AFTER_RECONCILIATION = "after_reconciliation"


class Requirement(str, Enum):
    NONE = "none"
    CONDITIONAL = "conditional"
    REQUIRED = "required"


class ReasonCode(str, Enum):
    INPUT_MALFORMED = "INPUT.MALFORMED"
    INPUT_OVERSIZED = "INPUT.OVERSIZED"
    VER_UNSUPPORTED = "VER.UNSUPPORTED"
    VER_DOWNGRADE_REJECTED = "VER.DOWNGRADE_REJECTED"
    IDENTITY_UNKNOWN = "IDENTITY.UNKNOWN"
    IDENTITY_FORGED = "IDENTITY.FORGED"
    IDENTITY_SUSPENDED = "IDENTITY.SUSPENDED"
    ORG_UNKNOWN = "ORG.UNKNOWN"
    ORG_BOUNDARY_VIOLATION = "ORG.BOUNDARY_VIOLATION"
    AUTH_MISSING = "AUTH.MISSING"
    AUTH_EXPIRED = "AUTH.EXPIRED"
    AUTH_REVOKED = "AUTH.REVOKED"
    AUTH_INSUFFICIENT = "AUTH.INSUFFICIENT"
    AUTH_DELEGATION_INVALID = "AUTH.DELEGATION_INVALID"
    POLICY_DENIED = "POLICY.DENIED"
    POLICY_UNAVAILABLE = "POLICY.UNAVAILABLE"
    WORK_ROOT_MISSING = "WORK_ROOT.MISSING"
    WORK_ROOT_DUAL = "WORK_ROOT.DUAL"
    WORK_ROOT_INACTIVE = "WORK_ROOT.INACTIVE"
    WORK_ROOT_INCOMPLETE = "WORK_ROOT.INCOMPLETE"
    WORK_ROOT_INVALID_KIND = "WORK_ROOT.INVALID_KIND"
    DECISION_MISSING = "DECISION.MISSING"
    DECISION_INCOMPLETE = "DECISION.INCOMPLETE"
    DECISION_ACCOUNTABLE_DECIDER_INVALID = "DECISION.ACCOUNTABLE_DECIDER_INVALID"
    DECISION_CURRENT_CONDITIONS_INVALID = "DECISION.CURRENT_CONDITIONS_INVALID"
    APPROVAL_MISSING = "APPROVAL.MISSING"
    APPROVAL_EXPIRED = "APPROVAL.EXPIRED"
    APPROVAL_REVOKED = "APPROVAL.REVOKED"
    APPROVAL_EXHAUSTED = "APPROVAL.EXHAUSTED"
    APPROVAL_OUT_OF_SCOPE = "APPROVAL.OUT_OF_SCOPE"
    RESOURCE_UNAVAILABLE = "RESOURCE.UNAVAILABLE"
    RESOURCE_EXCEEDED = "RESOURCE.EXCEEDED"
    RESOURCE_UNVERIFIED = "RESOURCE.UNVERIFIED"
    RESOURCE_RESERVATION_CONFLICT = "RESOURCE.RESERVATION_CONFLICT"
    LIFECYCLE_INVALID_TRANSITION = "LIFECYCLE.INVALID_TRANSITION"
    STATE_STALE_VERSION = "STATE.STALE_VERSION"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY.CONFLICT"
    STREAM_CONCURRENCY_CONFLICT = "STREAM.CONCURRENCY_CONFLICT"
    EVENT_FIELD_APPLICABILITY_INVALID = "EVENT.FIELD_APPLICABILITY_INVALID"
    EVENT_PROHIBITED_FIELD = "EVENT.PROHIBITED_FIELD"
    APPEND_FAILED = "APPEND.FAILED"
    APPEND_OUTCOME_UNCERTAIN = "APPEND.OUTCOME_UNCERTAIN"
    SUBSCRIPTION_UNAUTHORIZED = "SUBSCRIPTION.UNAUTHORIZED"
    CLASSIFICATION_DENIED = "CLASSIFICATION.DENIED"
    REPLAY_SIDE_EFFECT_VIOLATION = "REPLAY.SIDE_EFFECT_VIOLATION"
    TOOL_SCOPE_VIOLATION = "TOOL.SCOPE_VIOLATION"
    ADAPTER_IDENTITY_INVALID = "ADAPTER.IDENTITY_INVALID"
    EXTERNAL_OUTCOME_UNKNOWN = "EXTERNAL.OUTCOME_UNKNOWN"
    TOOL_EVIDENCE_CONTRADICTORY = "TOOL.EVIDENCE_CONTRADICTORY"
    RECONCILIATION_REQUIRED = "RECONCILIATION.REQUIRED"
    AUDIT_LINKAGE_MISSING = "AUDIT.LINKAGE_MISSING"
    BOOTSTRAP_INCOMPLETE = "BOOTSTRAP.INCOMPLETE"
    BOOTSTRAP_GENESIS_TYPE_INVALID = "BOOTSTRAP.GENESIS_TYPE_INVALID"
    BOOTSTRAP_GENESIS_SCOPE_INVALID = "BOOTSTRAP.GENESIS_SCOPE_INVALID"
    BOOTSTRAP_IDENTITY_QUARANTINED = "BOOTSTRAP.IDENTITY_QUARANTINED"
    BOOTSTRAP_COMPETING_GENESIS = "BOOTSTRAP.COMPETING_GENESIS"
    INCIDENT_SUSPENDED = "INCIDENT.SUSPENDED"
    OPERATION_TIMEOUT = "OPERATION.TIMEOUT"
    OPERATION_CANCELLED = "OPERATION.CANCELLED"
    RETRY_PROHIBITED = "RETRY.PROHIBITED"
    GOVERNANCE_DEPENDENCY_UNAVAILABLE = "GOVERNANCE.DEPENDENCY_UNAVAILABLE"
    INTEGRITY_VERIFICATION_FAILED = "INTEGRITY.VERIFICATION_FAILED"
    RELATIONSHIP_INTEGRITY_CONFLICT = "RELATIONSHIP.INTEGRITY_CONFLICT"
    CONTENT_GOVERNED_UNAVAILABLE = "CONTENT.GOVERNED_UNAVAILABLE"
    CONTENT_CRYPTOGRAPHICALLY_ERASED = "CONTENT.CRYPTOGRAPHICALLY_ERASED"
    SCHEDULE_TRIGGER_CONFLICT = "SCHEDULE.TRIGGER_CONFLICT"

    @property
    def metadata(self) -> "ReasonMetadata":
        return REASON_METADATA[self]


@dataclass(frozen=True, slots=True)
class ReasonMetadata:
    category: str
    meaning: str
    retryability: Retryability
    reevaluation_permitted: bool
    escalation: Requirement
    incident: Requirement
    safe_disclosure_guidance: str


_MEANINGS = {
    ReasonCode.INPUT_MALFORMED: "Required structure or type is invalid",
    ReasonCode.INPUT_OVERSIZED: "Input size or depth bound is exceeded",
    ReasonCode.VER_UNSUPPORTED: "Protocol, record, or payload version is unsupported",
    ReasonCode.VER_DOWNGRADE_REJECTED: "Offered version would weaken semantics",
    ReasonCode.IDENTITY_UNKNOWN: "Actor cannot be resolved",
    ReasonCode.IDENTITY_FORGED: "Invocation proof does not bind the asserted Actor",
    ReasonCode.IDENTITY_SUSPENDED: "Actor is operationally suspended",
    ReasonCode.ORG_UNKNOWN: "Claimed Organization cannot be resolved as an authoritative boundary",
    ReasonCode.ORG_BOUNDARY_VIOLATION: "Cross-Organization reference is not authorized",
    ReasonCode.AUTH_MISSING: "No applicable Authority Grant exists",
    ReasonCode.AUTH_EXPIRED: "Authority Grant is expired",
    ReasonCode.AUTH_REVOKED: "Authority Grant is revoked",
    ReasonCode.AUTH_INSUFFICIENT: "Requested scope exceeds Authority Grant",
    ReasonCode.AUTH_DELEGATION_INVALID: "Delegation expands or lacks parent delegation right",
    ReasonCode.POLICY_DENIED: "Controlling Policy prohibits the request",
    ReasonCode.POLICY_UNAVAILABLE: "Policy cannot be evaluated reliably",
    ReasonCode.WORK_ROOT_MISSING: "Neither Goal nor duty Work Root was supplied",
    ReasonCode.WORK_ROOT_DUAL: "Both Goal and duty Work Roots were supplied",
    ReasonCode.WORK_ROOT_INACTIVE: "Work Root is not current for new work",
    ReasonCode.WORK_ROOT_INCOMPLETE: "Duty Work Root lacks a mandatory component",
    ReasonCode.WORK_ROOT_INVALID_KIND: "A non-Goal, non-duty type was claimed as Work Root",
    ReasonCode.DECISION_MISSING: "Required consequential Decision is absent",
    ReasonCode.DECISION_INCOMPLETE: "Decision or audit fields are incomplete",
    ReasonCode.DECISION_ACCOUNTABLE_DECIDER_INVALID: "Human-reserved Decision lacks an eligible accountable decider",
    ReasonCode.DECISION_CURRENT_CONDITIONS_INVALID: "Current execution conditions no longer support the historical Decision",
    ReasonCode.APPROVAL_MISSING: "A required Approval is absent",
    ReasonCode.APPROVAL_EXPIRED: "Approval is expired",
    ReasonCode.APPROVAL_REVOKED: "Approval is revoked",
    ReasonCode.APPROVAL_EXHAUSTED: "Approval usage limit is reached",
    ReasonCode.APPROVAL_OUT_OF_SCOPE: "Use differs from approved scope",
    ReasonCode.RESOURCE_UNAVAILABLE: "Required Resource dimension lacks capacity",
    ReasonCode.RESOURCE_EXCEEDED: "Resource limit or stop threshold is exceeded",
    ReasonCode.RESOURCE_UNVERIFIED: "Resource availability or consumption is unverifiable",
    ReasonCode.RESOURCE_RESERVATION_CONFLICT: "Concurrent or aggregate reservation conflicts",
    ReasonCode.LIFECYCLE_INVALID_TRANSITION: "Transition is illegal from current state",
    ReasonCode.STATE_STALE_VERSION: "Expected entity or projection version is stale",
    ReasonCode.IDEMPOTENCY_CONFLICT: "Identity or idempotency key was reused for different semantics",
    ReasonCode.STREAM_CONCURRENCY_CONFLICT: "Expected prior stream position differs",
    ReasonCode.EVENT_FIELD_APPLICABILITY_INVALID: "Event field applicability is missing, unresolved, or simulated",
    ReasonCode.EVENT_PROHIBITED_FIELD: "A field prohibited by the Event schema is present",
    ReasonCode.APPEND_FAILED: "Append is confirmed not committed due to failure",
    ReasonCode.APPEND_OUTCOME_UNCERTAIN: "Append commitment cannot be established",
    ReasonCode.SUBSCRIPTION_UNAUTHORIZED: "Subscriber lacks required scope, purpose, or Grant",
    ReasonCode.CLASSIFICATION_DENIED: "Classification access is insufficient",
    ReasonCode.REPLAY_SIDE_EFFECT_VIOLATION: "Replay attempted a live side effect",
    ReasonCode.TOOL_SCOPE_VIOLATION: "Tool request or adapter exceeds authorized scope",
    ReasonCode.ADAPTER_IDENTITY_INVALID: "Adapter identity proof is invalid",
    ReasonCode.EXTERNAL_OUTCOME_UNKNOWN: "External result cannot be determined",
    ReasonCode.TOOL_EVIDENCE_CONTRADICTORY: "Material Tool observations conflict",
    ReasonCode.RECONCILIATION_REQUIRED: "Safe state requires reconciliation",
    ReasonCode.AUDIT_LINKAGE_MISSING: "Mandatory consequential trace is absent",
    ReasonCode.BOOTSTRAP_INCOMPLETE: "Proposed founding set is incomplete before commit",
    ReasonCode.BOOTSTRAP_GENESIS_TYPE_INVALID: "Bootstrap type or classification is not reserved genesis",
    ReasonCode.BOOTSTRAP_GENESIS_SCOPE_INVALID: "Genesis includes prohibited ordinary work or reuses exhausted authority",
    ReasonCode.BOOTSTRAP_IDENTITY_QUARANTINED: "Proposed Organization identity has uncertain genesis state",
    ReasonCode.BOOTSTRAP_COMPETING_GENESIS: "A materially different genesis conflicts with the registered attempt",
    ReasonCode.INCIDENT_SUSPENDED: "Incident control blocks the operation",
    ReasonCode.OPERATION_TIMEOUT: "Required observation is absent by deadline",
    ReasonCode.OPERATION_CANCELLED: "Future operation was cancelled",
    ReasonCode.RETRY_PROHIBITED: "Retry lacks required proof or approved duplicate risk",
    ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE: "Governance dependency is unavailable",
    ReasonCode.INTEGRITY_VERIFICATION_FAILED: "Integrity proof, checkpoint, or history is invalid",
    ReasonCode.RELATIONSHIP_INTEGRITY_CONFLICT: "Derived relationship state conflicts with canonical state",
    ReasonCode.CONTENT_GOVERNED_UNAVAILABLE: "Governed availability forbids or cannot provide referenced content",
    ReasonCode.CONTENT_CRYPTOGRAPHICALLY_ERASED: "Referenced content was cryptographically erased",
    ReasonCode.SCHEDULE_TRIGGER_CONFLICT: "Schedule trigger conflicts with its registered instance",
}


_NEVER = {
    ReasonCode.INPUT_MALFORMED, ReasonCode.IDENTITY_FORGED,
    ReasonCode.ORG_BOUNDARY_VIOLATION, ReasonCode.AUTH_DELEGATION_INVALID,
    ReasonCode.IDEMPOTENCY_CONFLICT, ReasonCode.REPLAY_SIDE_EFFECT_VIOLATION,
    ReasonCode.TOOL_SCOPE_VIOLATION, ReasonCode.ADAPTER_IDENTITY_INVALID,
    ReasonCode.OPERATION_CANCELLED, ReasonCode.BOOTSTRAP_GENESIS_SCOPE_INVALID,
    ReasonCode.BOOTSTRAP_COMPETING_GENESIS, ReasonCode.CONTENT_CRYPTOGRAPHICALLY_ERASED,
}
_RECONCILE = {
    ReasonCode.RESOURCE_UNVERIFIED, ReasonCode.APPEND_OUTCOME_UNCERTAIN,
    ReasonCode.EXTERNAL_OUTCOME_UNKNOWN, ReasonCode.TOOL_EVIDENCE_CONTRADICTORY,
    ReasonCode.RECONCILIATION_REQUIRED, ReasonCode.OPERATION_TIMEOUT,
    ReasonCode.BOOTSTRAP_IDENTITY_QUARANTINED, ReasonCode.SCHEDULE_TRIGGER_CONFLICT,
}
_INCIDENT_REQUIRED = {
    ReasonCode.IDENTITY_FORGED, ReasonCode.RESOURCE_EXCEEDED,
    ReasonCode.APPEND_OUTCOME_UNCERTAIN, ReasonCode.REPLAY_SIDE_EFFECT_VIOLATION,
    ReasonCode.TOOL_SCOPE_VIOLATION, ReasonCode.ADAPTER_IDENTITY_INVALID,
    ReasonCode.BOOTSTRAP_INCOMPLETE, ReasonCode.INTEGRITY_VERIFICATION_FAILED,
    ReasonCode.BOOTSTRAP_GENESIS_SCOPE_INVALID, ReasonCode.BOOTSTRAP_IDENTITY_QUARANTINED,
    ReasonCode.BOOTSTRAP_COMPETING_GENESIS, ReasonCode.RELATIONSHIP_INTEGRITY_CONFLICT,
}
_ESCALATION_REQUIRED = {
    ReasonCode.AUTH_DELEGATION_INVALID, ReasonCode.POLICY_UNAVAILABLE,
    ReasonCode.DECISION_MISSING, ReasonCode.DECISION_INCOMPLETE,
    ReasonCode.APPROVAL_MISSING, ReasonCode.APPROVAL_OUT_OF_SCOPE,
    ReasonCode.RESOURCE_EXCEEDED, ReasonCode.APPEND_OUTCOME_UNCERTAIN,
    ReasonCode.TOOL_EVIDENCE_CONTRADICTORY, ReasonCode.AUDIT_LINKAGE_MISSING,
    ReasonCode.BOOTSTRAP_INCOMPLETE, ReasonCode.RETRY_PROHIBITED,
    ReasonCode.GOVERNANCE_DEPENDENCY_UNAVAILABLE,
    ReasonCode.INTEGRITY_VERIFICATION_FAILED, ReasonCode.DECISION_ACCOUNTABLE_DECIDER_INVALID,
    ReasonCode.BOOTSTRAP_GENESIS_TYPE_INVALID, ReasonCode.BOOTSTRAP_GENESIS_SCOPE_INVALID,
    ReasonCode.BOOTSTRAP_IDENTITY_QUARANTINED, ReasonCode.BOOTSTRAP_COMPETING_GENESIS,
    ReasonCode.RELATIONSHIP_INTEGRITY_CONFLICT,
}


REASON_METADATA = {
    code: ReasonMetadata(
        category=code.value.split(".", 1)[0],
        meaning=_MEANINGS[code],
        retryability=(
            Retryability.NEVER if code in _NEVER else
            Retryability.AFTER_RECONCILIATION if code in _RECONCILE else
            Retryability.IDEMPOTENT_ONLY if code is ReasonCode.APPEND_FAILED else
            Retryability.AFTER_CHANGE
        ),
        reevaluation_permitted=code not in _NEVER,
        escalation=Requirement.REQUIRED if code in _ESCALATION_REQUIRED else Requirement.CONDITIONAL,
        incident=Requirement.REQUIRED if code in _INCIDENT_REQUIRED else Requirement.CONDITIONAL,
        safe_disclosure_guidance="disclose only the category and authorized bounded context",
    )
    for code in ReasonCode
}

assert set(_MEANINGS) == set(ReasonCode)
assert set(REASON_METADATA) == set(ReasonCode)
