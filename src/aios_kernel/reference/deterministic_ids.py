"""Preconfigured deterministic identifiers for reference tests."""
from collections import deque
from aios_protocol.identifiers import AuditRecordId, EventId, MessageId
class DeterministicIdentifiers:
    def __init__(self, dispositions, audits, events):
        self._dispositions=deque(dispositions); self._audits=deque(audits); self._events=deque(events)
        self.calls=[]
    def disposition_id(self): self.calls.append("disposition"); return MessageId(self._dispositions.popleft())
    def audit_id(self): self.calls.append("audit"); return AuditRecordId(self._audits.popleft())
    def event_id(self): self.calls.append("event"); return EventId(self._events.popleft())
