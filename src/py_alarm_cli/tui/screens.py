"""Textual modals: AddEdit, ConfirmDelete, Ring.

All dialogs share a centered layout with a theme-aware border
(`$primary` / `$warning` / `$error`), so they follow the app theme.
"""
from __future__ import annotations

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

_DIALOG_CSS = """
ModalScreen {
    align: center middle;
}
ModalScreen .dialog {
    width: 60;
    height: auto;
    padding: 1 2;
    background: $surface;
}
AddEditModal .dialog {
    border: heavy $primary;
}
ConfirmDelete .dialog {
    border: heavy $warning;
}
RingModal .dialog {
    border: heavy $error;
    background: $error;
}
RingModal .dialog.dialog-alt {
    background: $surface;
}
RingModal .title {
    color: white;
}
ModalScreen .title {
    text-align: center;
    text-style: bold;
    padding-bottom: 1;
}
ModalScreen .message {
    text-align: center;
}
ModalScreen .buttons {
    align: center middle;
    height: auto;
    padding-top: 1;
}
ModalScreen .buttons Button {
    margin: 0 1;
}
"""


class ThemedModal(ModalScreen):
    """Base modal: centered dialog, border color taken from the active theme."""

    DEFAULT_CSS = _DIALOG_CSS
    SCOPED_CSS = False  # screen-level rules must match globally, not under a scope

    def _dialog(self, *children):
        return Vertical(*children, classes="dialog")


class AddEditModal(ThemedModal):
    """Add / edit form. Returns dict(time, message, days) or None on dismiss."""

    def __init__(self, initial: dict | None = None) -> None:
        super().__init__()
        self.initial = initial or {"time": "07:30", "message": "", "days": ""}

    def compose(self):
        yield self._dialog(
            Label("Add alarm" if not self.initial.get("message") else "Edit alarm", classes="title"),
            Label("Time (HH:MM)"),
            Input(value=self.initial.get("time", "07:30"), id="time"),
            Label("Message"),
            Input(value=self.initial.get("message", ""), id="message"),
            Label("Days (comma separated, empty = Everyday)"),
            Input(value=self.initial.get("days", ""), id="days"),
            Horizontal(
                Button("Save", id="save", variant="primary"),
                Button("Cancel", id="cancel"),
                classes="buttons",
            ),
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            days_raw = self.query_one("#days", Input).value.strip()
            days = [d.strip() for d in days_raw.split(",") if d.strip()] if days_raw else []
            self.dismiss(
                {
                    "time": self.query_one("#time", Input).value.strip(),
                    "message": self.query_one("#message", Input).value.strip(),
                    "days": days,
                }
            )
        else:
            self.dismiss(None)


class ConfirmDelete(ThemedModal):
    def __init__(self, label: str) -> None:
        super().__init__()
        self.label = label

    def compose(self):
        yield self._dialog(
            Label("Confirm delete", classes="title"),
            Label(f"Delete '{self.label}'? [y/N]", classes="message"),
            Horizontal(
                Button("Delete", id="yes", variant="error"),
                Button("Cancel", id="no"),
                classes="buttons",
            ),
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")


class RingModal(ThemedModal):
    BINDINGS = [
        ("enter", "dismiss_modal", "Dismiss"),
        ("s", "snooze_modal", "Snooze 5m"),
    ]

    def __init__(self, message: str, time: str) -> None:
        super().__init__()
        self._message = message
        self._time = time

    def on_mount(self) -> None:
        # Flash the dialog ~2Hz while ringing; timer dies with the screen.
        self.set_interval(0.5, self._flash)

    def _flash(self) -> None:
        try:
            self.query_one(".dialog").toggle_class("dialog-alt")
        except Exception:
            pass

    def compose(self):
        yield self._dialog(
            Label("ALARM", classes="title"),
            Label(f"{self._time}: {self._message}", classes="message"),
            Horizontal(
                Button("Dismiss (Enter)", id="dismiss", variant="primary"),
                Button("Snooze 5m (s)", id="snooze"),
                classes="buttons",
            ),
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_dismiss_modal(self) -> None:
        self.dismiss("dismiss")

    def action_snooze_modal(self) -> None:
        self.dismiss("snooze")
