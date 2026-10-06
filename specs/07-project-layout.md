# 07 — Project Layout & Packaging — py-alarm-cli

## 1. Runtime
- Python `>=3.9` (Textual floor). Deps: `textual>=3`. Dev extras: `pytest pytest-asyncio coverage`.
- Entry: `py-alarm` → `py_alarm_cli.app:main()` → opens TUI. No other commands/flags.

## 2. Tree
```
py-alarm-cli/
  README.md
  pyproject.toml
  specs/00-overview.md … 07-project-layout.md
  src/py_alarm_cli/
    __init__.py
    __main__.py        # python -m py_alarm_cli
    app.py             # main(): setup_logging + wire repo/service + AlarmApp.run()
    logger.py
    core/models.py
    core/service.py
    core/scheduler.py
    core/ringer.py
    storage/json_repo.py
    tui/app.py
    tui/screens.py
    tui/widgets.py
  tests/ (see 06)
  .gitignore (alarms.json, *.bak, py-alarm-cli.log*, __pycache__)
```

## 3. `pyproject.toml` (essentials)
- `[project] name="py-alarm-cli"`, `requires-python=">=3.9"`, `dependencies=["textual>=3"]`, `[project.scripts] py-alarm="py_alarm_cli.app:main"`, `[project.optional-dependencies] dev=["pytest","pytest-asyncio","coverage"]`.
- `[tool.pytest.ini_options] asyncio_mode="auto"`.
- src-layout (`[tool.setuptools.packages.find] where=["src"]`).

## 4. Runtime files (cwd only)
- `./alarms.json`, `./py-alarm-cli.log` (+ rotations), `./alarms.json.corrupt-*.bak` — all gitignored, all created lazily on first run.

## 5. Build order (TDD)
1. packaging + logger + models → 2. json_repo → 3. service → 4. scheduler/ringer → 5. tui → 6. app wiring. Run `pytest` after each; keep Textual out of `core/`/`storage/`.
