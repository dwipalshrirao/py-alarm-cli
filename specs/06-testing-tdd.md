# 06 — Testing & TDD — py-alarm-cli

## 1. Workflow (Red → Green → Refactor, per spec item)
1. Write failing test for next smallest behavior (e.g. `test_rejects_bad_time`).
2. Implement minimum code to pass.
3. Refactor (keep tests green), update spec if behavior clarified.
- Order: models → repository → service → scheduler/ringer → logger → tui.
- No production code without a failing test first; no speculative tests for un-specced features.

## 2. Stack & commands
- `pytest`, `pytest-asyncio` (asyncio_mode=auto), `coverage` (`pytest --cov=py_alarm_cli --cov-report=term --cov-fail-under=80`).
- Gates: full suite green + `core/` + `storage/` coverage ≥ 80%. TUI covered by Pilot flows, not line-counted strictly.
```bash
pip install -e ".[dev]"
pytest -q
pytest --cov=py_alarm_cli --cov-report=term --cov-fail-under=80
```

## 3. Layout
```
tests/
  conftest.py          # tmp cwd (isolated alarms.json + log), sample alarms, fake clock
  test_models.py       # validation table, next_ring cases
  test_json_repo.py    # round-trip, missing→[], corrupt→.bak+[]+ERROR log
  test_service.py      # CRUD, toggle, due_alarms matrix, snooze/dismiss
  test_scheduler.py    # tick fires once per minute, disabled/day-filter, fake ringer
  test_ringer.py       # \a emitted, OS-hook failure swallowed + WARNING
  test_logger.py       # file created in cwd, env level, invalid→INFO
  test_tui.py          # Pilot: add/edit/delete/toggle, invalid blocked, ring modal
```

## 4. Conventions
- Fake time: inject `get_now=lambda: fixed_dt`; never `sleep()` real time.
- Isolated fs: `monkeypatch.chdir(tmp_path)` so `./alarms.json` + `./py-alarm-cli.log` never touch the real cwd.
- Mocks: mock `BellRinger`, real `AlarmService` + real repo on tmp files (thin-mock rule: mock only at seams).
- TUI: `async with app.run_test() as pilot:` + `await pilot.press("a")` etc.; assert on service state, not widget internals.
