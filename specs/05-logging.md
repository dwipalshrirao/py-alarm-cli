# 05 — Logging — py-alarm-cli

Goal: debug the app from a single file in the current directory, no CLI flags.

## 1. Setup — `py_alarm_cli/logger.py`
```python
def setup_logging(level: str = os.getenv("PY_ALARM_LOG_LEVEL", "INFO")) -> logging.Logger
```
- Stdlib only. Called once in `app.py`. Returns `py-alarm-cli` logger.
- Level from `PY_ALARM_LOG_LEVEL` env (`DEBUG/INFO/WARNING/ERROR`, default INFO). Invalid → INFO + warning. No CLI flags by design (TUI-only).

## 2. Sinks (current directory only)
- Console: `StreamHandler(stderr)` at chosen level — so Textual screen isn't polluted (Textual captures stdout; stderr stays readable).
- File: `RotatingFileHandler("./py-alarm-cli.log", maxBytes=512_000, backupCount=3, encoding="utf-8")` at DEBUG always (file keeps detail even when console is INFO).
- Format: `%(asctime)s %(levelname)-5s %(name)s %(message)s [%(alarm_id)s]` — `alarm_id` via `LoggerAdapter`, default `-`.

## 3. What to log
| Event | Level | Example |
| ----- | ----- | ------- |
| app start, repo path, alarm count | INFO | `started alarms=2 file=./alarms.json` |
| create/update/delete/toggle/snooze/dismiss | INFO + `extra={"alarm_id": id}` | `alarm_created time=07:30` |
| load empty / corrupt backup | INFO / ERROR | `corrupt json backed up to ./alarms.json.corrupt-...bak` |
| save ok / fail | DEBUG / ERROR | `saved n=2` |
| scheduler tick | DEBUG throttled (every 60s) | `tick due=0` |
| due + ring + OS-hook failure | INFO / WARNING | `ringing id=..` / `bell hook failed: ...` |

Never log tracebacks to TUI toasts — log full exception, toast shows one line.

## 4. Rules
- `logging.getLogger("py-alarm-cli")` everywhere; no `print()` debugging, no per-module config.
- No secrets: only user-typed alarm messages; no full JSON dumps.
- Log file lives next to `alarms.json` in cwd — easy to find, easy to delete, easy to attach to bug reports.

## 5. Test anchors (→ 06)
- `setup_logging` creates `./py-alarm-cli.log` (tmp cwd via `monkeypatch.chdir`), respects env level, invalid → INFO.
- Service ops emit records with `alarm_id`; corrupt load emits ERROR.
