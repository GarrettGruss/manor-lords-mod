# Part A: hand cannon against crossbow militia (A/B)

Date: 2026-10-18. Suite `harness/suites/custom-unit-ab.json`, scenario `combat-levers`, pak `handcannon`, fixture `base`, one fight per run, speed 3. Suite id `20261018-110435-6c0f`, runs `-001` to `-021`. N = 5 per variant. The statistics are a heuristic (permutation test and Cohen's d, see spec 10 `ab-statistics.md`).

| Variant | Player loss rate (5 runs) | Bandit loss rate | Player won | Fight time (wall s) |
|---|---|---|---|---|
| 32 crossbowMilitia vs 18 Brigands | 0.31, 0.38, 0.41, 0.53, 0.13 (median 0.38) | 1.0, 0.72, 0.72, 1.0, 1.0 | 5 of 5 | 17.5, 17.3, 17.0, 17.2, 11.5 |
| 32 handCannon vs 18 Brigands | 0.03, 0, 0, 0, 0 (median 0) | 1.0, 1.0, 0.67, 1.0, 1.0 | 5 of 5 | 11.7, 11.6, 11.6, 8.8, 11.5 |
| 32 crossbowMilitia vs 32 crossbowMilitia | 0.91, 0.59, 0.47, 0.28, 0.09 (median 0.47) | 0.63, 1.0, 1.0, 0.94, 1.0 | 4 of 5 | 14.5, 17.4, 14.5, 20.4, 17.5 |
| 32 handCannon vs 32 crossbowMilitia | 0.03, 0, 1.0, 0, 0 (median 0) | 1.0, 1.0, 0.69, 1.0, 1.0 | 4 of 5 | 11.7, 11.7, 63.0, 8.9, 11.6 |

Run ids:
- crossbow vs Brigands: `-001 -003 -005 -007 -009`.
- handCannon vs Brigands: `-002 -004 -006 -008 -010`.
- crossbow vs crossbow: `-011 -014 -016 -018 -020`. Run `-013` failed (flaky). The suite retried it as `-014`.
- handCannon vs crossbow: `-012 -015 -017 -019 -021`.

Verdicts from the suite report:
- handCannon against Brigands, compared with crossbow: player loss rate 0.38 to 0 (d -3.25, p 0.008, `different`). Fight time 17.2 to 11.6 s (p 0.04).
- handCannon against crossbow in a duel: median loss rate 0.47 to 0 (d -0.69, p 0.33, `inconclusive`). One run (`-017`) was lost by the hand cannon (loss rate 1.0, 63 s). The spread is large. The A/A control (crossbow against crossbow) shows the noise: the player side won 4 of 5.

Reading:
- The item rows drive ranged combat. Raising `rangedAtt` 32 to 64 and `armorPierce` 0 to 8 made the squad kill faster and lose almost nobody. So the item row is the lever (open question 2: item, not template and not code).
- `Speed` 0.5 and `shootingRange` 6000 (shorter than the crossbow 11500) did not make the unit weak. The effect of `Speed` was not isolated. It may slow walking, not reload. Range and reload were not tested separately.
- The balance numbers are not tuned. This only shows that a new row fights and that item values matter.
