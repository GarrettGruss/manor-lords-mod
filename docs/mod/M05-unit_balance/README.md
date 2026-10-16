# M05: unit-balance

Feature folder: `unit_balance`. Batch 2.

## Goal
Make armor matter in battle. Give the Hussites roles from existing foot units. Add counters and veterancy.

## Player rules (from M00)
- The game has only foot soldiers. All factions fight on foot.
- Hussite units: sword men, pikemen and spearmen, crossbowmen, and early handgunners if the game has a fitting unit.
- Armor matters. Unarmored units take much more damage: villagers in militia, bandits and light raiders.
  - Target: an unarmored unit takes 2 to 3 times the damage of the same unit with armor.
  - Target: an armored militia group beats a bandit group 1.5 to 2 times its size in most runs.
  - Investment in armor (smiths, armor stock, liege requests) must pay off clearly.
- Counters: pavises and shields against crossbows and handguns. Pikes and a held line against sword men. Archers against light raiders.
- Veterancy: surviving units keep experience. Losing the best retinue hurts.

## Current state
Not started. The lever research is done (spec 25). The tuning tool is done on branch `feat/28-unit-tuning` (not merged).

## Proven building blocks
- Lever results: `docs/harness/25-combat-lethality/implementation-notes/ab-results.md`, `levers.md`.
  - The live write of `def` and `block` on units works and holds for a whole fight. Militia loss rate went from 0.33 to 0.61 with def 0 and block 0 (p 0.002).
  - Armor alone does not win the 1.5 times fight. Armor plus weapon (retinue unit: att 5, armorPierce 2, def 62, block 60) wins 5 of 5.
  - The `CombatHit` hook is dead. There is no per-hit lever from Lua.
  - A write to a `DT_Items` value changes units spawned after it.
- Live tuning tool and side detection by squad id: `docs/harness/28-unit-tuning/README.md` (on branch `feat/28-unit-tuning`; read it with `git show feat/28-unit-tuning:docs/harness/28-unit-tuning/README.md`), note `unit-owner.md` on the same branch.
- Counter test (spear against sword, p 0.029): `docs/harness/10-invasion-testability/implementation-notes/ab-statistics.md`, `spike-C1.md`.
- Typed squads and unit rows: `docs/harness/10-invasion-testability/implementation-notes/spike-S7.md`, `game-data-tables.md`.
- Veterancy and unit stat numbers (`maxSize`): spec 10 criteria in `docs/harness/10-invasion-testability/criteria.json`.
- Larger formations and retinue: `docs/harness/13-mod-inspection/implementation-notes/larger-formations.md`.
- A/B method: skill `harness-ab-testing`.
- Row ids: `docs/harness/23-row-id-range/README.md`. Proposed block: building ids 1500 to 1599, only if it adds buildings (rule in `feature-breakdown.md`).

## Tunables (M00)
- Damage ratio unarmored to armored (2 to 3 times).
- Armored militia against bandits (1.5 to 2 times its size).
- Per-role stat values for Hussite sword, pike, spear, crossbow rows.
- Veterancy gain per battle.

## Dependencies
- None for the rules. M03 and M04 use the result (raiders and bandits are the units that get the stats).
- Needs a Lua write on units that spawn later (spawn hook or poll, as in spec 28).

## Open questions
1. Which Lua rule applies the stat write to each new squad: a spawn hook or a poll (spec 28 uses a 2 s timer)?
2. Does a live write of `att` and `armorPierce` on militia reach the 1.5 times target? Not tested (spec 25).
3. Which existing foot rows stand in for sword men and handgunners? No handgunner row was found (M00 open question 13).
4. Does the pak route (`DT_UnitTemplates` equipment ids) give a stable item-level lever? Not tested.
5. Veterancy: which field holds the experience, and does it survive a save? Not stated in M00.
6. The loss rate stops at 1.0 when a group routs. How is the 2 to 3 times target measured? Use the loss rate ratio, or the raw damage ratio?

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | unarmored-lethality | Apply the live `def` and `block` write to unarmored units, for each new squad. | not started |
| 02 | hussite-roles | Hussite roles from existing foot rows. | not started |
| 03 | armored-militia | Armor plus weapon values so militia beat 1.5 times as many bandits. | not started |
| 04 | counters-veterancy | Counters and veterancy. | not started |
