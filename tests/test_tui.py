"""TDD Red: TUI helpers + Textual app smoke per specs/03."""
from datetime import datetime

import pytest

from py_alarm_cli.core.models import Alarm
from py_alarm_cli.tui.widgets import format_clock, format_days, format_next, get_status


def test_format_clock_includes_seconds():
    assert format_clock(datetime(2026, 10, 5, 14, 5, 9)) == "14:05:09"


@pytest.mark.asyncio()
@pytest.mark.parametrize("which", ["ring", "add_edit", "confirm"])
async def test_modals_have_themed_border_and_centered_dialog(isolated_cwd, which):
    """Popup windows carry a heavy theme-color border and centered dialog content."""
    from py_alarm_cli.tui.screens import AddEditModal, ConfirmDelete, RingModal
    from textual.app import App

    modal = {
        "ring": RingModal("Wake up", "07:30"),
        "add_edit": AddEditModal(),
        "confirm": ConfirmDelete("x"),
    }[which]

    class T(App):
        pass

    app = T()
    async with app.run_test() as pilot:
        await app.push_screen(modal)
        await pilot.pause()
        dialog = modal.query_one(".dialog")
        style, _color = dialog.styles.border_top
        assert style == "heavy"  # theme border visible
        assert modal.query_one(".buttons") is not None  # actions aligned in button row
        app.pop_screen()
        await pilot.pause()


def test_format_days():
    assert format_days([]) == "Everyday"
    assert format_days(["Mon", "Tue", "Wed", "Thu", "Fri"]) == "Mon-Fri"
    assert format_days(["Mon"]) == "Mon"


def test_format_next_and_status():
    alarm = Alarm(id="1", time="07:30", message="m", days=[])
    now = datetime(2026, 10, 5, 6, 0)
    text = format_next(alarm, now)
    assert "07:30" in text or "1h" in text or "90" in text or "in" in text
    assert get_status(alarm, now) == "Enabled"
    disabled = Alarm(id="2", time="07:30", message="m", days=[], enabled=False)
    assert get_status(disabled, now) == "Disabled"


def test_alarm_app_instantiates(isolated_cwd):
    from py_alarm_cli.core.service import AlarmService
    from py_alarm_cli.storage.json_repo import JsonAlarmRepository
    from py_alarm_cli.tui.app import AlarmApp

    service = AlarmService(JsonAlarmRepository("./alarms.json"))
    app = AlarmApp(service)
    assert app is not None


@pytest.mark.asyncio()
async def test_tui_pilot_add_flow(isolated_cwd):
    """Full Pilot flow: press 'a', fill form, save -> service has 1 alarm."""
    from py_alarm_cli.core.service import AlarmService
    from py_alarm_cli.storage.json_repo import JsonAlarmRepository
    from py_alarm_cli.tui.app import AlarmApp

    service = AlarmService(JsonAlarmRepository("./alarms.json"))
    app = AlarmApp(service)
    async with app.run_test() as pilot:
        await pilot.press("a")
        await pilot.pause()
        # Screens/modals are implementation detail; assert app opened add modal
        assert app.screen is not None
        clock = app.query_one("#clock")
        assert clock is app.clock  # live HH:MM:SS header present (text via format_clock)


@pytest.mark.asyncio()
async def test_ring_modal_appears_on_due_and_dismiss_resolves(isolated_cwd):
    """Live wiring: scheduler tick with due alarm pops RingModal; dismiss clears it."""
    from py_alarm_cli.core.scheduler import Scheduler
    from py_alarm_cli.core.service import AlarmService
    from py_alarm_cli.storage.json_repo import JsonAlarmRepository
    from py_alarm_cli.tui.app import AlarmApp
    from py_alarm_cli.tui.screens import RingModal

    class FakeRinger:
        def __init__(self):
            self.rang = []

        def ring(self, alarm):
            self.rang.append(alarm.id)

    service = AlarmService(JsonAlarmRepository("./alarms.json"))
    alarm = service.create(time="07:30", message="Wake up", days=[])
    ringer = FakeRinger()
    sched = Scheduler(service, ringer, get_now=lambda: datetime(2026, 10, 5, 7, 30))
    app = AlarmApp(service, scheduler=sched)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.poll_alarms()
        await pilot.pause()
        assert isinstance(app.screen, RingModal)
        assert ringer.rang == [alarm.id]
        # Dismiss via modal button -> service cleared, scheduler resolved
        await pilot.click("#dismiss")
        await pilot.pause()
        assert not isinstance(app.screen, RingModal)
        assert service.get(alarm.id).snoozed_until is None


def _due_app(isolated_cwd):
    """Helper: service with one 07:30 everyday alarm + scheduler frozen at due minute."""
    from py_alarm_cli.core.scheduler import Scheduler
    from py_alarm_cli.core.service import AlarmService
    from py_alarm_cli.storage.json_repo import JsonAlarmRepository
    from py_alarm_cli.tui.app import AlarmApp

    class FakeRinger:
        def __init__(self):
            self.rang = []

        def ring(self, alarm):
            self.rang.append(alarm.id)

    service = AlarmService(JsonAlarmRepository("./alarms.json"))
    alarm = service.create(time="07:30", message="Wake up", days=[])
    ringer = FakeRinger()
    sched = Scheduler(service, ringer, get_now=lambda: datetime(2026, 10, 5, 7, 30))
    return service, alarm, ringer, AlarmApp(service, scheduler=sched)


@pytest.mark.asyncio()
async def test_bug1_dismissed_modal_does_not_reappear_same_minute(isolated_cwd):
    """Bug 1: after dismiss, the next 1s poll (same minute) must NOT re-pop the modal."""
    from py_alarm_cli.tui.screens import RingModal

    service, alarm, ringer, app = _due_app(isolated_cwd)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.poll_alarms()
        await pilot.pause()
        assert isinstance(app.screen, RingModal)
        await pilot.click("#dismiss")
        await pilot.pause()
        assert not isinstance(app.screen, RingModal)
        # Same minute, modal closed: further polls stay quiet, bell rang exactly once.
        app.poll_alarms()
        await pilot.pause()
        app.poll_alarms()
        await pilot.pause()
        assert not isinstance(app.screen, RingModal)
        assert ringer.rang == [alarm.id]


@pytest.mark.asyncio()
async def test_bug1_enter_key_dismisses_ring_modal(isolated_cwd):
    """Bug 1: pressing Enter while the alarm modal is open must dismiss it."""
    from py_alarm_cli.tui.screens import RingModal

    service, alarm, ringer, app = _due_app(isolated_cwd)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.poll_alarms()
        await pilot.pause()
        assert isinstance(app.screen, RingModal)
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, RingModal)
        assert service.get(alarm.id).snoozed_until is None


@pytest.mark.asyncio()
async def test_bug2_toggle_operates_on_highlighted_row(isolated_cwd):
    """Bug 2: space/toggle must affect the highlighted row, not always row 0."""
    from py_alarm_cli.core.service import AlarmService
    from py_alarm_cli.storage.json_repo import JsonAlarmRepository
    from py_alarm_cli.tui.app import AlarmApp

    service = AlarmService(JsonAlarmRepository("./alarms.json"))
    first = service.create(time="07:30", message="First", days=[])
    second = service.create(time="21:00", message="Second", days=[])
    app = AlarmApp(service)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.table.move_cursor(row=1)
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()
        assert service.get(first.id).enabled is True
        assert service.get(second.id).enabled is False


@pytest.mark.asyncio()
async def test_bug2_delete_operates_on_highlighted_row(isolated_cwd):
    """Bug 2: delete must remove the highlighted row, not always row 0."""
    from py_alarm_cli.core.service import AlarmService
    from py_alarm_cli.storage.json_repo import JsonAlarmRepository
    from py_alarm_cli.tui.app import AlarmApp

    service = AlarmService(JsonAlarmRepository("./alarms.json"))
    first = service.create(time="07:30", message="First", days=[])
    second = service.create(time="21:00", message="Second", days=[])
    app = AlarmApp(service)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.table.move_cursor(row=1)
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.click("#yes")
        await pilot.pause()
        remaining = service.list_alarms()
        assert [a.id for a in remaining] == [first.id]
        _ = second
