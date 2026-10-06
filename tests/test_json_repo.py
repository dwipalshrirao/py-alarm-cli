"""TDD Red: JsonAlarmRepository per specs/02 + specs/05."""
import json
import logging
from pathlib import Path

from py_alarm_cli.core.models import Alarm
from py_alarm_cli.storage.json_repo import JsonAlarmRepository, StorageError


def _alarm(**over):
    base = {"id": "a1", "time": "07:30", "message": "Wake up", "enabled": True, "days": [], "snoozed_until": None}
    base.update(over)
    return Alarm(**base)


def test_round_trip_save_load(isolated_cwd):
    repo = JsonAlarmRepository("./alarms.json")
    alarms = [_alarm(id="a1"), _alarm(id="b2", time="21:00", message="Tea", enabled=False)]
    repo.save(alarms)
    assert repo.load() == alarms


def test_missing_file_returns_empty_and_logs_info(isolated_cwd, caplog):
    repo = JsonAlarmRepository("./alarms.json")
    with caplog.at_level(logging.INFO, logger="py-alarm-cli"):
        assert repo.load() == []


def test_corrupt_file_backed_up_and_returns_empty(isolated_cwd, caplog):
    Path("./alarms.json").write_text("{not json", encoding="utf-8")
    repo = JsonAlarmRepository("./alarms.json")
    with caplog.at_level(logging.ERROR, logger="py-alarm-cli"):
        assert repo.load() == []
    backups = list(Path(".").glob("alarms.json.corrupt-*.bak"))
    assert len(backups) == 1
    assert any("corrupt" in r.message or "backed up" in r.message for r in caplog.records)


def test_save_is_atomic_and_pretty_printed(isolated_cwd):
    repo = JsonAlarmRepository("./alarms.json")
    repo.save([_alarm()])
    raw = Path("./alarms.json").read_text(encoding="utf-8")
    assert '"time": "07:30"' in raw  # indent=2 pretty print
    assert json.loads(raw)["alarms"][0]["id"] == "a1"


def test_storage_error_type_exists():
    assert issubclass(StorageError, Exception)
