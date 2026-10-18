# M05 iteration 04: counters-veterancy

Branch: `feat/M05-unit_balance-04-counters-veterancy`. Stacked on PR #193 (M05.03), which is stacked on PR #182. Issue: see the PR.

## Goal
M00 "Army counters": pavises and shields against crossbows, pikes and a held line against sword men, archers against light raiders. M00 "Veterancy": surviving units keep experience, losing the best retinue hurts.
Also revisit the shield block loss from M05.01 (`unarmored_block_factor` 0 removes the block of shield-bearing unarmored militia).

## Facts so far
- Experience (`SMUnit.combatExperience`) rises in fights, survivors keep it, the value can be written (spec 10 spike C2, `set_squad_experience`). The effect of experience on strength was never measured.
- Spear against sword is a native counter (spec 10, spike C1, p 0.029).
- There is no per-hit hook (spec 25). A counter must be a stat value, not a rule on each hit.

## Plan
1. Generic scenario `unit-balance-matchup` (templates, squad counts, experience, rule switches by option). Measure each counter pair with N >= 5 per variant, interleaved:
   - shield: militia with block kept (`block_factor` 1) against block 0, enemy crossbows.
   - pike: `spearMilitia` against `militiaFoot`, rule on.
   - archers: `bowMilitia` against `Brigands`.
   - veterancy: militia with experience 0 against experience 25 (`set_squad_experience`).
2. Decide each rule from the data. A counter that exists natively gets only a note. A missing one becomes a stat value in config.
3. Veterancy rule: the experience of a unit scales its `att` and `def` in steps (config `veterancy`). A recheck on a slow poll reads the experience of known units.
4. Revisit `unarmored_block_factor` from the shield data without losing the M05.01 lethality (militia loss rate ratio 2 to 3 times, A/B).

## Acceptance criteria
- A1: each counter pair has an A/B result (N >= 5 per variant) in the notes, with the verdict native, added or none.
- A2: veterans (experience 25) win a fight that the same unit with experience 0 loses or loses more units in: militia loss rate lower with the rule, p <= 0.1 (small N: heuristic).
- A3: the veterancy poll adds no crash in a 3 run series and reads at most one value for each known unit on a slow pass.
- A4: the shield decision is recorded; lethality (M05.01 A4) is rechecked if the factor changes.
- A5: fake-game tests for the veterancy tiers, restore and command validation. The full suite passes.

## Result
not started
