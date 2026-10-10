# RaidStandIn: a toy model of the raid logic of the Invasion Mode mod

Status: built and unit tested in the fake game kit (2026-10-10). **NOT run in the real game yet.** The parent marks `method_verified` after real runs.
Follow-up of U10 (`mod-state-contract.md`). Files: `mod/RaidStandIn/Scripts/main.lua`, `harness/raidstandin/client.py`, `harness/scenarios/raid_*.py`,
`harness/suites/raid-size-ab.json`, tests `harness/tests/test_fakegame_raidstandin.py` and `test_fakegame_raid_scenarios.py`.

## Why

The first stand-in (`InvasionStandIn`) proved that the harness can observe and drive state that a mod defines: outposts, captives, tribute.
The brief has more mod-defined logic: the raid director, raid behavior, tiers, the warlord, the sack rule and the pressure systems.
This stand-in models them as a small toy, so the scenarios for T1, T3, T5, R1, R4, R6, D1, D2, D3, S2, S3, P1, P2, P4 and P6 exist before the real mod.
The toy proves the TEST METHOD. The real mod will later pass the same scenarios. The numbers in the toy are not the balance of the real mod.

## Design

- Same contract as `InvasionStandIn`: the mod registers commands and metrics in `HarnessCommands` (`RaidStandIn.<name>`). The mod serves them in its own Lua state through `<run>/modcmd/RaidStandIn/`. The Python side is `ctx.mod`.
- No loop, no hook, no game object. The state is plain Lua tables.
- The toy day follows the game days. Each command and each metric read first reads `TemporalComponent.daysTotal` and runs the toy rules for every game day that passed (`syncTime`). A scenario can also move the toy day by hand: `set_day` (no rules run) and `advance_days` (runs the rules for each day, at most 4000). This lets a scenario simulate three years in one command.
- Randomness: a small seeded generator (a linear congruential generator, upper bits). `configure seed=N` makes a run repeatable. A different seed gives another run. The scenarios take a base seed from the run folder name (`seed_base_for`), write it to `scenario.log`, and so repeated suite runs differ but a failed run can be repeated.
- Every command has a schema (types, ranges, allowed values). `HarnessCommands` refuses wrong arguments before the handler runs.
- `RAID_STANDIN_SIZE_PERCENT` (10 to 1000, default 100) is read when the mod loads. It scales raid sizes. A suite variant sets it with `env`, so the A/B runner has a real difference to find. A bad value stops the mod with an error.
- Deploy: `deploy.ps1` enables every folder in `mod/`. The mod does nothing until a scenario sends it a command. Deploy it only for the raid scenarios.

## Toy rules

| Area | Rule |
|---|---|
| Calendar | 360 days a year, 90 days a season: spring 0-89, summer 90-179, autumn 180-269, winter 270-359. |
| Factions | `cuman`: summer only, dominant unit `horse_archers`, objective `loot`. `norse`: spring and autumn, dominant unit `shock_infantry`, objective `burn`. |
| Director | A raid is planned (`set_timer`, or automatically with `auto`), announced `announce_days` before arrival, then it arrives. A timer shorter than the lead time is announced at once. One raid is scheduled at a time. Automatic raids arrive only in an allowed season (the day moves forward to the next allowed day). |
| Composition | The first unit type is dominant (60% when there is more than one type). The tier sets the number of unit types (variety). The announced `kind` is the dominant unit type. |
| Tiers | 1 to 4: base size 12, 20, 32, 48. Gap between raids 120, 60, 30, 15 days (plus or minus 15). Variety 1 to 4. Targeting: tier 1 random, tiers 2 to 4 the nearest stockpile with at least 100 stock (the bait rule). Breaking point 50, 40, 30, none. Tier 4 retreats only when the leader dies. |
| Size | tier size * `size_percent` * jitter (90 to 110%) * warlord bonus (+25% a level) * pact (cuman pact: 50%). |
| Active raid | Each day: loot 1 per unit from the target stockpile (capacity 4 per unit), morale -5 and -1 more for each 10 defense, the timer -1 (6 days), a chance that the leader dies (`leader_death_percent`, default 10). In winter the raid is paused. |
| Retreat | `leader_dead`, `morale_break` (morale at or under the breaking point), `full_loot`, `timer_end`. At tier 4 only `leader_dead`. |
| Warlord | A raid that retreats with a living leader raises the warlord level (max 5). A dead leader resets it and gives the town +10 hope. |
| Sack | `sack` records the day. Food falls to 70%, morale -30. When the sacks inside `sack_window_days` (360) reach `sack_limit` (2), `game_over` is true. The day counter and the director keep running after a sack. |
| Settlement | Start: food 1000, silver 500, workers farming 40, crafting 20, military 0, morale 70. Food income = farming / 2 (0 in winter). Food use = 10, +5 in winter, +3 with conscription. |
| Morale meter | -2 a day while a raid is announced or active, +1 a day otherwise, clamped to 0..100. |
| Laws | `conscription` (100 silver, +20 defense, 3 food a day), `tithe` (free, +5 silver a day, -10 morale once), `cuman_pact` (200 silver, cuman raids are half the size). No refund on repeal. |
| War economy | On: 10 farmers become military (defense +10, food income -5). Off: back. |
| Stockpiles | Start: id 1 (distance 10, stock 50), 2 (20, 300), 3 (35, 400), 4 (5, 20). Stock grows back 3 a day up to its start value. High value means at least 100 stock. |

## Commands and metrics

Commands (22): `configure`, `reset`, `clock`, `set_day`, `advance_days`, `set_timer`, `cancel_raid`, `next_raid`, `current_raid`, `raid_log`,
`kill_leader`, `kill_raiders`, `damage_morale`, `fill_loot`, `expire_timer` (the last five force a retreat condition and fail with "no raid is active" without a raid),
`set_stockpile`, `stockpiles`, `sack`, `settlement`, `enact`, `repeal`, `set_war_economy`.
Metrics (15): `day`, `season`, `raids_arrived`, `raid_announced`, `raid_active`, `spawned_units`, `bait_hits`, `warlord_level`, `town_morale`, `defense`, `silver`, `food`, `workers_farming`, `sacks_in_window`, `game_over`.
A raid view has: `id`, `state` (`scheduled`, `announced`, `active`, `ended`), `faction`, `kind`, `objective`, `breaking_point`, `leader_only`, `tier`, `size`, `units_left`, `composition`,
`announce_day`, `announced_day`, `planned_day`, `arrival_day`, `end_day`, `target`, `bait_hit`, `loot`, `capacity`, `morale`, `timer_left`, `leader_alive`, `retreat_reason`, `warlord_level`, `paused_days`, `arrival_season`.
`bait_hit` means: the target is the choice of the bait rule (the nearest high value stockpile, or the nearest one when none has high value).

## Scenarios and criteria

| Scenario | COVERS | What it does | Wall time (estimate) |
|---|---|---|---|
| `raid-timeline` | T1, T3 | Sets the timer, steps the toy clock to the announcement (exactly N days before) and the arrival, compares the announced kind with the units for both factions. Then waits 4 real game days at speed 3 (two legs) to prove that the toy clock follows the game clock. | about 40 s |
| `raid-seasons` | T5, P6 | Compares the season of 10 border days with an independent Python copy of the calendar. Simulates 3 years of automatic raids and checks each raid day against the rules (no winter raid, both factions, every year). Winter pauses an active raid. Winter stops the harvest and raises food use. | about 15 s |
| `raid-behavior` | R1, R4, R6 | Reads the per-raid log of a 2-year run (one objective, one numeric breaking point, known reason). Forces each retreat trigger in a fresh raid and checks the state change. Places a bait stockpile and checks the target, then spends the bait. | about 40 s |
| `raid-tiers` | D1, D2, D3 | 4 tiers x 6 seeded 2-year runs. Uses `suitelib/stats.py` to compare size and frequency (tier 1 against tier 3 and 4), checks variety and targeting, reports `tier<N>_mean_size` and `tier<N>_mean_raids` with `ctx.metric`. Checks that an escaped warlord returns stronger (same seed, ratio at least 1.4) and a dead one resets. Checks that tier 4 retreats only on leader death. | about 40 s |
| `raid-sack` | S2, S3 | One sack: no game over, the clock and the director go on. Two sacks inside the window: game over. Two sacks a window apart: no game over. | about 15 s |
| `raid-politics` | P1, P2, P4 | Conscription, tithe and the cuman pact: costs and benefits, a refusal when silver is short. The morale meter against the clock (a series of metric reads while calm, while a raid is announced and after it) and `metrics_window`. The war economy toggle. | about 20 s |

The wall time is a guess from the number of command round trips (about 0.1 to 0.3 s each). Every scenario has `LIMIT_S = 120`.

## The A/B scenario

`raid-tiers` reports per-tier numbers with `ctx.metric`. The suite `harness/suites/raid-size-ab.json` runs it 4 times each with `RAID_STANDIN_SIZE_PERCENT` 100 and 150.
The report should show `tierN_mean_size` as different (about +50%) and `tierN_mean_raids` as the same. The fake game test `test_the_size_setting_of_the_ab_suite_changes_the_reported_metrics` checks the ratio.
The in-run comparison inside `raid-tiers` is a second use of the statistics: it compares tiers inside one run.

## What is toy and what is not proven

- The rules and numbers are inventions of this fixture. They are not the balance of the real mod and not rules of the base game.
- The toy shows that the observation and drive METHOD works: read per-raid state, force conditions, set the clock, replay seeded runs, compare tiers with statistics, read a meter against the clock.
- NOT verified in the real game: all six scenarios. Only the fake game kit ran them (separate Lua states per mod, real `HarnessCommands`, real `ModState`).
- Not covered (need the real game): R3, R7, R8, S1, C1, C2, C3, P3, P5, T4, Q1, Q4. Also not covered: the announcement through the game UI, units in the real world, and the real raid timer of the base game (`raid-timer` covers the base timer).
- In the real mod the retreat conditions, the target and the composition will come from game objects. The scenarios then need the real mod to expose the same commands or an adapter with the same names. That is a later spec.
- `set_day` jumps the toy day without running the rules for the skipped days. A scheduled raid whose day lies before the new day arrives on the next day. Use `advance_days` to run the rules.

## Test findings during the build

- The first random generator used the low bits of the linear congruential generator. One of 100 run names gave only one faction in 3 years. The generator now uses the upper bits (shift by 16).
- Frequency by tier was hidden by the season windows when the gaps were 150, 100, 70 and 45 days. The gaps are now 120, 60, 30 and 15 days.
- A raid size that grows with the tier is not enough to show the effect of a setting: the warlord bonus adds noise. The scenario compares medians and uses the statistics, and the warlord check uses one fixed seed.
- The nearest-high-value rule can find no high-value stockpile when a big raid has emptied them. `bait_hit` then follows the fallback of the rule (the nearest stockpile).
