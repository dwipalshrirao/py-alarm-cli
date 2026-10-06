"""Shared fixtures: isolated cwd, fixed clock, sample alarms."""
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture()
def isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture()
def fixed_now():
    # Monday 2026-10-05 06:00 local (naive local per spec v1)
    return datetime(2026, 10, 5, 6, 0)


@pytest.fixture()
def sample_alarm_dict():
    return {
        "id": "a1b2c3",
        "time": "07:30",
        "message": "Wake up",
        "enabled": True,
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "snoozed_until": None,
    }
