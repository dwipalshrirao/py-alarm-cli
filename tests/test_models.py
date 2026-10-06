"""TDD Red: Alarm model validation + next_ring() per specs/02."""
from datetime import datetime

import pytest

from py_alarm_cli.core.models import Alarm, next_ring


def test_valid_alarm_constructs(sample_alarm_dict):
    alarm = Alarm(**sample_alarm_dict)
    assert alarm.time == "07:30"
    assert alarm.message == "Wake up"
    assert alarm.enabled is True


@pytest.mark.parametrize("bad_time", ["7:30", "24:00", "07:60", "ab:cd", "", "0730", "07:30:00"])
def test_rejects_bad_time(sample_alarm_dict, bad_time):
    with pytest.raises(ValueError, match="HH:MM"):
        Alarm(**{**sample_alarm_dict, "time": bad_time})


@pytest.mark.parametrize("bad_msg", ["", "   ", "x" * 201])
def test_rejects_bad_message(sample_alarm_dict, bad_msg):
    with pytest.raises(ValueError):
        Alarm(**{**sample_alarm_dict, "message": bad_msg})


def test_rejects_bad_days(sample_alarm_dict):
    with pytest.raises(ValueError):
        Alarm(**{**sample_alarm_dict, "days": ["Funday"]})
    with pytest.raises(ValueError):
        Alarm(**{**sample_alarm_dict, "days": ["Mon", "Mon"]})


def test_days_normalized_to_mon_first_order(sample_alarm_dict):
    alarm = Alarm(**{**sample_alarm_dict, "days": ["Fri", "Mon"]})
    assert alarm.days == ["Mon", "Fri"]


def test_next_ring_later_today():
    alarm = Alarm(id="1", time="07:30", message="m", days=[])
    now = datetime(2026, 10, 5, 6, 0)  # Monday
    assert next_ring(alarm, now) == datetime(2026, 10, 5, 7, 30)


def test_next_ring_tomorrow_when_time_passed():
    alarm = Alarm(id="1", time="07:30", message="m", days=[])
    now = datetime(2026, 10, 5, 8, 0)
    assert next_ring(alarm, now) == datetime(2026, 10, 6, 7, 30)


def test_next_ring_respects_day_filter_week_wrap():
    # Only Monday; now Friday -> next Monday
    alarm = Alarm(id="1", time="07:30", message="m", days=["Mon"])
    now = datetime(2026, 10, 9, 8, 0)  # Friday
    assert next_ring(alarm, now) == datetime(2026, 10, 12, 7, 30)


def test_next_ring_prefers_snooze_when_sooner():
    alarm = Alarm(
        id="1",
        time="07:30",
        message="m",
        days=[],
        snoozed_until="2026-10-05T06:05:00",
    )
    now = datetime(2026, 10, 5, 6, 0)
    assert next_ring(alarm, now) == datetime(2026, 10, 5, 6, 5)
