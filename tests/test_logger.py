"""TDD Red: logging per specs/05 (cwd-only file)."""
import logging
import os
from pathlib import Path

import pytest

from py_alarm_cli.logger import setup_logging


@pytest.fixture(autouse=True)
def _clean_logger():
    yield
    for h in logging.getLogger("py-alarm-cli").handlers[:]:
        try:
            h.close()
        except Exception:
            pass
        logging.getLogger("py-alarm-cli").removeHandler(h)


def test_creates_log_file_in_cwd(isolated_cwd):
    setup_logging(level="DEBUG")
    assert Path("./py-alarm-cli.log").exists()


def test_env_level_respected(isolated_cwd, monkeypatch):
    monkeypatch.setenv("PY_ALARM_LOG_LEVEL", "DEBUG")
    logger = setup_logging()
    assert logger.getEffectiveLevel() == logging.DEBUG


def test_invalid_level_falls_back_to_info(isolated_cwd, monkeypatch):
    monkeypatch.setenv("PY_ALARM_LOG_LEVEL", "NOPE")
    logger = setup_logging()
    assert logger.getEffectiveLevel() == logging.INFO


def test_no_home_dir_paths(isolated_cwd):
    import py_alarm_cli.logger as logger_mod
    import inspect

    src = inspect.getsource(logger_mod)
    assert ".py-alarm-cli" not in src or "./py-alarm-cli.log" in src
    assert str(os.path.expanduser("~")) not in src
