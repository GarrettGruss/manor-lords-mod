# M05 iteration 03: armored-militia

Branch: `feat/M05-unit_balance-03-armored-militia`. Stacked on PR #182 (M03.02 follow-up). Issue: see the PR.

## Goal
Armor investment pays off (M00): an armored militia group beats 1.5 to 2 times its size in bandits in most runs. Spec 25 found that armor alone is not enough (def 32 or 62 on militia: 0 of 5 wins against 50 bandits). Armor together with weapon values (retinue: att 5 to 7, armorPierce 1 to 2) wins 5 of 5.

## Design
- An armored unit is a living `SMUnit` with `armored_def_min` (10) <= def < `heavy_def_min` (40) when first seen. Mail on a militia gives about 17. Retinue units (def 62) are heavy and are left alone: they win already.
- Rule: for each new armored unit write `att = att x armored_att_factor` and `armorPierce = armorPierce + armored_pierce_add` (config; first values 1.5 and 2, TBD by the A/B).
- The rule holds for all sides (as the unarmored rule does).
- The record of a changed unit keeps the original values, so `unit_balance_set enabled=false` restores them.
- Commands: `unit_balance_set` gets `att_factor` and `pierce_add`. `unit_balance_state` shows them.
- No new call, no pak. Unknown before the spike: do live writes of `att` and `armorPierce` change the fight? (spec 25 did not test it.)

## Test
Scenario `unit-balance-armored-fight`: 32 `spearMilitia` against 3 squads of `Brigands` (54 units, 1.69 times). The rule is off while the groups spawn. Then the scenario writes `def + 10` (mail) on the militia (live write by `set_unit_stat` is not per unit, so the scenario adds 10 with one write of 17.2) and switches the rule on. Variants: `UB_WEAPON=off` (att factor 1, pierce add 0) and `UB_WEAPON=on`.

## Acceptance criteria
- A1: with the weapon values on, militia with armor win (bandit loss rate 1.0 and militia loss rate below the bandit loss rate) in at least 3 of 5 runs (N >= 5, interleaved with the weapon-off variant).
- A2: the militia win rate with weapon values on is higher than with armor only; permutation test on `player_loss_rate`, p <= 0.1 (small N: heuristic).
- A3: a heavy unit (retinue, def 62) keeps att and armorPierce; unarmored units are handled as in iteration 01.
- A4: fake-game tests for the new rule, restore and command validation. The full suite passes.

## Result
not started
