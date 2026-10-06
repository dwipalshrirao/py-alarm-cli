"""TDD Red: Scheduler tick per specs/04."""
from datetime import datetime

from py_alarm_cli.core.scheduler import Scheduler
from py_alarm_cli.core.service import AlarmService
from py_alarm_cli.storage.json_repo import JsonAlarmRepository


class FakeRinger:
    def __init__(self):
        self.rang = []

    def ring(self, alarm):
        self.rang.append(alarm.id)


def _service(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return AlarmService(JsonAlarmRepository("./alarms.json"))


def test_tick_rings_due_once(tmp_path, monkeypatch):
    service = _service(tmp_path, monkeypatch)
    alarm = service.create(time="07:30", message="m", days=[])
    ringer = FakeRinger()
    sched = Scheduler(service, ringer, get_now=lambda: datetime(2026, 10, 5, 7, 30))
    due = sched.tick()
    assert [a.id for a in due] == [alarm.id]
    assert ringer.rang == [alarm.id]


def test_tick_no_double_fire_same_minute(tmp_path, monkeypatch):
    service = _service(tmp_path, monkeypatch)
    service.create(time="07:30", message="m", days=[])
    ringer = FakeRinger()
    sched = Scheduler(service, ringer, get_now=lambda: datetime(2026, 10, 5, 7, 30))
    sched.tick()
    sched.tick()
    assert len(ringer.rang) == 1


def test_tick_ignores_disabled_and_wrong_day(tmp_path, monkeypatch):
    service = _service(tmp_path, monkeypatch)
    a = service.create(time="07:30", message="m", days=["Tue"])
    service.set_enabled(a.id, False)
    ringer = FakeRinger()
    sched = Scheduler(service, ringer, get_now=lambda: datetime(2026, 10, 5, 7, 30))
    assert sched.tick() == []
    assert ringer.rang == []
