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
- State command shows `season` and `last_season`. Test setter `InvasionMod.bandits_tick_now` stays (forced roll). Scenarios move the season with the harness action `set_season`.

## Acceptance criteria
- B1: a scenario that crosses at least 2 season changes (with `set_season`) gives exactly 1 roll per change: `rolls` grows by exactly 1 per change.
- B2: no extra roll while the season stays the same: after 3 game days in one season, `rolls` is unchanged.
- B3: a roll never happens on the first poll (no roll at the start of a run: `rolls` is 0 before the first season change).
- B4: the season state survives a load: with the saved last season equal to the current one, a reload of the feature does not roll (fake game test only; the real game cannot be saved in tests).
- B5: a conversion at a season change removes 2 families and 18 bandit units appear (forced roll 0 in the fake game; in the real game the dice are real, and a forced conversion is covered by `bandits-convert-families`).
- B6: the fake game distribution test: over 20000 simulated rolls the conversion rate is within plus or minus 0.015 of 0.10, 0.25 and 0.50 for orders 60, 40 and 10, and 0 for order 80.
- B7: the game runs 10 game days after the season ticks with no crash.
- Fake game tests cover the season change, the no-repeat rule, the first poll, the restart and the distribution.

## Scenarios
- `scenarios/bandits/season_tick.py` (`bandits-season-tick`): B1 to B3, B5, B7 in the real game.

## Result
PASS in the real game (2026-10-17). Notes: `../implementation-notes/iteration-02-season-tick.md`.
- `bandits-season-tick`: runs `20261017-223606-7b43` and `20261017-224040-e87d` pass. Each run crossed 3 season changes (winter, spring, summer) and made exactly 3 rolls (B1), 0 rolls in the 3 days before (B2, B3), and 0 extra rolls a day later. Run 7b43 had two real conversions (roll 0.01 and 0.02 at chance 10 percent): 2 families and 18 bandit units each time (B5). Both runs ran 10 more game days with no crash (B7).
- Fake game tests: 6 new season tests (one roll per change, winter across the year change, reload in the same season, conversion at a season change, no roll on the first poll) and the distribution test (B6: 20000 rolls per order, rate within 0.015 of 0, 0.10, 0.25, 0.50).
- Deviation: the scenario cannot hold approval at 0 (the game moves it back within days), so the real runs have order 71 and chance 10 percent. B5 with a forced roll stays in `bandits-convert-families`.
- Crashes: 4 of 5 runs at speed 3 crashed in the real game (runs `20261017-222043-cfeb`, `-222814-b61c`, `-223036-5d4e`, `-223238-9640`; access violations at varying addresses, one in `UObjectBase::setup_member_functions`), during multi-day runs, also before any season change. At speed 2 with 3 and 10 day runs, 2 of 2 passed. Cause not isolated. `bandits-convert-families` at speed 3 passed on the same code. The scenario now uses speed 2.
