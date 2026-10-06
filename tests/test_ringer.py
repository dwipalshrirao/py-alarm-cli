"""TDD Red: TerminalBellRinger per specs/04."""
import logging

from py_alarm_cli.core.models import Alarm
from py_alarm_cli.core.ringer import BellRinger, TerminalBellRinger


def _alarm():
    return Alarm(id="x", time="07:30", message="Wake up", days=[])


def test_protocol_exists():
    assert hasattr(BellRinger, "ring")


def test_bell_always_emits_and_never_raises(capsys):
    ringer = TerminalBellRinger(os_hook=None)
    ringer.ring(_alarm())  # must not raise
    out, _ = capsys.readouterr()
    assert "\a" in out


def test_os_hook_failure_swallowed_and_logged_warning(capsys, caplog):
    def boom():
        raise RuntimeError("no speaker")

    ringer = TerminalBellRinger(os_hook=boom)
    with caplog.at_level(logging.WARNING, logger="py-alarm-cli"):
        ringer.ring(_alarm())  # must not raise
    out, _ = capsys.readouterr()
    assert "\a" in out  # bell still emitted
    assert any(r.levelno == logging.WARNING for r in caplog.records)
