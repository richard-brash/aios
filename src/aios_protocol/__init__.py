"""AIOS canonical logical protocol reference contracts.

Importing this package performs no I/O, clock reads, randomness, or environment
inspection. Protocol records remain in focused submodules to keep boundaries clear.
"""

from . import (
    admission, append, approvals, audit, authority, bootstrap, commands, comparison, dispositions,
    envelope, events, identifiers, memory, operations, presence, projections,
    reason_codes, reconciliation, replay, resources, schedules, subscriptions,
    tools, validation, versions,
)

__all__ = [
    "admission", "append", "approvals", "audit", "authority", "bootstrap", "commands", "comparison",
    "dispositions", "envelope", "events", "identifiers", "memory",
    "operations", "presence", "projections", "reason_codes",
    "reconciliation", "replay", "resources", "schedules", "subscriptions",
    "tools", "validation", "versions",
]
