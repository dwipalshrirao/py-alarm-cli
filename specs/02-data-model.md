# 02 — Data Model & JSON Storage — py-alarm-cli

## 1. Alarm entity
```python
@dataclass(frozen=True)
class Alarm:
    id: str            # uuid4 hex, immutable, unique
    time: str          # "HH:MM" 24h, e.g. "07:30"
    message: str       # 1..200 chars, shown on ring
    enabled: bool = True
    days: list[str] = field(default_factory=list)
        # [] = every day; else subset of ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    snoozed_until: str | None = None  # ISO datetime local, set by snooze
```

No seconds, no timezone field, no cron expressions — simple alarm clock.

## 2. Validation (single path: `Alarm.validate()` + service re-check)
- `time` must match `^([01]\d|2[0-3]):[0-5]\d$`, else `ValueError("time must be HH:MM 24h")`.
- `message` stripped; empty → error; >200 chars → error.
- `days` values must be in the 7-name set, no duplicates (normalized to Mon-first order).
- `snoozed_until` must be future ISO datetime if set.
- `id` immutable on update; `enabled` toggled via dedicated method.

## 3. JSON format — `./alarms.json` (current directory only)
```json
{
  "alarms": [
    {"id": "a1b2c3", "time": "07:30", "message": "Wake up", "enabled": true, "days": ["Mon","Tue","Wed","Thu","Fri"], "snoozed_until": null},
    {"id": "d4e5f6", "time": "21:00", "message": "Tea", "enabled": false, "days": [], "snoozed_until": null}
  ]
}
```

## 4. Repository contract — `JsonAlarmRepository(path="./alarms.json")`
- `load() -> list[Alarm]`: missing file → `[]` + log INFO; corrupt JSON / schema error → rename to `./alarms.json.corrupt-<timestamp>.bak`, return `[]`, log ERROR with path + reason (never crash TUI).
- `save(alarms) -> None`: atomic write (temp file + `os.replace`), `json.dump(indent=2)`.
- All file errors wrapped as `StorageError`; service maps to user-facing TUI toast + log.
- CRUD lives in `AlarmService`, repo only does load/save — keeps SRP.

## 5. Service CRUD contract
- `create(time, message, days) -> Alarm` (generates id, validates, saves, logs `alarm_created extra={alarm_id}`).
- `update(id, ...) -> Alarm`, `delete(id) -> None`, `set_enabled(id, bool) -> Alarm`.
- `snooze(id, minutes=5/10)`, `dismiss(id)` (clears `snoozed_until`).
- `due_alarms(now) -> list[Alarm]`: enabled AND (time matches HH:MM AND day matches OR `snoozed_until <= now`).
- `next_ring(alarm, now) -> datetime`: next occurrence from time+days; if `snoozed_until` future, min(snoozed, computed).

## 6. Test anchors (→ 06)
- Round-trip: save → load equality.
- Corrupt file → backup + empty + ERROR log.
- Validation table: bad times, empty/overlong messages, bad days.
- `next_ring` cases: later today, tomorrow, day-filtered week wrap.
