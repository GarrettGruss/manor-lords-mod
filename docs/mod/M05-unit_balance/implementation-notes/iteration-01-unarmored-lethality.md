# Iteration 01: unarmored-lethality (notes)

## Design
- Feature `mod/InvasionMod/Scripts/features/unit_balance/` (`rules.lua` pure rules, `init.lua` poll and commands). It needs no other feature and only the shipped shared module `ManorCore`. `HarnessCommands` is used only when present (as in M03). It does not use `HarnessTune` or `HarnessBattle` (harness-only modules). Spec 28 shows the same idea; the mod has its own small copy.
- Unarmored: own `def` below `armored_def_min` (10) when first seen, and not both `def` and `block` 0. No side test, no squad test: the rule holds for all sides. Squadless units with def 0 and block 0 are skipped by this rule.
- Rule: `def = def x 0`, `block = block x 0` (config). A poll every 2000 ms visits `FindAllOf("SMUnit")`. An unknown living unit is read (`dead`, `def`, `block`) and maybe written. A known unit costs one read of `def` (to find an address reused by a new unit). Records of missing units are dropped.
- Commands: `unit_balance_state`, `unit_balance_set` (enabled, def_factor, block_factor; off restores), `unit_balance_apply` (one pass now). HarnessActions was not changed (version stays 55).

## Findings
- In the real game the mod is on from boot. In the first off run the state showed 19 units changed and 335 seen before the scenario switched it off; the off command restored them (`tracked` 0). Units of the loaded save (levies, guards) are therefore also changed by the rule.
- Baseline (rule off): mean def 6.7 (militia) and 2.9 (Brigands). On: 0 for both.
- The fight with both sides unarmored: militia loss rate 0.23 to 0.49 (x2.14). Bandits die in 4 of 6 on-runs anyway (loss rate 1.0), so the militia pay more for the same win. In 2 of 6 on-runs the bandits survived with 19 and 12 units (militia lost 23 and 26).
- `casualties_total` is no good as the A/B metric (capped by 36 bandits).
- One of 7 off runs had no contact (1 casualty): same flake as in spec 25. It was replaced.

## Deviations
- The suite tool has no `--slot auto` (it uses slot 0, which could collide with another agent's game). The A/B ran as a script loop of `run.py --slot auto` runs, off and on interleaved. The suite file `harness/suites/unit-balance-ab.json` is kept for later runs; the permutation test came from `suitelib/stats.py`.
- A4 metric changed from `casualties_total` to `player_loss_rate` after the first look at the data (see the iteration file).
- Armored comparison is by the `def` threshold, not by item ids. Open: a militia with a shield has block above 0 but small def; it is unarmored and loses its shield value. Iteration 04 (counters: shields against crossbows) must revisit `unarmored_block_factor`.
- The damage ratio 2 to 3 is measured as a loss rate ratio (open question 6 of the README): 2.14 mean, 2.6 median.

## Runs
- `m05-kept-1` (armored kept): pass.
- Lethality A/B: off `m05-ab-off-2` to `-7`, on `m05-ab-on-1` to `-6`. `m05-ab-off-1` (no contact) excluded.
