# M06 iteration 04: sack-target

Issue: #224. Branch: `feat/M06-sack_and_terms-04-sack-target` (stacked on PR #223, M02.07).

## Goal
The sack hits the region under attack, or the home region. It must not hit "the first region that the player owns": after a fallback capital move (M06.03) that region may be the capital.

## Design
- `HarnessSack` functions take an optional `region` (object name). `HarnessSack.playerRegion(name)` returns that region when the player owns it. Without a name it is `core.player_region()` as before.
- `sack_and_terms/rules.sack_region(target, home, player_regions)`: the raid target when the player owns it; else the home region (ModState `vassals_home_region`) when the player owns it; else nil (the old first-region behaviour).
- The raid target comes from the raid summary (`target`, M08.02). A manual sack (`sack_now`) uses the home region.
- The stores for the goods step are read from the same region (`raid_behavior.world.stores(region)`).
- The result of a sack has `region`.

## Acceptance criteria
- R1: with the capital moved, a sack with no raid target hits the home region: the sack result region is the home region and the capital loses no family.
- R2: a raid that targets a player region sacks that region (fake game).
- R3: a raid on a region the player does not own sacks the home region (fake game).
- R4: no known region keeps the old behaviour (fake game).
- R5: no crash in the run.

## Scenarios
- Fake game: `SackRegionTests`, `test_fakegame_harnesssack.py`.
- Real game: `sack-and-terms-sack-region` (new game): vassal, fallback capital, then `sack_now`.

## Result
PASS in the real game (2026-10-18).
- `sack-and-terms-sack-region`: runs `20261018-103938-e3e5` and `20261018-104509-b9b3` pass (R1, R5). The sack named the home region (5 families to 2 at difficulty 3); the capital kept its families.
- Fake game tests: `SackRegionTests` (5), `test_fakegame_harnesssack.py` (1).
- Limit: the scenario cannot force the order of `engine.regions`, so the real run does not prove that the old code picked the capital. The fake game proves the selection rule.
- The raid still starts at `core.player_region()` (first region); only the sack and its stores are now region aware.
