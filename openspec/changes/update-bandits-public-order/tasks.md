## 1. Rules and state

- [ ] 1.1 Add the tick, the timer and the leave rules to `rules.lua`; remove `debuffed_order`, the bands and the season roll. Verified by fake game tests (`harness/tests/test_bandits_rules.py`, `test_fakegame_bandits.py`).
- [ ] 1.2 Keep mod order, tick day and timer start in ModState (saved). Verified by a fake game test of a reload.
- [ ] 1.3 Add the config values (tick days 30, manor term 10, homeless term 5, threshold 25, timer days 90, leavers 18, order gain 25) to the bandits config. Verified by a fake game test.

## 2. World

- [ ] 2.1 Overwrite `Region.publicOrder` each tick with mod order. Verified by a real game run.
- [ ] 2.2 Leave for banditry through `ManorCore.remove_families`; spawn a band only when the bandit pawn exists, else log. Verified by a fake game test and a real game run.
- [ ] 2.3 Register the telemetry metric and the `HarnessLog` line for each tick. Verified by `harness/tests/test_telemetry_mock.py` and a real game run.

## 3. Test scenarios

- [ ] 3.1 Replace `order_debuff.py`, `convert_families.py` and `season_tick.py` with test scenarios for the tick, the timer and the leave. Verified by real game runs.
- [ ] 3.2 Update `bandits_state` and `bandits_tick_now`. Verified by the test scenarios.

## 4. Docs and close

- [ ] 4.1 Update `CHANGELOG.md`, the wiki and the affected skills. Verified by `wiki.py check`.
- [ ] 4.2 Run `openspec validate update-bandits-public-order --strict`, then archive as the last commit.
- [ ] 4.3 Fill the test results table of the implementation pull request.
