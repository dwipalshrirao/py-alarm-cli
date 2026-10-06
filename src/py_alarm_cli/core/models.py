"""Alarm model, validation, next_ring() computation."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_DAY_INDEX = {d: i for i, d in enumerate(DAY_NAMES)}
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


@dataclass(frozen=True)
class Alarm:
    id: str
    time: str  # "HH:MM" 24h
    message: str
    enabled: bool = True
    days: list[str] = field(default_factory=list)
    snoozed_until: str | None = None  # ISO datetime local

    def __post_init__(self) -> None:
        if not TIME_RE.match(self.time):
            raise ValueError("time must be HH:MM 24h")
        msg = self.message.strip() if isinstance(self.message, str) else ""
        if not msg:
            raise ValueError("message must not be empty")
        if len(msg) > 200:
            raise ValueError("message must be <= 200 chars")
        if not isinstance(self.days, list):
            raise ValueError("days must be a list")
        if any(d not in _DAY_INDEX for d in self.days):
            raise ValueError(f"days must be subset of {DAY_NAMES}")
        if len(set(self.days)) != len(self.days):
            raise ValueError("days must not contain duplicates")
        # Normalize to Mon-first order (frozen -> object.__setattr__)
        object.__setattr__(self, "days", sorted(self.days, key=lambda d: _DAY_INDEX[d]))
        if self.snoozed_until is not None:
            try:
                datetime.fromisoformat(self.snoozed_until)
            except (ValueError, TypeError) as exc:
                raise ValueError("snoozed_until must be ISO datetime") from exc


def _parse_time(time_str: str) -> tuple[int, int]:
    hour, minute = time_str.split(":")
    return int(hour), int(minute)


def next_ring(alarm: Alarm, now: datetime) -> datetime:
    """Next occurrence from time+days; min() with future snoozed_until."""
    hour, minute = _parse_time(alarm.time)
    computed: datetime | None = None
    for offset in range(8):
        day = now.date() + timedelta(days=offset)
        candidate = datetime(day.year, day.month, day.day, hour, minute)
        if offset == 0 and candidate < now:
            continue
        name = DAY_NAMES[candidate.weekday()]
        if not alarm.days or name in alarm.days:
            computed = candidate
            break
    if computed is None:  # pragma: no cover - defensive
        day = now.date() + timedelta(days=7)
        computed = datetime(day.year, day.month, day.day, hour, minute)
    if alarm.snoozed_until:
        try:
            snoozed = datetime.fromisoformat(alarm.snoozed_until)
        except ValueError:
            return computed
        # Strip tzinfo for naive comparison (spec v1 uses local naive)
        if snoozed.tzinfo is not None:
            snoozed = snoozed.replace(tzinfo=None)
        ref = now.replace(tzinfo=None) if now.tzinfo is not None else now
        if snoozed > ref:
            return min(snoozed, computed)
    return computed
