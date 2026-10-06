"""Background scheduler tick: find due alarms, ring once per minute."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

LOG = logging.getLogger("py-alarm-cli")


class Scheduler:
    def __init__(self, service, ringer, get_now: Callable[[], datetime] | None = None, interval: float = 1.0) -> None:
        self.service = service
        self.ringer = ringer
        self.get_now = get_now or (lambda: datetime.now().astimezone().replace(tzinfo=None))
        self.interval = interval
        self._fired: set[tuple[str, str]] = set()

    def tick(self):
        now = self.get_now()
        key = now.strftime("%Y-%m-%d %H:%M")
        due = self.service.due_alarms(now)
        fresh = [a for a in due if (a.id, key) not in self._fired]
        for alarm in fresh:
            try:
                self.ringer.ring(alarm)
            except Exception as exc:  # defensive; ringer should never raise
                LOG.warning("ringer failed: %s", exc, extra={"alarm_id": alarm.id})
            self._fired.add((alarm.id, key))
        if len(self._fired) > 500:  # prune old minute keys
            keep = {k for k in self._fired if k[1] == key}
            self._fired = keep
        return fresh

    def resolve(self, alarm_id: str) -> None:
        self._fired = {k for k in self._fired if k[0] != alarm_id}
