# M13 iteration 01: manor-storage

Branch: `feat/M13-manor_stronghold-01-manor-storage`. Issue: #207.

## Goal
The manor holds more goods after a tech tree upgrade. The mod owns the store (spec 12: `manor_put`, `manor_take`). The capacity is a mod rule, so Lua can change it.

## Decisions used
M00 decisions 22 and 23 (tech tree nodes, data driven). The M00 rule: manor upgrades are open to both paths. The manor is the safest store (M03 storage tiers, a later layer).

## Changes
- New feature `manor_stronghold` (`rules.lua` pure, `world.lua`, `init.lua`). No requirement.
- Capacity of one manor module = `storage_base_capacity` (200, from spec 12) + bonus. The feature sets `HarnessManor.CAPACITY`.
- New tree effect kind `manor_storage` (add, units). Nodes `iron_hand` and `amnesty` (second node of each path) give +200 each (TBD). So both paths can upgrade.
- `tech_tree` pushes the bonus to `manor_stronghold.set_modifiers`.
- Commands: `manor_state`, `manor_put`, `manor_take` (prefix `InvasionMod.`). They call the shared module `HarnessManor`.
- `mod.json`: feature `manor_stronghold`, shared module `HarnessManor`.

## Acceptance criteria
- S1: before an upgrade the capacity is 200 and a put of 201 units is refused.
- S2: after the node `amnesty` (Prosperity) the capacity is 400. A put of 300 units works and a put over 400 is refused.
- S3: a take returns the goods and the region stock follows (put +N, take -N).
- S4: the goods stay in the manor after 2 game days.
- Fake game: capacity totals, both paths, refusals, no manor built.

## Scenarios
- `mod/InvasionMod/scenarios/manor_stronghold/manor_storage.py` (`manor-stronghold-storage`), fixture `manor-bailey` (a built manor house, no mouse).

## Result
PASS in the real game (2026-10-18), fixture `manor-bailey`. Runs `20261018-090003-97fb` and `20261018-090634-fdf1` pass (S0 to S4). A third launch (`20261018-090206-a900`) ended `harness_error` at boot (PAUSING), not a mod problem.
- Fake game tests: `harness/tests/test_fakegame_manor_stronghold.py` (10 tests).
- Deviations: the nodes are not new. The `manor_storage` effect was added to `iron_hand` and `amnesty` so the 8-node tree stays. Raiders do not yet treat the manor store differently (M03 storage tiers, later). Values TBD.
- Notes: `../implementation-notes/iteration-01-manor-storage.md`.
