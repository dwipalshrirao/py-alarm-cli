"""Pure formatting helpers for the alarm table (no Textual imports needed)."""
from __future__ import annotations

from datetime import datetime

from py_alarm_cli.core.models import DAY_NAMES, next_ring

_DAY_INDEX = {d: i for i, d in enumerate(DAY_NAMES)}


def format_days(days: list[str]) -> str:
    if not days:
        return "Everyday"
    ordered = sorted(days, key=lambda d: _DAY_INDEX[d])
    if ordered == ["Mon", "Tue", "Wed", "Thu", "Fri"]:
        return "Mon-Fri"
    if ordered == ["Sat", "Sun"]:
        return "Sat-Sun"
    if ordered == list(DAY_NAMES):
        return "Everyday"
    idx = [_DAY_INDEX[d] for d in ordered]
    if len(idx) > 1 and idx == list(range(idx[0], idx[0] + len(idx))):
        return f"{ordered[0]}-{ordered[-1]}"
    return ",".join(ordered)


def format_next(alarm, now: datetime) -> str:
    """Human countdown, always containing the alarm time for clarity."""
    if not alarm.enabled:
        return "--"
    target = next_ring(alarm, now)
    delta_s = max(0, int((target - now).total_seconds()))
    hours, rem = divmod(delta_s, 3600)
    minutes = rem // 60
    if delta_s < 3600:
        return f"in {minutes}m ({alarm.time})"
    if hours < 24:
        return f"in {hours}h {minutes:02d}m ({alarm.time})"
    days = delta_s // 86400
    if days == 1:
        return f"Tomorrow {alarm.time}"
    return f"in {days}d ({alarm.time})"


def format_clock(now: datetime) -> str:
    """Current time with seconds for the TUI header, e.g. '14:05:09'."""
    return now.strftime("%H:%M:%S")


def get_status(alarm, now: datetime) -> str:
    if not alarm.enabled:
        return "Disabled"
    if alarm.snoozed_until:
        try:
            snoozed = datetime.fromisoformat(alarm.snoozed_until)
        except ValueError:
            snoozed = None
        if snoozed is not None and snoozed > now:
            return "Snoozed"
    return "Enabled"
