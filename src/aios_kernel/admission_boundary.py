"""Capability-neutral trusted recording-boundary resolver port."""

from __future__ import annotations

from typing import Protocol

from aios_protocol.admission import AdmissionClaim, AdmissionResolution


class RecordingBoundaryResolver(Protocol):
    """Resolve Organization existence and Actor attribution without mutation."""

    def resolve(self, claim: AdmissionClaim) -> AdmissionResolution: ...
