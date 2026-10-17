# M04 iteration 02: season-tick

Branch: `feat/M04-bandits-02-season-tick`. Issue: #161.

## Goal
Replace the fixed 30 day tick with the season tick (M00 decisions 12 and 14). The conversion roll happens once per region at each season change.
Chances stay: Public Order below 75: 10%, below 50: 25%, below 25: 50%.

## Changes
- The game exposes the season as `RTSMultiEngineCPP.TemporalComponent.Season` (0 winter, 1 spring, 2 summer, 3 autumn). See `docs/harness/04-telemetry-and-assertions/implementation-notes/time-measurements.md` and `docs/harness/07-feature-test-kit/implementation-notes/actions-catalog.md`.
- The poll reads `Season`. A tick runs when `Season` differs from the saved last season. One tick per season change, one roll per region.
- ModState key `bandits_last_season` (default -1). The first read after a new game only stores the season and does not roll. After a load, the saved value equals the current season, so the same season does not fire again.
- The key `bandits_last_tick_day` stays (for state and logs). `tick_days` is removed from the config. Pure rule: `rules.season_changed(current, last)`.
- State command shows `season` and `last_season`. Test setter `InvasionMod.bandits_tick_now` stays (forced roll). New test setter `InvasionMod.bandits_set_season` is not needed: scenarios use the harness `set_season`.

## Acceptance criteria
- B1: a scenario that crosses at least 2 season changes (for example spring to summer to autumn with `set_season`) gives exactly 1 roll per change: `rolls` grows by exactly 2.
- B2: no extra roll while the season stays the same: after 5 game days in one season, `rolls` is unchanged.
- B3: a roll never happens on the first poll (no roll at the start of a run: `rolls` is 0 before the first season change).
- B4: the season state survives a load: with the saved last season equal to the current one, a restart of the feature does not roll (fake game test; real game: not tested, no save function may be used).
- B5: forced roll 0 with Public Order below 25 at a season change converts 2 families (families 10 to 8) and 18 bandit units appear.
- B6: the fake game distribution test: over 20000 simulated rolls the conversion rate is within plus or minus 0.015 of 0.10, 0.25 and 0.50 for orders 60, 40 and 10, and 0 for order 80.
- B7: the game runs 10 game days after the season ticks with no crash.
- Fake game tests cover the season change, the no-repeat rule, the first poll, the restart and the distribution.

## Scenarios
- `scenarios/bandits/season_tick.py` (`bandits-season-tick`): B1 to B3, B5, B7 in the real game.

## Result
Not started.
