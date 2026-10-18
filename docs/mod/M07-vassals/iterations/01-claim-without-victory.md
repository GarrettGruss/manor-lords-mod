# M07 iteration 01: claim-without-victory

Branch: `feat/M07-vassals-01-claim-without-victory`. Issue: #187.

## Goal
The mod sets goals = Endless (EGameGoals 2) on every start and every load, so a region claim never ends the game (spec 26: a Growth start played the victory cinematic on the first claim, 3 of 3). The mod keeps a vassal registry with a loyalty value per vassal. The registry lives in ModState (pawn Tags). The player claims one region and the mod registers it as a vassal slot.

## Decisions used
- M00 decision 20: no vassals at the start. The player settles a region and the game hands it to a friendly AI lord (iteration 02).
- Spec 26: write `gameSetup.currentGameSetup.goals = 2`. Use the shared module `HarnessGameSetup`.
- Loyalty is a mod-owned value. TBD: it lives in the pawn Tags (ModState keys per slot), not in region Tags. Why: ModState already saves the pawn Tags, and a region actor may not be saved.

## Changes
- New feature `vassals` (`mod/InvasionMod/Scripts/features/vassals/`): `rules.lua` (pure rules), `world.lua` (game access), `init.lua` (poll, commands).
- Poll (scheduler, 2 s): read the goal, write 2 when it is different, count the writes.
- ModState keys for 3 slots: `vassal<N>_region`, `vassal<N>_lord`, `vassal<N>_loyalty`, `vassal<N>_since_day`; plus `vassals_goal_writes`.
- Commands: `vassals_state` (read), `vassals_claim` (the player claims a free region by name and the mod registers a slot), `vassals_set_loyalty` (test), `vassals_set_goal` (test: write a goal to prove the mod writes it back).
- Config `vassals`: `max_vassals = 3`, `loyalty_start = 50`, `poll_ms = 2000`, `goal = 2`.
- Shared module `HarnessGameSetup` joins the `shared` list of `mod.json`.

## Acceptance criteria
- V1: within 15 s of the boot, `vassals_state.goal == 2` (fixture start and new game start).
- V2: after the test sets the goal to 3, the goal is 2 again within 15 s and `goal_writes` grew by at least 1.
- V3: on a new game (no AI lords, Growth default), `vassals_claim` of a free region leaves `currentGameVictoryStatus == 0` and the region owner is the player.
- V4: the claim registers slot 1: region name, loyalty 50, `count == 1`. The ModState Tags show the keys.
- V5: loyalty stays in 0..100 (set 150 gives 100, set -5 gives 0).
- V6: the game runs 10 more game days with no crash.

## Scenarios
- `scenarios/vassals/claim_without_victory.py` (`vassals-claim-without-victory`): V1 to V6. Run with `--new-game` (V3 needs it) and once with the default fixture (V1, V2, V4 to V6; V3 is not visible there because the base fixture does not end in victory).

## Result
PASS in the real game (2026-10-18). Notes: `../implementation-notes/iteration-01-claim-without-victory.md`.
- `vassals-claim-without-victory` on a new game: runs `20261018-055246-4163` and `20261018-055546-b692` pass (V1 to V6). A third run on the fixture `base`: `20261018-055901-17ca` passes.
- V3 on a new game: the Growth default (goals 3) was written to 2 by the mod; the claim left the victory status at 0 and the player owned the region. Without the mod, spec 26 saw status 2 in 3 of 3 runs.
- Fake game tests: `harness/tests/test_fakegame_vassals.py` (11 tests: goal write and rewrite, registry in the Tags, refusals, loyalty clamp).
- Deviation: the claim is a test command (`vassals_claim`). Detection of the player own claim and settle comes in iteration 02.
