# Refugee waves mod (issue #51, 2026-10-13)

Game 0.8.111, fixture `base` (Riesenbuckel, 10 families, 2 free home slots). Mod: `mod/RefugeeWaves/Scripts/main.lua`. Scenario: `refugee-wave`.
Runs: `rw1`, `rw2`, `rw3`, all `pass` (3 of 3). No crash, no save function, no eval, no `family_add`.

## What the mod does (design accepted by the user on #51)
| Design point | Implementation |
|---|---|
| Trigger | Each new game month, `chance_percent` (15). Only with at least `min_families` (10) and no active wave. The month comes from `TemporalComponent.Year * 12 + month`. A check runs every 2 s of real time on the game thread. |
| Wave size | 1 to `max_calls` (3) calls of `settleRegion` through `HarnessLords.settle_region`. The village size limits it: one call for each `families_per_extra_call` (10) families. |
| Camp | `forest_spot` first (the woods), then `tent_find_spot`, then the settled centre. |
| Message | `PawnCPP:playEventMessage` (HarnessUi banner) and a log line. See the gap below. |
| Pressure | None added. The game lowers approval for homeless families. |
| End | The homeless count falls back to the count from before the wave (outcome `housed`). |
| Bad outcome | Wave families homeless for `homeless_days_limit` (30) game days, or approval under `approval_floor` (40). Then `ceil(homeless wave families * rebel_share_percent / 100)` families (at most 6) leave and a raid starts: `HarnessBandits.rebel_raid_rally`. Outcome `rebelled`. If the call fails, the mod logs an error and records `rebellion_failed`. |
| Save and load | The mod keeps no state that the game cannot rebuild. A new Lua state adopts the homeless families that it finds at its first check as the active wave (start day = that day). The setting `adopt_on_start` turns this off. Not testable in the real game (save functions are banned). |

All settings are at the top of the file (`CONFIG`). The command `RefugeeWaves.configure` changes them at run time.
Commands: `configure`, `start_wave` (calls 1 to 5), `check`, `status`, `forget_wave`. Metrics: `wave_active`, `waves_started`, `waves_ended`, `rebellions`, `last_outcome`, `wave_homeless`.
Wave size depends on free home slots: `settleRegion` adds 5 families; free homes take the first ones, the rest is homeless. On `base` one call gives 5 families and 3 homeless. The mod does not eject families to make more homeless (`family_eject` is available for a later change).

## Real runs (scenario `refugee-wave`, three runs, same result)
Phase 1: wave, then plots.
- `start_wave calls=1`: families 10 -> 15 (+5), homeless 0 -> 3, camp at the woods, in all 3 runs.
- Approval 71 fell by 10 within 4 game days (assert: at least 3).
- 5 burgage plots placed without the mouse. The wave ended `housed`, homeless 0, approval 68 or more (assert: at least low + 2). No rebellion.
Phase 2: second wave, timer set to 3 game days.
- Families 15 -> 20, homeless 5. After 3 game days the mod logged "refugees stayed homeless for 3 game days" and started the raid: 2, 3 and 2 families left (the homeless count had fallen to 3 or 4 by then, because the game moves tent families into free homes). Bandit units: 36 (2 squads of the raid).
- Each run took about 300 s of wall time.

## Gaps
- The banner: `playEventMessage` returned, but the widget was not found right after the call ("no widget appeared"). It may appear later, or the game may drop it while paused. Not checked on screen. The log line always exists. A real letter (`Letter` in `InBox`) was not tried.
- The monthly random trigger was proven in the fake game only. The real runs start the wave with the command, because a real month takes too long for a scenario. The month read (`TemporalComponent.month`, `Year`) was not checked in the real game.
- The acceptance of the rebellion is the raid (`rebel_raid_rally`), which burns buildings. The families removed by `sack_people` are killed, not turned into bandits one by one. The settle letter as a way to negotiate them back works only while the raiders stand at the waypoint (`homeless-rebellion.md`); the mod does not send it.
- Save and load were not tested in the real game.
- The mod's check handler `start_wave` takes about 0.1 s (the forest spot search). The registry logs a warning. It is not harmful.
