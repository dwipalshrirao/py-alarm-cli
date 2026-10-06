"""JSON persistence for alarms (current directory only)."""
from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

from py_alarm_cli.core.models import Alarm

LOG = logging.getLogger("py-alarm-cli")


class StorageError(Exception):
    """Wraps file errors so the TUI can show a toast instead of crashing."""


class JsonAlarmRepository:
    def __init__(self, path: str = "./alarms.json") -> None:
        self.path = Path(path)

    def load(self) -> list[Alarm]:
        if not self.path.exists():
            LOG.info("no alarm file, starting empty file=%s", str(self.path))
            return []
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            items = data.get("alarms", []) if isinstance(data, dict) else []
            return [Alarm(**item) for item in items]
        except (OSError, ValueError, TypeError, KeyError) as exc:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = Path(f"{self.path}.corrupt-{stamp}.bak")
            try:
                os.replace(self.path, backup)
            except OSError:
                backup = self.path.with_suffix(".bak")
            LOG.error("corrupt json backed up to %s: %s", str(backup), exc)
            return []

    def save(self, alarms: list[Alarm]) -> None:
        payload = {
            "alarms": [
                {
                    "id": a.id,
                    "time": a.time,
                    "message": a.message,
                    "enabled": a.enabled,
                    "days": a.days,
                    "snoozed_until": a.snoozed_until,
                }
                for a in alarms
            ]
        }
        try:
            parent = self.path.parent
            if str(parent) not in ("", "."):
                parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=str(parent) if str(parent) else ".", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, indent=2)
                    fh.write("\n")
                os.replace(tmp, self.path)
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
            LOG.debug("saved n=%d file=%s", len(alarms), str(self.path))
        except OSError as exc:
            LOG.error("save failed file=%s: %s", str(self.path), exc)
            raise StorageError(str(exc)) from exc
