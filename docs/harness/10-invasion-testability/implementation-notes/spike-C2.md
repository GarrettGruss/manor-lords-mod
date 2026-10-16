# Spike C2: veterancy (combatExperience)

Date: 2026-10-10. Branch `feat/28-unit-data-combat`. Real game, base fixture. Runs: `s7-explore2` (probes), `s7-v1` to `s7-v3` (development), series of `veterancy` (3 of 3: `20261011-023258-22c7`, `-023457-000a`, `-023701-a4fd`, about 120 s each).
Verdict: **verified.** Experience rises in a fight, survivors keep it through a second fight and a game day, and the value can be written. Criterion C2 has a verified method.

## Facts
- `SMUnit.combatExperience` (float). Fresh spawned units have 0, whatever the `combatExperience` of the template row says (the row has 5.0; see `spike-S7.md`).
- It rises in fights. After a fight of 96 spear units against 24 sword units: mean 0.29 of the living units, the best unit 3.4. A unit that never met an enemy stays 0, so the mean is low.
- `SMUnit.UniqueID` is unique (625 units, no duplicate). The scenario tracks single units with it between reads.
- Dead units leave the unit list at once, so only survivors are compared.

## Scenario `veterancy` (COVERS C2)
3 player squads of `spearMilitia` (96 units) and one bandit squad of `militiaFoot` (maxSize written to 24 and restored, so the defenders survive: with 32 against 32 one side was wiped out in one development run and the scenario failed on "the same units are in both reads").
1. Fresh units: mean experience 0.
2. Fight 1 (speed 3 until one side is gone or 10 wall seconds without a casualty): both sides lose units; the mean experience of the player units is at least 0.1 and the best unit at least 1.0.
3. A new bandit squad, fight 2: at least 5 units appear in both reads (by unit id), none of them lost experience, and their mean did not fall.
4. The bandits that are left are removed (they would fight during the day), 1 game day at speed 3: at least 5 of the same units live and none lost experience.
5. `set_squad_experience(squad, 25)`: read back 25 on every unit, and still 25 after 10 game seconds.

Results (mean experience of the same units after fight 1 -> fight 2): run 1 0.54 -> 1.15, run 2 0.39 -> 0.94, run 3 0.61 -> 1.31. In a development run: 0.22 -> 0.91 on 78 common units.

## Traps
- A fight is a coin toss. 32 against 32 wiped out the defenders once. Use a clear size margin.
- The second fight must not run into the day check: units that still fight can die and look like "lost experience".
- The bridge JSON of the Lua encoder writes an empty map as `[]` (fixed in `runlib/battle.py`).

## Not verified
Experience across a save and load (no save function may be called), the effect of experience on strength (not measured), and decay over more than one day.
