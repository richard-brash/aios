"""Authoritative evaluation-time port."""
from __future__ import annotations
from datetime import datetime
from typing import Protocol

class Clock(Protocol):
    def evaluation_time(self) -> datetime: ...
