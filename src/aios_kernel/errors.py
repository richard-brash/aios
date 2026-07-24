"""Safe kernel-internal failures, separate from protocol decisions."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class KernelInternalError(RuntimeError):
    code: str
    safe_summary: str
    def __str__(self) -> str:
        return f"{self.code}: {self.safe_summary}"
