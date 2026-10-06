"""BellRinger protocol + TerminalBellRinger (always bell, best-effort OS hook)."""
from __future__ import annotations

import logging
import sys
from typing import Callable, Protocol

LOG = logging.getLogger("py-alarm-cli")


class BellRinger(Protocol):
    def ring(self, alarm) -> None: ...


class TerminalBellRinger:
    """Emit terminal bell; run optional OS hook without ever raising."""

    def __init__(self, os_hook: Callable[[], None] | None = None, use_platform_default: bool = False) -> None:
        self._os_hook = os_hook
        self._use_platform_default = use_platform_default

    def ring(self, alarm) -> None:
        print("\a", end="", flush=True)
        hook = self._os_hook
        if hook is None and self._use_platform_default:
            hook = self._platform_hook()
        if hook is None:
            return
        try:
            hook()
        except Exception as exc:  # never break ringing on hook failure
            LOG.warning("bell hook failed: %s", exc, extra={"alarm_id": getattr(alarm, "id", "-")})

    @staticmethod
    def _platform_hook():  # pragma: no cover - OS-specific, exercised manually per platform
        if sys.platform.startswith("win"):
            def _win():
                import winsound  # type: ignore

                winsound.MessageBeep()

            return _win
        if sys.platform == "darwin":
            def _mac():
                import subprocess

                subprocess.Popen(
                    ["afplay", "/System/Library/Sounds/Glass.aiff"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            return _mac
        return None
