# 01 — Architecture — py-alarm-cli

## 1. Layering (dependency flows inward)
```
app (entrypoint, opens TUI)
 └─> tui (Textual screens / widgets)
      └─> core (models, AlarmService, scheduler, ringer interface)
           └─> storage (JSON repository)
```

Rules:
- `tui` NEVER reads/writes `alarms.json` or `*.log` directly — only via `core.AlarmService`.
- `storage` NEVER imports `textual`, `core` NEVER imports `textual`.
- `app` only wires logger + repository + service + TUI app and runs it.
- OS differences isolated behind small interfaces in `core/` (ringer) — no `if sys.platform` scattered in TUI.

## 2. Modules (single responsibility)

| Module | Responsibility | Depends on |
| ------ | -------------- | ---------- |
| `py_alarm_cli/__main__.py` + `app.py` | configure logging, build repo/service, `AlarmApp().run()` | logger, storage, core, tui |
| `py_alarm_cli/logger.py` | `setup_logging()` — stderr + `./py-alarm-cli.log` | stdlib only |
| `py_alarm_cli/core/models.py` | `Alarm` dataclass, validation, `next_ring()` computation | stdlib `datetime`, `zoneinfo` (local tz) |
| `py_alarm_cli/core/service.py` | `AlarmService`: CRUD + enable/disable/snooze/dismiss orchestration | models, storage protocol, logger |
| `py_alarm_cli/core/scheduler.py` | background `asyncio` tick: find due alarms, call ringer | service, clock abstraction, logger |
| `py_alarm_cli/core/ringer.py` | `BellRinger` protocol + `TerminalBellRinger` (`\a` + OS hook) | logger |
| `py_alarm_cli/storage/json_repo.py` | `JsonAlarmRepository`: load/save `./alarms.json`, atomic write, corrupt-file backup | models, logger |
| `py_alarm_cli/tui/app.py` | `AlarmApp(App)`: mounts list + footer, runs scheduler worker | core service, logger |
| `py_alarm_cli/tui/widgets.py` | table rows, countdown/status formatting (pure functions where possible) | core models |
| `py_alarm_cli/tui/screens.py` | `AddEditModal`, `RingModal`, `ConfirmDelete` | service |

## 3. SOLID mapping
- **S:** each module above has one reason to change.
- **O:** new ringer (e.g. sound file) = new `BellRinger` impl, no service change.
- **L/D:** service depends on `AlarmRepository` and `BellRinger` protocols, concrete classes injected in `app.py` — enables fake repo / mock ringer / fake clock in tests.
- **I:** protocols are tiny: `load() / save()`, `ring(alarm)`.

## 4. Data flow
1. Launch: `app.py` → `setup_logging()` → `JsonAlarmRepository("./alarms.json").load()` → `AlarmService` → `AlarmApp(service).run()`.
2. CRUD from TUI: widget event → screen → `service.create/update/delete/toggle()` → repo atomic save → log + refresh table.
3. Ring: `scheduler` tick (every 1s) → `service.due_alarms(now)` → `ringer.ring(alarm)` → TUI `RingModal` with message → dismiss/snooze → service update → save + log.

## 5. Portability
- Pure Python + `textual` + `rich` (Textual dep). No `curses`, no binary wheels.
- Bell: always emit `\a` (works everywhere); OS hook is best-effort and never raises (see 04).
- Paths: everything in current working directory (`./alarms.json`, `./py-alarm-cli.log`) — no home-dir / XDG logic in v1 (keeps it a simple alarm clock).
- Timezone: local system time via `datetime.now().astimezone()`; no tz config in v1.
