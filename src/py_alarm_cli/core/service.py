"""AlarmService: CRUD + enable/disable + snooze/dismiss + due logic."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

from py_alarm_cli.core.models import Alarm, DAY_NAMES

LOG = logging.getLogger("py-alarm-cli")
_WEEKDAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class AlarmService:
    def __init__(self, repo, logger=None) -> None:
        self.repo = repo
        self.log = logger or LOG

    # -- helpers ------------------------------------------------------
    def list_alarms(self) -> list[Alarm]:
        return self.repo.load()

    def get(self, alarm_id: str) -> Alarm:
        for alarm in self.repo.load():
            if alarm.id == alarm_id:
                return alarm
        raise KeyError(f"unknown alarm id: {alarm_id}")

    def _persist(self, alarms: list[Alarm]) -> None:
        self.repo.save(alarms)

    # -- CRUD ---------------------------------------------------------
    def create(self, time: str, message: str, days: list[str] | None = None) -> Alarm:
        alarm = Alarm(id=uuid.uuid4().hex[:8], time=time, message=message, days=list(days or []))
        alarms = self.repo.load() + [alarm]
        self._persist(alarms)
        self.log.info("alarm_created time=%s", alarm.time, extra={"alarm_id": alarm.id})
        return alarm

    def update(self, alarm_id: str, **kwargs) -> Alarm:
        alarms = self.repo.load()
        for i, alarm in enumerate(alarms):
            if alarm.id == alarm_id:
                data = {
                    "id": alarm.id,
                    "time": kwargs.get("time", alarm.time),
                    "message": kwargs.get("message", alarm.message),
                    "enabled": kwargs.get("enabled", alarm.enabled),
                    "days": kwargs.get("days", alarm.days),
                    "snoozed_until": kwargs.get("snoozed_until", alarm.snoozed_until),
                }
                updated = Alarm(**data)
                alarms[i] = updated
                self._persist(alarms)
                self.log.info("alarm_updated", extra={"alarm_id": alarm_id})
                return updated
        raise KeyError(f"unknown alarm id: {alarm_id}")

    def delete(self, alarm_id: str) -> None:
        alarms = [a for a in self.repo.load() if a.id != alarm_id]
        self._persist(alarms)
        self.log.info("alarm_deleted", extra={"alarm_id": alarm_id})

    def set_enabled(self, alarm_id: str, enabled: bool) -> Alarm:
        return self.update(alarm_id, enabled=bool(enabled))

    # -- snooze / dismiss ---------------------------------------------
    def snooze(self, alarm_id: str, minutes: int = 5, now: datetime | None = None) -> Alarm:
        now = now or datetime.now()
        until = (now + timedelta(minutes=minutes)).isoformat()
        updated = self.update(alarm_id, snoozed_until=until)
        self.log.info("alarm_snoozed minutes=%d", minutes, extra={"alarm_id": alarm_id})
        return updated

    def dismiss(self, alarm_id: str) -> Alarm:
        updated = self.update(alarm_id, snoozed_until=None)
        self.log.info("alarm_dismissed", extra={"alarm_id": alarm_id})
        return updated

    # -- due -----------------------------------------------------------
    def due_alarms(self, now: datetime) -> list[Alarm]:
        today = _WEEKDAY[now.weekday()]
        hhmm = now.strftime("%H:%M")
        due: list[Alarm] = []
        for alarm in self.repo.load():
            if not alarm.enabled:
                continue
            if alarm.snoozed_until is not None:
                try:
                    snoozed = datetime.fromisoformat(alarm.snoozed_until)
                except ValueError:
                    snoozed = None
                if snoozed is not None:
                    ref = now
                    if snoozed > ref:
                        continue  # snoozed into the future: not due yet
                    due.append(alarm)
                    continue
            if hhmm == alarm.time and (not alarm.days or today in alarm.days):
                due.append(alarm)
        # keep DAY_NAMES referenced for spec parity
        _ = DAY_NAMES
        return due
