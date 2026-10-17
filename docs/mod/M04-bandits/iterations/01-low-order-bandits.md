# M04 iteration 01: low-order-bandits

Branch: `feat/M04-bandits-01-low-order-bandits`. Issue: #155.

## Goal
Low approval lowers Public Order. Low Public Order turns families into bandits through `homeless_rebel`.
The exact season tick and the exact chances belong to iteration 02. This iteration adds a simple tick so the rules can be tested.

## Changes
- New feature `Scripts/features/bandits/` (requires `invasion`, so ModState and the daily clock exist).
- Config `bandits`: thresholds (75, 50, 25), chances (10, 25, 50 percent), families per conversion, tick length in game days, difficulty factor.
- Public Order debuff (M00 decisions 11 to 15): debuff = (100 - approval) x difficulty, rounded up. It is applied on top of the game's own value.
  The mod keeps its own estimate of the game's value ("natural order") and writes `natural - debuff` to `Region.publicOrder`.
  The game recalculates Public Order. The mod must not erase the game's change and must not stack the debuff on itself each tick.
  The spike for this rule is in `../implementation-notes/public-order-write.md`.
- Conversion: one roll for the region at each tick (decision 12). Chance by the thresholds on the debuffed Public Order. On success the mod calls `HarnessBandits.homeless_rebel` (mode `home`, template `Brigands`).
  No `turnToBandit`, no `Region:AddNewFamily`.
- Simple tick (stand-in for iteration 02): every `tick_days` game days (default 30, one roll). Iteration 02 replaces it with the season tick.
- ModState keys (mod `invasion`): `bandits_converted_families`, `bandits_last_tick_day`, `bandits_natural_order`, `bandits_rolls`.
- Named commands: `InvasionMod.bandits_state`; test setters `InvasionMod.bandits_set_approval` (write `Region.Approval`), `InvasionMod.bandits_set_natural_order`, `InvasionMod.bandits_tick_now` (optional `roll` 0 to 1 to force the dice), `InvasionMod.bandits_set_difficulty`.

## Acceptance criteria
- A1: at approval 65 and difficulty 1, `Region.publicOrder` read after 2 game days is `natural - 35` within plus or minus 5, where `natural` is `bandits_state.natural_order`.
- A2: the debuff does not stack: after 5 more game days at the same approval, `publicOrder` is within 10 of `natural - 35` and not lower than 0.
- A3: with the debuff off (approval 100), `publicOrder` returns to the game's own value (within 5) in 2 game days.
- A4: difficulty 2 at approval 65 gives a debuff of 70 (capped so Public Order stays at least 0).
- A5: with Public Order under 25 and a forced roll of 0 (always converts), one tick removes `families_per_conversion` families from the village (population falls) and bandit units rise by 18 per squad. The state counters change by the same amounts.
- A6: with a forced roll of 0.99 and Public Order under 25 (chance 50 percent), no family is removed.
- A7: with Public Order of 80 or more, a forced roll of 0 removes no family (no chance above 75).
- A8: the game does not crash in a run of 10 game days after a conversion.
- Fake game tests cover the threshold table, the round-up rule, the no-stack rule and the roll logic.

## Scenarios
- `scenarios/bandits/order_debuff.py`: A1 to A4.
- `scenarios/bandits/convert_families.py`: A5 to A8.

## Result
Not started.
