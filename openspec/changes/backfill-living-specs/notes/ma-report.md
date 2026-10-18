# Report of agent group MA (Invasion Mod, part A)

Date: 2026-10-18. Files: `specs/mod/{core,mod_state,invasion,raid_widget,raid_behavior,bandits}/spec.md`. All six pass `openspec validate backfill-living-specs --strict` (no error or warning in these files).

## Numbers
| Capability | Requirements | With a real check | Spec scenarios | "Not checked yet" scenarios |
|---|---|---|---|---|
| mod/core | 9 | 7 | 11 | 2 (scheduler error isolation, run without HarnessCommands) |
| mod/mod_state | 9 | 9 | 11 | 0 |
| mod/invasion | 13 | 13 | 20 | 0 |
| mod/raid_widget | 6 | 6 | 9 | 0 |
| mod/raid_behavior | 10 | 10 | 15 | 0 |
| mod/bandits | 8 | 8 | 17 | 1 (conversion banner) |

"Real check" means at least one spec scenario of the requirement names a test scenario or a Python test. Many checks are fake game tests only (for example carry cap, quiet-spot removal, the `won` phase, the plan in the Tags). Real game checks exist for the main paths.

## Planned iterations that are not built (not written as requirements)
- M01: `iterations/` has only 01. Planned "02 region-state-and-limits" (region Tags, size limit test) is in the README table only.
- M03: README lists `02b loot-back-to-store`, `03 carry-caps` (by raid type), `04 storage-tiers` as not started. Note: loot return to the nearest store IS built (iteration 01), and a single `carry_cap` exists. Only per-raid-type caps, store tiers and the ruin rebuild discount are not built.
- M02: no unbuilt iteration file. Not built: season weights, winter raid rule, start screen, terms buttons in the widget.
- M04: no unbuilt iteration file.

## Legacy claims dropped (with reason)
- M02 "raid size class random with weights 50/35/15": the code picks the class uniformly (`plan.first_raid`). Spec says "at random".
- M02 "early raids hit vassals first, plunder raids hit the main town during the whole game": only the subjugation raid targets vassals; a plunder raid always targets home. Only the code rule is written.
- M02 loss of the final battle: no rule in code (README says TBD). Not written.
- M02 season weights, "Main raids come from spring to autumn": no code.
- M02 ransom demand before a raid: belongs to M06.
- M03 carry caps "Hussite grain 10, iron 5, bandit grain 5": code has one `carry_cap = 10`.
- M03 storage tiers, loss share per trip, ruin rebuild discount, hostages: no code.
- M03 "Units rout on their own": not a mod behavior.
- M04 "Bandits raid the home region and vassals like small local raids", "bandit raid size uses the random class weights": no code. The converted bandits are spawned by `homeless_rebel`; their raid is native game behavior.
- M04 oppression/prosperity effects on bandits: belong to M12 (only the three modifiers are written).
- M04 "captured bandits become forced labor": no code.
- spec 22 row patches, id ranges, pak build, release: harness capabilities (H2), not written here. Only `example` feature has patches.
- spec 24 harness save action `save_game`: capability `harness/save-game`. Only the mod side (ModState, no save call) is here.
- M01 Tunable "flush interval": not in code (flush is on each change; `autoflush` flag only).

## Feedback files
None written. `feedback.md` of M01, M02 and M03 say "(none yet)". M04 has no feedback file.

## Doubts
- `mod_state/init.lua` and `raid_widget` mention rules about `LoopAsync`, but `mod_state` itself uses two `LoopAsync` loops (load wait, hook retry). The wiki says features must not start their own. I did not write "no feature starts a LoopAsync" as a requirement. The scheduler requirement only covers the scheduler.
- Scheduler tick: the code is 50 ms; the wiki says 100 ms. Spec uses the code (50 ms).
- The scenario `invasion/subjugation_raid.py` accepts a wait of 55 to 120 days (spec says 60 to 120, as in config). The extra 5 days are margin in the check.
- `raid_composition.py` is named for M05.02 (roles); the role composition requirement is placed in `mod/invasion` because the code is in `features/invasion/plan.lua`. Group MB (`unit_balance`) may overlap on "Hussite roles".
- The siege rule (vassal lost with reason `taken` after 8 days) is in `tribute` (group MB). `mod/invasion` only has the target choice. `vassal_targets.py` is cited as its check.
- `native_plunder.py` turns roles off with `invasion_set_roles`, so "native raid" scenarios do not test the default (lord) raid for the A1 numbers.
- Not verified in a run: lord-raid `loss`/`time` reasons are covered by `lord_leave_reason.py` (needs option `LEAVE_REASON`); the scenario file runs one reason per run.
- The "Terms" widget line depends on `sack_and_terms` (group MB). It is checked only by fake game text tests.
- `example` feature (layout stub) has no requirement.
