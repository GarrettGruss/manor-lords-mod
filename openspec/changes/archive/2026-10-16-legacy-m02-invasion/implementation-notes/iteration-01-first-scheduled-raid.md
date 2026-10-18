# Iteration 01: first-scheduled-raid (notes)

## Design
- Feature `mod/InvasionMod/Scripts/features/invasion/` (`init.lua`, pure rules in `plan.lua`). It needs `mod_state`.
- ModState keys (mod "invasion", pawn Tags): `difficulty`, `plan_day`, `raid_day`, `warning_day`, `size_class`, `squads`, `raids_spawned`, `last_banner_day`. Days are `daysTotal`.
- A check runs every 300 ms real time. Each check lifts the base game timer (`daysUntilNextRaid`) to 700 when it is under 300. The daily step runs once for each new game day.
- Daily step: no plan yet -> make the plan. Days left <= 0 -> `spawnRaiders(squads, player pawn position)`. From the warning day: banner "Raid in N days, about S raiders" (log line `INVASION banner`).
- Plan: raid day = plan day + 30..90. Warning = 14..56 days (cut to the wait). Size class random 1..3. Squads = multiplier x difficulty.
- Only one raid is planned in this iteration. After the spawn the mod plans nothing more (later iterations).
- Named commands: `InvasionMod.invasion_state`, `invasion_force_next`, `invasion_set_difficulty` (1..3), `invasion_set_size` (small, medium, large). A size or difficulty change recomputes the squads of the open plan.
- The M01 command `mod_state_dump` now reports only its own selftest keys. The M01 scenario `mod-state-default-load` checks only selftest entries, because the invasion feature writes its own entries and the version entry.

## Limits
- The plan is made on the first check after load. The plan day banner can show the random size before a scenario forces the size. In real play nothing forces it.
- The player position is the spawn centre. The raiders appear where `spawnRaiders` puts them (spike S2).
- Writes above 730 to the base timer were not needed: the mod lifts it to 700 whenever it is under 300.
- A pop-up pauses the game. `ctx.time` runs close pop-ups every 2 s now (harness fix). `invasion-no-double-raid` also closes them before each chunk.
- Raiders fight after the spawn, so a late census shows fewer than 18 units per squad. A4 checks `0 < added <= planned`; the exact count is checked in `first-raid` right after the spawn.
