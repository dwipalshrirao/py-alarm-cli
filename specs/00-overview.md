# 00 — Project Overview — py-alarm-cli

## 1. Purpose
Portable Python CLI alarm clock controlled via a full-screen Terminal User Interface (TUI).

Users can set multiple alarms, perform CRUD operations persisted in JSON, and get notified
with a message + terminal bell on Windows / macOS / Linux.

## 2. Source of Truth
`README.md`:
> Portable Python CLI alarm clock — set multiple alarms, CRUD via JSON, rings with message
> + terminal bell on Windows/macOS/Linux and can be controlled using terminal user interface.

Stack decision: **Textual** for the TUI (pure-Python, cross-platform, no curses).

## 3. Scope — v1

### In scope
- Multiple alarms with time, optional days/recurrence, message, enabled flag.
- Full-screen Textual TUI as the only control:
  - list alarms with next-ring countdown / status (next-ring = when that alarm will fire next, e.g. "in 2h 15m" / "Tomorrow 07:30"; status = Enabled / Disabled / Ringing / Snoozed)
  - add / edit / delete / enable-disable via keyboard + forms
- JSON file persistence (`alarms.json`).
- Ringing: display message + terminal bell (`\a`), abstracted sound backend per OS.
- Single entrypoint `py-alarm` opens the TUI — no extra CLI flags; all control from inside the TUI.
- Cross-platform: Windows, macOS, Linux with a single codebase.
- Debuggability via stdlib logging (console + rotating file).
- Test Driven Development: `pytest` + `pytest-asyncio`, coverage gate.

## 4. Guiding Principles

### Software design principles
- **Separation of Concerns / Layering:** `storage` (JSON) → `core` (models + scheduler service) → `tui` (Textual) → `app` (entrypoint that opens the TUI). UI never touches the file directly.
- **SOLID:** single-responsibility modules; scheduler, repository, and ringer depend on abstractions (e.g. `AlarmRepository`, `BellRinger` protocols) for testability and OS portability.
- **DRY / KISS / YAGNI:** one validation path, one ring path; no speculative features.
- **Portability first:** pure-Python + Textual; OS differences isolated in `platform/` adapters.
- **Fail-safe:** corrupt JSON never crashes the TUI — backup + start empty + log error.

### Test Driven Development
- Red → Green → Refactor for every spec item.
- Order: models → repository → service/scheduler (fake clock) → ringer (mock) → TUI (Textual Pilot).
- Gates: `pytest`, `pytest-asyncio`, `coverage >= 80%` on `core/` + `storage/`.
- Details: see `specs/06-testing-tdd.md`.

### Logging to debug the application
- Stdlib `logging` only, configured once in `py_alarm_cli/logger.py`.
- Sinks: stderr console + rotating file in current directory only (`./py-alarm-cli.log`).
- Level via `PY_ALARM_LOG_LEVEL` env (default INFO), no CLI flags.
- Log CRUD ops, scheduler ticks (DEBUG throttled), due/ring/snooze/dismiss events with `extra={"alarm_id": ...}`.
- Never log full file dumps or PII beyond the alarm message the user typed.
- Details: see `specs/05-logging.md`.

## 5. Success Criteria
- [ ] `pip install -e .` then `py-alarm` opens the Textual TUI on Win/macOS/Linux.
- [ ] User can add, list, edit, delete, enable/disable alarms entirely from the TUI.
- [ ] Alarms survive restart (JSON round-trip).
- [ ] Due alarm shows its message + audible bell.
- [ ] `pytest` green, coverage met, logs explain every state change at DEBUG level.

## 6. Spec Map
| File | Covers |
| ---- | ------ |
| `specs/01-architecture.md` | layers, modules, dependency rules |
| `specs/02-data-model.md` | Alarm schema, JSON format, validation, CRUD contract |
| `specs/03-tui-ux.md` | screens, widgets, keybindings |
| `specs/04-scheduler-ringing.md` | due detection, ring flow, OS sound abstraction |
| `specs/05-logging.md` | logger config, levels, format, flags |
| `specs/06-testing-tdd.md` | TDD workflow, test layout, gates |
| `specs/07-project-layout.md` | packaging, Python version, repo tree |
