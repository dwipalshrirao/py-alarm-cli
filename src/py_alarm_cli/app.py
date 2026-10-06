"""App wiring: logging + repo + service + TUI entrypoint (TUI-only)."""
from __future__ import annotations

import logging

from py_alarm_cli.core.ringer import TerminalBellRinger
from py_alarm_cli.core.scheduler import Scheduler
from py_alarm_cli.core.service import AlarmService
from py_alarm_cli.logger import setup_logging
from py_alarm_cli.storage.json_repo import JsonAlarmRepository
from py_alarm_cli.tui.app import AlarmApp

LOG = logging.getLogger("py-alarm-cli")


def main() -> None:
    setup_logging()
    repo = JsonAlarmRepository("./alarms.json")
    service = AlarmService(repo)
    ringer = TerminalBellRinger(use_platform_default=True)
    scheduler = Scheduler(service, ringer)
    LOG.info("started alarms=%d file=./alarms.json", len(service.list_alarms()))
    app = AlarmApp(service, scheduler=scheduler)
    app.run()
