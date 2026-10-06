# 03 — TUI UX (Textual, TUI-only) — py-alarm-cli

Single entrypoint `py-alarm` opens this UI. No CLI CRUD flags — everything below is in-TUI.

## 1. Layout — `AlarmApp`
```
┌ py-alarm-cli ──────────────────────┐
│ 14:05:09                           │  ← live current time (HH:MM:SS, ticks every second)
│ Time  │ Days      │ Message │ Next │ Status  │
│ 07:30 │ Mon-Fri   │ Wake up │ 2h15m│ Enabled │
│ 21:00 │ Everyday  │ Tea     │ 8h   │ Disabled│
├────────────────────────────────────┤
│ [a]dd [e]dit [d]elete [space] on/off [s]nooze [q]uit │
└────────────────────────────────────┘
```
- Table: Textual `DataTable` (columns above). `Next` = next-ring countdown (`in 2h 15m` / `Tomorrow 07:30`), `Status` = Enabled / Disabled / Ringing / Snoozed.
- Modals (`AddEditModal`, `ConfirmDelete`, `RingModal` in `tui/screens.py` via `ThemedModal` base): centered `.dialog` (width 60, `$surface` bg, centered title/message, centered button row) with heavy theme-color border — `$primary` add/edit, `$warning` delete, `$error` ring. `SCOPED_CSS = False` so screen-level rules match.
- Footer: key hints. Toast for errors/confirmations (e.g. "Saved 07:30").

## 2. Interactions
- `a` → `AddModal`: Time input (HH:MM, placeholder `07:30`), Message input, Days multi-select (checkboxes Mon..Sun, all-off = Everyday), `[Save] [Cancel]`. Validation errors shown inline; Save disabled until valid.
- `e` / `Enter` → `EditModal`: same fields prefilled, id shown read-only.
- `d` → `ConfirmDelete("Delete 'Wake up' 07:30? [y/N]")`.
- `space` → toggle enabled.
- On ring → `RingModal` (blocking, top): big message + time, `[Dismiss (Enter)] [Snooze 5m (s)]`, bell keeps pulsing until action.
- `q` → quit (state already saved on every mutation, so quit is safe).

## 3. Rules
- Widgets are dumb: format via pure functions (`format_next()`, `format_days()`), all mutations via `AlarmService`. No JSON/file code in `tui/`.
- Live countdown refresh every 5s; scheduler tick every 1s (separate worker, see 04).
- Empty state: "No alarms — press `a` to add one."
- Errors (e.g. storage failure): toast + log, never traceback on screen.

## 4. Test anchors (→ 06)
- Textual `Pilot`: add-valid, add-invalid-blocked, edit, delete-confirm/cancel, toggle.
- Ring modal appears on fake due alarm; dismiss/snooze update service.
- Pure format functions unit-tested (countdown text, day ranges).
