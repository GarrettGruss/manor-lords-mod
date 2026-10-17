# M05 iteration 01: unarmored-lethality

Branch: `feat/M05-unit_balance-01-unarmored-lethality`. Issue: #156.

## Goal
Armor matters. A unit without armor takes much more damage than the same unit with armor (M00 target: 2 to 3 times). The mod does this with a live stat write. It adds no pak and no hook.

## Definition of "unarmored"
- A living `SMUnit` is unarmored when its own `def` is below `armored_def_min` (config, first value 10) when the mod first sees it.
- Why `def`: `def` is the sum of body armor and helmet (and shield `def`). Measured means: `Brigands` 2.9 to 3.2, `militiaFoot` about 5, `spearMilitia` 7.2, `retinue_tier3` 62 (spec 25). Mail armor (item 164) adds 10 alone. So bandits and plain militia are unarmored, and a unit with mail or retinue gear is armored.
- A unit with `def` 0 and `block` 0 is skipped (nothing to reduce; this also skips units with no gear).
- The test uses the base value once, when the unit is first seen. The mod keeps the original values, so the test does not flip after its own write.
- Sides are not tested. The rule holds for the player, bandits, raiders and AI lords alike. Squad ownership is not needed.

## Rule
- For each new unarmored unit: write `def = def * unarmored_def_factor` and `block = block * unarmored_block_factor` (config, first values 0 and 0; spec 25 measured def 0 and block 0).
- A poll every `poll_ms` (2000) finds new units. This applies the rule to each new squad within one poll. The poll reads only `dead` and `def` of a unit it has not seen, and `def` of a unit it knows (to find a reused address).
- The mod must not need a harness-only module. It uses `ManorCore` only. Commands use `HarnessCommands` when present (as M03 does).

## Changes
- New feature `Scripts/features/unit_balance/` (`rules.lua` pure rules, `init.lua` poll and commands). No dependency on other features.
- Config table `unit_balance` in `config.lua`: `enabled`, `poll_ms`, `armored_def_min`, `unarmored_def_factor`, `unarmored_block_factor`.
- Named commands: `unit_balance_state` (switch, config, counts, mean written values), `unit_balance_set` (enabled, factors; disabling restores the original values), `unit_balance_apply` (one pass now).
- Scenarios in `mod/InvasionMod/scenarios/unit_balance/`: `unit-balance-lethality` (one fight, variant by option), `unit-balance-armored-kept` (armored unit is not changed, unarmored is).
- Suite `unit-balance-ab`: rule off against rule on.

## Acceptance criteria
- A1: after a spawn and one apply, the mean `def` and `block` of spawned `spearMilitia` and `Brigands` equal `base * factor` (0 with the first values), read back from the units. All of the units that the rule counts as unarmored are changed (`changed == unarmored`).
- A2: units with `def >= armored_def_min` (a `retinue_tier3` squad, def 62) keep their `def` and `block` exactly.
- A3: the rule needs no new call: a squad that spawns later (second spawn, no command) is changed within 2 polls (4 s wall).
- A4 (A/B, N >= 5 per variant, interleaved by the suite, fight 32 `spearMilitia` against 2 squads of `Brigands`): total casualties of both sides (`casualties_total`) with the rule on are at least 1.5 times the mean with the rule off, and the permutation test gives p <= 0.1. Reference: spec 25 measured 1.9 times militia losses with def 0 and block 0 on one side. The upper bound is 3.5 times (more would mean the rule is too strong for the 2 to 3 times target; compare the loss rate too, which stops at 1.0).
- A5: with the rule off (`unit_balance_set enabled=false`), unit values are the original ones. The A/B "off" variant must equal the vanilla fight (mean player `def` above 5 at the start).
- A6: fake-game tests for classification, writes, restore, command validation. The full unit suite passes.

## Scenarios and measures
- `unit-balance-lethality`: clears the battle, sets the rule on or off from the option `UB_RULE` (`on` or `off`), spawns the groups, applies the rule, logs the stats, runs the fight (`run_fight`), records `casualties_total`, `player_loss_rate`, `bandit_loss_rate`, `player_casualties`, `bandit_casualties`, `player_def_mean`, `bandit_def_mean`.
- The raw damage ratio is not measured (no per-hit hook, spec 25). The casualty count is the proxy. A fight ends at a rout or stand-off, so the ratio is capped (M05 open question 6).

## Result
not started
