"""TDD Red: AlarmService CRUD + due logic per specs/02 + specs/04."""
from datetime import datetime

import pytest

from py_alarm_cli.core.service import AlarmService
from py_alarm_cli.storage.json_repo import JsonAlarmRepository


@pytest.fixture()
def service(isolated_cwd):
    return AlarmService(JsonAlarmRepository("./alarms.json"))


def test_create_persists_and_returns_id(service):
    alarm = service.create(time="07:30", message="Wake up", days=["Mon"])
    assert alarm.id
    assert service.get(alarm.id) == alarm


def test_create_rejects_invalid(service):
    with pytest.raises(ValueError):
        service.create(time="99:99", message="bad")


def test_update_delete_toggle(service):
    alarm = service.create(time="07:30", message="Wake up")
    updated = service.update(alarm.id, message="Rise!")
    assert updated.message == "Rise!"
    toggled = service.set_enabled(alarm.id, False)
    assert toggled.enabled is False
    service.delete(alarm.id)
    with pytest.raises((KeyError, ValueError)):
        service.get(alarm.id)


def test_due_exact_minute_everyday(service):
    alarm = service.create(time="07:30", message="m", days=[])
    now = datetime(2026, 10, 5, 7, 30)  # Monday
    assert [a.id for a in service.due_alarms(now)] == [alarm.id]


def test_not_due_minute_before_or_after(service):
    service.create(time="07:30", message="m", days=[])
    assert service.due_alarms(datetime(2026, 10, 5, 7, 29)) == []
    assert service.due_alarms(datetime(2026, 10, 5, 7, 31)) == []


def test_disabled_never_due(service):
    alarm = service.create(time="07:30", message="m", days=[])
    service.set_enabled(alarm.id, False)
    assert service.due_alarms(datetime(2026, 10, 5, 7, 30)) == []


def test_day_filter_respected(service):
    service.create(time="07:30", message="m", days=["Tue"])
    assert service.due_alarms(datetime(2026, 10, 5, 7, 30)) == []  # Monday
    assert len(service.due_alarms(datetime(2026, 10, 6, 7, 30))) == 1  # Tuesday


def test_snooze_defers_and_refires(service):
    alarm = service.create(time="07:30", message="m", days=[])
    now = datetime(2026, 10, 5, 7, 30)
    assert len(service.due_alarms(now)) == 1
    service.snooze(alarm.id, minutes=5, now=now)
    # snoozed: not due at same instant anymore
    snoozed = service.get(alarm.id)
    assert snoozed.snoozed_until is not None
    service.dismiss(alarm.id)  # clear path also covered
    alarm2 = service.snooze(alarm.id, minutes=5, now=now)
    from datetime import datetime as dt

    assert service.due_alarms(dt(2026, 10, 5, 7, 35)) != []
    _ = alarm2
