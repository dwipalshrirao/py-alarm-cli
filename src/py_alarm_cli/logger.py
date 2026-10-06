"""Logging setup: stderr console + rotating file in current directory only."""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys

LOGGER_NAME = "py-alarm-cli"
LOG_FILE = "./py-alarm-cli.log"
_VALID = {"DEBUG", "INFO", "WARNING", "ERROR"}


class _AlarmIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "alarm_id"):
            record.alarm_id = "-"
        return True


def _resolve_level(level: str | None) -> int:
    name = (level if level is not None else os.getenv("PY_ALARM_LOG_LEVEL", "INFO")).upper()
    if name not in _VALID:
        return logging.INFO
    return getattr(logging, name)


def setup_logging(level: str | None = None) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    resolved = _resolve_level(level)
    # Reset handlers so repeated calls (e.g. tests) don't duplicate output.
    for handler in logger.handlers[:]:
        try:
            handler.close()
        except Exception:
            pass
        logger.removeHandler(handler)
    logger.setLevel(resolved)  # effective level follows env/arg (tests assert this)
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(name)s %(message)s [%(alarm_id)s]")
    filt = _AlarmIdFilter()

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(resolved)
    console.setFormatter(fmt)
    console.addFilter(filt)
    logger.addHandler(console)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=512_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    file_handler.addFilter(filt)
    logger.addHandler(file_handler)

    if (level if level is not None else os.getenv("PY_ALARM_LOG_LEVEL", "INFO")).upper() not in _VALID:
        logger.warning("invalid log level, falling back to INFO")

    logger.debug("logging setup level=%s file=%s", logging.getLevelName(resolved), LOG_FILE)
    return logger
