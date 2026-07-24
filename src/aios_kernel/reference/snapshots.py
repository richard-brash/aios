"""Configured coherent snapshot reader for deterministic tests."""
from dataclasses import dataclass
from ..snapshots import SnapshotResult
@dataclass
class BoundSnapshotReader:
    result: SnapshotResult
    calls: int = 0
    def bind(self, organization_id, actor_id):
        self.calls += 1
        return self.result
