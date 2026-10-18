# M05 iteration 03: armored-militia (notes)

## Method
Scenario `unit-balance-armored-fight`: 32 `spearMilitia` against 4 squads of `Brigands` (72 units, 2.25 times; 3 squads = 1.69 times were two first runs). Armor is modeled by a live write `def` 17.2 on the militia (def 7.2 plus mail 10). The write runs while the feature is off. Then the feature is switched on and one pass is applied. Interleaved loop of `run.py --slot auto` (as M05.01), 5 valid runs per variant. A run with no casualties (no contact, the known flake) is excluded and was repeated.

## Result (4 squads)
| Variant | Valid runs | Militia wins | Mean militia loss rate | Mean bandit loss rate |
|---|---|---|---|---|
| vanilla (feature off, no armor) | 5 | 0 | 0.48 (0.47 to 1.0) | 0.05 |
| feature on, militia unarmored (def 0) | 5 | 0 | 0.62 | 0.13 |
| feature on, armored (def 17.2), weapon bonus off | 5 | 5 | 0.175 | 1.0 |
| feature on, armored, weapon bonus on (att x1.5, armorPierce +2) | 5 | 5 | 0.094 | 1.0 |

- Win: bandit loss rate 1.0 and a lower militia loss rate.
- Weapon bonus against armor only: militia loss rate 0.094 against 0.175 (permutation test, one-sided p 0.028, two-sided 0.056; N 5 and 5).
- Run ids. vanilla: 060726-c582, 061405-1e63, 062106-0ad5, 062928-1e7f, 063740-e03a (060110-7edd no contact). unarmoured: 060244-57a5, 060856-051f, 061542-1a25, 062232-37b4, 063055-28ae. armor: 060406-f8f5, 061050-8acd, 061728-b0e7, 062457-56dc, 063200-a32b. armor-weapon: 060545-785f, 061228-db8b, 061942-8a18, 062727-0df8, 063906-45ba (063338-b28f and 063627-c6ea no contact). All ids start with `20261018-`.
- Earlier check at 3 squads (1.69 times): armor-weapon 2 of 2 wins (`20261018-053854-dff8`, `054057-ba8d`); armor only and weapon, 5 pairs: all 10 won (loss rates 0.0 to 0.09).

## Findings
- The live write of `att` and `armorPierce` on `SMUnit` works (read back equals written) and the fight changes.
- Armor already pays off here, because the unarmored rule (iteration 01) strips the bandits to def 0 and block 0. Spec 25 tested armor against normal bandits and lost. With both rules the armored militia beat 2.25 times its size in 5 of 5 runs, with or without the weapon bonus. The weapon bonus cuts the losses by about half.
- Armor from smiths is not modeled by the test: it is a def write. The rule classifies by `def` 10 to 40, as real mail would give.
- The no-contact flake hit 3 of 27 runs (about 11 percent).

## Deviations
- The size test is 2.25 times (the target says 1.5 to 2 times); a 4th squad was the only way to get above 1.69 with whole squads. The result holds for the stricter fight.
- `suite.py` has no `--slot` (issue #160), so the A/B ran as a shell loop.
