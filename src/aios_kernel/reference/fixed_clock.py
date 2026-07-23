"""Configured reference clock; never reads wall time."""
from dataclasses import dataclass
from datetime import datetime
@dataclass(frozen=True, slots=True)
class FixedClock:
    value: datetime
    def __post_init__(self):
        if self.value.tzinfo is None or self.value.utcoffset() is None: raise ValueError("fixed clock requires aware time")
    def evaluation_time(self) -> datetime: return self.value
