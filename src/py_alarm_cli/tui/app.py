"""Textual AlarmApp: table + keybindings, all mutations via AlarmService."""
from __future__ import annotations

import logging
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Static

from py_alarm_cli.core.ringer import TerminalBellRinger
from py_alarm_cli.core.scheduler import Scheduler
from py_alarm_cli.tui.screens import AddEditModal, ConfirmDelete, RingModal
from py_alarm_cli.tui.widgets import format_clock, format_days, format_next, get_status

LOG = logging.getLogger("py-alarm-cli")


class AlarmApp(App):
    BINDINGS = [
        ("a", "add", "Add"),
        ("e", "edit", "Edit"),
        ("d", "delete", "Delete"),
        ("space", "toggle", "On/Off"),
        ("s", "snooze", "Snooze"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, service, scheduler=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = service
        self.scheduler = scheduler or Scheduler(service, TerminalBellRinger(use_platform_default=True))
        self.table: DataTable | None = None
        self.clock: Static | None = None
        self._ring_open = False

    def compose(self) -> ComposeResult:
        yield Header()
        clock = Static(format_clock(datetime.now()), id="clock")
        self.clock = clock
        yield clock
        table = DataTable(id="alarms")
        table.add_columns("Time", "Days", "Message", "Next", "Status")
        self.table = table
        yield table
        yield Static("[a]dd [e]dit [d]elete [space] on/off [s]nooze [q]uit", id="hints")
        yield Footer()

    async def on_mount(self) -> None:
        self.refresh_table()
        self.update_clock()
        self.set_interval(1.0, self.update_clock)
        self.set_interval(1.0, self.poll_alarms)

    def update_clock(self) -> None:
        if self.clock is not None:
            self.clock.update(format_clock(datetime.now()))

    # -- live trigger -------------------------------------------------
    def poll_alarms(self) -> None:
        """1s tick: ring due alarms via scheduler, pop RingModal (no stacking)."""
        if self._ring_open:
            return
        try:
            due = self.scheduler.tick()
        except Exception as exc:
            LOG.error("scheduler tick failed: %s", exc)
            return
        if due:
            self.show_ring(due[0].id)

    # -- table --------------------------------------------------------
    def refresh_table(self) -> None:
        if self.table is None:
            return
        now = datetime.now()
        self.table.clear()
        alarms = self.service.list_alarms()
        if not alarms:
            self.table.add_row("--", "--", "No alarms — press a to add one", "--", "--")
            return
        for alarm in alarms:
            self.table.add_row(
                alarm.time,
                format_days(alarm.days),
                alarm.message,
                format_next(alarm, now),
                get_status(alarm, now),
                key=alarm.id,
            )

    def _selected_id(self) -> str | None:
        alarms = self.service.list_alarms()
        if not alarms:
            return None
        row = 0
        if self.table is not None:
            try:
                row = self.table.cursor_row or 0
            except Exception:
                row = 0
        return alarms[min(max(row, 0), len(alarms) - 1)].id

    # -- actions ------------------------------------------------------
    async def action_add(self) -> None:
        self.push_screen(AddEditModal(), self._on_add_result)

    def _on_add_result(self, result: dict | None) -> None:
        if not result:
            return
        try:
            self.service.create(time=result["time"], message=result["message"], days=result["days"])
        except ValueError as exc:
            self.notify(str(exc), severity="error")
        self.refresh_table()

    async def action_edit(self) -> None:
        alarm_id = self._selected_id()
        if alarm_id is None:
            return
        alarm = self.service.get(alarm_id)
        self.push_screen(
            AddEditModal({"time": alarm.time, "message": alarm.message, "days": ",".join(alarm.days)}),
            lambda result: self._on_edit_result(alarm_id, result),
        )

    def _on_edit_result(self, alarm_id: str, result: dict | None) -> None:
        if not result:
            return
        try:
            self.service.update(alarm_id, time=result["time"], message=result["message"], days=result["days"])
        except ValueError as exc:
            self.notify(str(exc), severity="error")
        self.refresh_table()

    async def action_delete(self) -> None:
        alarm_id = self._selected_id()
        if alarm_id is None:
            return
        alarm = self.service.get(alarm_id)
        self.push_screen(ConfirmDelete(f"{alarm.message} {alarm.time}"), lambda ok: self._on_delete_result(alarm_id, ok))

    def _on_delete_result(self, alarm_id: str, confirmed: bool) -> None:
        if confirmed:
            self.service.delete(alarm_id)
            self.refresh_table()

    async def action_toggle(self) -> None:
        alarm_id = self._selected_id()
        if alarm_id is None:
            return
        alarm = self.service.get(alarm_id)
        self.service.set_enabled(alarm_id, not alarm.enabled)
        self.refresh_table()

    async def action_snooze(self) -> None:
        alarm_id = self._selected_id()
        if alarm_id is None:
            return
        self.service.snooze(alarm_id, minutes=5)
        self.refresh_table()

    def show_ring(self, alarm_id: str) -> None:
        alarm = self.service.get(alarm_id)
        self._ring_open = True
        self.push_screen(RingModal(alarm.message, alarm.time), lambda action: self._on_ring_result(alarm_id, action))

    def _on_ring_result(self, alarm_id: str, action: str | None) -> None:
        self._ring_open = False
        try:
            if action == "snooze":
                self.service.snooze(alarm_id, minutes=5)
                self.scheduler.resolve(alarm_id)  # re-arm: snoozed_until is future, safe to forget
                LOG.info("alarm_snoozed minutes=5", extra={"alarm_id": alarm_id})
            else:
                # Dismiss: do NOT resolve — keep this minute's fired marker so the
                # 1s poll doesn't re-ring until the minute passes.
                self.service.dismiss(alarm_id)
                LOG.info("alarm_dismissed", extra={"alarm_id": alarm_id})
        except (KeyError, ValueError) as exc:
            LOG.warning("ring resolve failed: %s", exc, extra={"alarm_id": alarm_id})
        self.refresh_table()
