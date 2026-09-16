"""Log de operações (dados reais da sessão)."""

import time
from datetime import datetime


class LogEntry:
    __slots__ = ("ts", "date", "hour", "operation", "service", "before", "after", "result", "detail", "duration")

    def __init__(self, operation="", service="", before=None, after=None, result="OK", detail="", duration=0.0):
        now = datetime.now()
        self.ts = time.time()
        self.date = now.strftime("%d/%m/%Y")
        self.hour = now.strftime("%H:%M:%S")
        self.operation = operation
        self.service = service
        self.before = before or "—"
        self.after = after or "—"
        self.result = result
        self.detail = detail or ""
        self.duration = duration

    def as_row(self):
        return [self.date, self.hour, self.operation, self.service,
                self.before, self.after, self.result]


class LogStore:
    def __init__(self):
        self.entries = []

    def add(self, operation="", service="", before=None, after=None,
            result="OK", detail="", duration=0.0):
        self.entries.append(LogEntry(operation, service, before, after, result, detail, duration))

    def clear(self):
        self.entries.clear()

    def snapshot(self):
        return list(self.entries)


store = LogStore()