# M05 iteration 04: counters and veterancy (notes)

Scenario `unit-balance-matchup` (options: templates, squads, rule on/off, block factor, live stat writes on the player group, experience, reach, veterancy). One fight per run, interleaved shell loops of `run.py --slot auto` (no `--slot` in `suite.py`, issue #160). Win: enemy loss rate 1.0 and a lower player loss rate. Runs with `harness_error` (4) or no contact (3) are excluded. All run ids start with `20261018-`.

## Counter measurements (N 4 to 5 per variant)
Player group 1 squad `spearMilitia` (32), unless stated.
| Pair | Variant | Valid | Wins | Player loss rate | Enemy loss rate |
|---|---|---|---|---|---|
| vs 1 squad `crossbowMilitia` | feature off | 5 | 0 | 0.91 | 0.0 |
| | rule on, block 0 (M05.01) | 4 | 0 | 0.86 | 0.0 |
| | rule on, block kept (factor 1) | 4 | 0 | 1.0 | 0.0 |
| | def written 17.2 | 5 | 0 | 0.84 | 0.0 |
| | block written 40 | 5 | 0 | 0.91 | 0.0 |
| | def 40 and block 40 | 5 | 0 | 0.96 | 0.0 |
| vs 1 squad `militiaFoot` (sword and axe) | feature off | 5 | 0 | 0.78 | 0.31 |
| | att written 6 | 5 | 5 | 0.49 | 1.0 |
| | def written 17.2 | 5 | 1 | 0.83 | 0.75 |
| `bowMilitia` vs 1 squad `Brigands` | feature off | 4 | 3 | 0.44 | 0.83 |
| | rule on | 4 | 2 | 0.35 | 0.74 |
Verdicts:
- Shield or pavise against crossbows: **no counter in the game data and no stat lever**. Crossbowmen (rangedAtt 32) kill the spear militia with no loss, whatever `def` and `block` the militia have. Block kept or removed makes no measurable difference, so the M05.01 block loss (`unarmored_block_factor` 0) stays. A real pavise counter needs a per-hit rule (no hook exists, spec 25). Open.
- Pikes against sword men: not native with these units (spear att 4 loses to sword att 5). Melee is decided by `att`; `def` does not help. Lever: a pike bonus (below).
- Archers against light raiders: native. Bow militia win 3 of 4 against Brigands with the feature off and 2 of 4 with it on, with a loss rate of 0.35 to 0.44. No rule needed.

## Pike bonus (config `reach_att_add` 1.0)
- Unit `range` values (probe `20261018-083257-a607`): spear 120, villagers 100, short sword 65, polearm 75, axes 130 and more. A pike unit is a unit with `range` 110 to 125.
- `spearMilitia` (32) vs `militiaFoot` (32), rule on: bonus 0: 1 of 5 wins, player loss 0.79, enemy loss 0.69. Bonus 1: 3 of 4 wins, player loss 0.66, enemy loss 1.0 (loss rate difference p 0.40, wins only a trend).

## Veterancy (config `veterancy`)
- Rule: tier = floor(experience / step), at most `max_tier`; `att` and `def` are scaled by 1 + tier x `per_tier`. A slow pass (every 5th poll) reads `combatExperience` of each unit. A tier change multiplies by the ratio of the factors. Restore divides back.
- Test: 32 `spearMilitia` with experience 5 (written) vs 2 squads of `Brigands`, rule on.
  - `per_tier` 0.04 (+20 percent at tier 5): wins 2 of 4 (vet) against 2 of 5 (vet off) and 4 of 5 for experience 0. No effect.
  - `per_tier` 0.1 (+50 percent at tier 5): 5 of 6 wins, player loss 0.38 against 2 of 6 wins and loss 0.70 with veterancy off (permutation p 0.035). Chosen default.
  - Default config run 3 of 3 wins (loss 0.59).
- Natural experience is small (spike C2: 0.5 to 1.3 on the mean unit after a fight), so `step` is 1.0.
- Open: experience across a save and load was not tested.

## Regression (M05.01 lethality)
`unit-balance-lethality` with the new default config: loss rate off 0.23 (4 runs), on 0.61 (5 runs). Ratio 2.6, inside the 2 to 3 target.

## Run ids (all `20261018-`)
- Counters and shield: `064846-86da`, `070118-0241`, `071215-7c57`, `072501-77e3`, `073537-70f0` (shield-vanilla); `065213-34f4`, `071351-7877`, `072714-4b3c`, `073726-8c4f` (block 0); `065341-6f65`, `070444-a795`, `071610-d56a`, `073833-95ab` (block kept); pike-vs-sword `065604-a262` and four more in the same loop; bows `065815-cd68` to `074303-945d`; lever probes `074526-6fca` to `082619-4a92`.
- Reach: `083409-30df` to `091027-aae6`. Veterancy 0.04: `083728-1753` to `091531-fc15`; 0.1: `091821-7d86` to `093647-6b5a`; default: `095732-bac5`, `095856-4158`, `100054-37da`. Lethality: `094021-8a21` to `095558-c02a`.
