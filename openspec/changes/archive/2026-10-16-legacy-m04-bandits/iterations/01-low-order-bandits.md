# M04 iteration 01: low-order-bandits

Branch: `feat/M04-bandits-01-low-order-bandits`. Issue: #155.

## Goal
Low approval lowers Public Order. Low Public Order turns families into bandits through `homeless_rebel`.
The exact season tick and the exact chances belong to iteration 02. This iteration adds a simple fixed-interval tick so the rules can be tested.

## Changes
- New feature `Scripts/features/bandits/` (requires `invasion`, so ModState, the difficulty and the clock exist).
- Config `bandits`: bands (below 75: 10%, below 50: 25%, below 25: 50%), families per conversion, tick length in game days, minimum families left.
- Public Order debuff (M00 decisions 11 to 15): debuff = `ceil((100 - approval) x difficulty)`. The mod keeps its estimate of the game's own value ("natural order") and writes `natural - debuff` to `Region.publicOrder`.
  The game rewrites Public Order about once per game day (spike, `../implementation-notes/iteration-01-low-order-bandits.md`). A value that differs from the mod's last write is taken as the new natural value. The debuff never stacks.
- Conversion: one roll for the region at each tick (decision 12). The chance comes from the bands and the debuffed Public Order. On success the mod calls `HarnessBandits.homeless_rebel` (mode `home`, template `Brigands`, 2 families, 1 squad). No `turnToBandit`, no `Region:AddNewFamily`.
- Simple tick (stand-in for iteration 02): every `tick_days` game days (default 30), one roll.
- ModState keys (mod `invasion`): `bandits_converted_families`, `bandits_last_tick_day`, `bandits_rolls`, `bandits_natural_order`, `bandits_written_order`.
- Named commands: `InvasionMod.bandits_state`; test setters `InvasionMod.bandits_set_approval` (writes `Region.Approval`) and `InvasionMod.bandits_tick_now` (optional `roll` from 0 to 1 forces the dice). Difficulty uses `invasion_set_difficulty` (M02).

## Acceptance criteria
- A1: at approval about 65 and difficulty 1, `Region.publicOrder` read after 2 game days is `natural - debuff` within plus or minus 5 (natural and approval are read in the same `bandits_state` answer; at approval 65 the value is 65).
- A2: after 5 more game days at the same approval, `publicOrder` is within 10 of `natural - debuff` and is 0 or more (no stacking).
- A3: after approval is set to 100, `publicOrder` equals the natural order at once.
- A4: at difficulty 2 the debuff doubles (approval 71 gives `ceil(29 x 2)` = 58, order 42), within plus or minus 10, and the order is 0 or more.
- A5: with Public Order under 25 and a forced roll of 0, one tick removes 2 families (families 10 to 8) and one squad of 18 bandit units appears.
- A6: with Public Order under 25 and a forced roll of 0.99 (chance 50 percent), no family is removed.
- A7: with Public Order of 80 or more and a forced roll of 0, no family is removed.
- A8: the game runs 10 game days after a conversion with no crash.
- Fake game tests cover the debuff, the no-stack rule, the game rewrite, the roll logic and the tick interval.

## Scenarios
- `scenarios/bandits/order_debuff.py` (`bandits-order-debuff`): A1 to A4.
- `scenarios/bandits/convert_families.py` (`bandits-convert-families`): A5 to A8.

## Result
Result: PASS in the real game (2026-10-17), with deviations. Notes: `../implementation-notes/iteration-01-low-order-bandits.md`.
- The game does NOT keep a written Public Order: it rewrites it to its own value about once per game day (spike run `20261017-213853-d83a`). So the mod writes again after each rewrite (deviation from "write once"). A1 to A4 hold with this method.
- `bandits-order-debuff`: run `20261017-214349-93e2` pass. Approval 71 (the game moved the written 65 back): order 71 = 100 - 29 on days 2 and 7, 7 rewrites seen by the mod in 7 days, none stacked; approval 100 gave order 100 at once; difficulty 2 gave order 42.
- `bandits-convert-families`: run `20261017-214539-c7cc` pass. Order 100: no conversion (A7). Order 0, roll 0.99: none (A6). Roll 0: families 10 to 8, bandit units +18 (A5). 10 game days later the game still ran (A8).
- Fake game tests: 16 new tests pass. Full suite: only the 5 `test_install_scripts` failures that also fail on `main` (environment).
- Deviations: fixed 30 day tick instead of the season tick (iteration 02). Approval and Public Order are rewritten by the game, so the scenarios compare with the values read in the same answer. One crash in 3 spike runs (`20261017-213728-57b9`, UE4SS "Abort signal", game day 2); not repeated in 3 later runs.
