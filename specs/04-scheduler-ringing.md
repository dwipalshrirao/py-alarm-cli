# 04 — Scheduler & Ringing — py-alarm-cli

## 1. Clock & tick
- `Scheduler(service, ringer, get_now=..., interval=1.0s)` is owned by `AlarmApp` (injected, default built with `TerminalBellRinger`) and polled via `set_interval(1.0, app.poll_alarms)` — no threads. `poll_alarms()` calls `tick()` and pops one `RingModal` per due alarm (`_ring_open` guard prevents stacking).
- Each tick (DEBUG log throttled to every 60s to avoid spam): `due = service.due_alarms(now)`.
- Dedup: alarm already in `ringing` set is not re-fired until dismissed/snoozed.

## 2. Due logic — `AlarmService.due_alarms(now)`
- Candidate if `enabled` and not currently ringing.
- If `snoozed_until` set and `snoozed_until <= now` → due (and clear after ring → reschedule).
- Else if `now.strftime("%H:%M") == alarm.time` and (`days == []` or today-name in days) → due.
- Minute granularity is enough for a simple clock; 1s tick guarantees we hit the minute.

## 3. Ring flow
1. `ringer.ring(alarm)`: ALWAYS `print("\a", end="", flush=True)`; then best-effort OS hook, each wrapped in try/except + log WARNING on failure (never raise):
   - Windows: `winsound.MessageBeep()` (guarded import).
   - macOS: `afplay /System/Library/Sounds/Glass.aiff` via non-blocking `subprocess.Popen` (short timeout).
   - Linux: `print("\a")` only in v1 (no external player dependency).
2. TUI opens `RingModal` with `alarm.message` + time.
3. User `Dismiss (Enter)` → `service.dismiss(id)` (clears snooze, logs `alarm_dismissed`); one-shot alarms stay enabled (simple clock: all alarms repeat daily/days-pattern).
4. User `Snooze (s)` → `service.snooze(id, minutes=5)` sets `snoozed_until = now + 5m`, logs `alarm_snoozed`, row shows `Snoozed (in 5m)`.

## 4. Interface (for OCP + tests)
```python
class BellRinger(Protocol):
    def ring(self, alarm: Alarm) -> None: ...
```
`TerminalBellRinger` is the v1 impl. Tests inject a mock ringer + fake `get_now`.

## 5. Test anchors (→ 06)
- Fake-clock matrix: rings at exact minute, not a minute before/after; day filter respected; disabled never rings; snooze re-rings after 5m.
- Ringer: `\a` emitted even when OS hook fails.
- Scheduler: no double-fire within same minute.
