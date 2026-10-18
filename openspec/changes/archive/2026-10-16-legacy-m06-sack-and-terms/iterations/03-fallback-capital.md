# M06 iteration 03: fallback-capital

Branch: `feat/M06-sack_and_terms-03-fallback-capital` (stacked on PR #204, M09.02). Issue: #205.

## Goal
Before or during a battle the player pays to make a fortified vassal the fallback capital (M00). Simplest feasible form, all values TBD.

## Design (TBD values are marked)
- Command `fallback_move{slot}` (the later UI and the sack logic call `fallback.move`).
- Refused when: the slot has no handed-over vassal; a capital exists already; the vassal region has fewer than 8 buildings ("fortified", TBD); silver is under `150 x difficulty` (TBD).
- Steps, risky step first so a failure costs nothing:
  1. Take the region back from the lord. Variant `write` (default): write `Region.ownerPawn = player` (the change a won challenge made in spike S11). Variant `clear` (owner cleared, player claim and finalize) crashes the game, see the notes.
  2. The vassal slot gets `capital = true` and no lord (the M07 scan does not hand it over again; tribute and refugees skip it).
  3. Pay silver.
  4. Move 20 units of grain from the home stores (first of Bread 172, Grain 1, Fish 30 that the stores hold) into the first building of the capital that takes them.
  5. One `settleRegion` call on the capital: 5 families arrive.
- Not done (TBD, later): move the best units (no move order exists for a squad, spike S11), and remove families from home (removing a family kills it, spike S8). The capital gets new settlers instead of the home families.
- State (ModState): `fallback_slot`, `fallback_day`, `fallback_silver_paid`, `fallback_grain_moved`.

## Changes
- `sack_and_terms/fallback.lua`, `fallback_rules.lua`. `sack_and_terms` now requires `vassals`.
- `vassals`: slot key `capital`, export `set_capital`.
- Commands `fallback_state`, `fallback_move`, `fallback_set_min_buildings` and `fallback_set_take_back` (tests).
- Config `sack_and_terms.fallback`.

## Acceptance criteria
- F1: after the move the region owner is the player pawn.
- F2: silver drops by exactly `150 x difficulty`.
- F3: grain taken from the home stores equals grain deposited in the capital.
- F4: the capital gets 5 families for one settle call; the slot is `capital` with no lord.
- F5: an empty slot and a second capital are refused.
- F6: 5 game days later the region is still the player region and was not handed over again; no crash.

## Scenarios
- `scenarios/sack_and_terms/fallback_capital.py` (`sack-and-terms-fallback-capital`), new game.

## Result
PASS in the real game (2026-10-18), with one design change. Notes: `../implementation-notes/iteration-03-fallback-capital.md`.
- `sack-and-terms-fallback-capital` (variant `write`): runs `20261018-085523-64ec` and `20261018-085819-7a0e` pass (F1 to F6). The capital grew from 14 to 20 buildings in the 5 days after the move.
- The first design (`clear`: clear the owner, then the player claims) crashed the game in 3 of 3 runs a few game seconds after the move (access violation reading 0x50, native frames): `20261018-084541-2b07`, `20261018-084900-afca`, `20261018-085046-c0e4`. The `write` variant did not crash in 2 of 2 runs.
- Fake game tests: `harness/tests/test_fakegame_fallback.py` (8 tests).
