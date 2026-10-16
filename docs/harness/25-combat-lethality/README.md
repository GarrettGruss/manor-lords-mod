# Spec 25: Combat lethality and armor levers (spike)

Status: A/B round done (2026-10-16): `CombatHit` hook dead, live `def`/`block` write proven, armor alone does not win, armor plus weapon (retinue unit) does. See `implementation-notes/ab-results.md`. Issue: #129. Branch: `feat/25-combat-lethality`.
Needed by: the Invasion Mod (M00 feasibility decision 5, "armor matters").

## Goal
Find every lever that can make unarmored combat more lethal and armored units much stronger. Measure each lever with an A/B test.
Design target (M00, a first guess): an unarmored unit takes 2 to 3 times the damage of the same unit with armor; an armored militia beats a bandit group 1.5 to 2 times its size in most runs.

## Known
- Unit rows (`DT_UnitTemplates`) hold equipment as item id arrays: `weapons`, `armours`, `shields`, `helmets` (spec 10 `spike-S7.md`). The item values are in `DT_Items`. They were not read.
- Lua can read and write number fields of `itemStats` rows (spec 09 `datatable-check.md`). It is not verified that game logic uses a changed value.
- Unit stat numbers such as `maxSize` can be changed (spec 10 criterion C3).
- Army A/B tests work (spec 10 `ab-statistics.md`, skill `harness-ab-testing`). Spear against sword was measured (p 0.029).
- The retinue armor upgrade exists in the game UI (spec 13 `adaptive-retinue-manager.md`).
- Do not read soft object fields or `RowStruct` through the bridge: it crashes the game.

## Levers to look for
1. Item values: armor, damage, defense or protection numbers in `DT_Items` or `itemStats` (Lua write or pak).
2. Unit values: health, attack, defense, morale or rout fields in the unit rows or on the unit classes (jmap).
3. Equipment: give or remove armor item ids on unit rows (pak), so raiders and militia differ.
4. Global combat values: damage multipliers in game settings, difficulty settings or config rows.
5. Run-time hooks: a reflected damage or hit function that Lua can post-hook to read the attacker and target (and maybe change a value).

## Plan
1. Static: search the jmap and the data tables for damage, armor, health, defense, hit and morale fields and functions. Read `DT_Items` armor rows with UAssetGUI (not the bridge). Write `implementation-notes/levers.md` with each candidate.
2. For each promising lever: a small change (Lua write or pak) and a 3 against 3 fight A/B with N runs per side (skill `harness-ab-testing`). Measure deaths, time to rout, winner.
3. Test the strongest lever on the design target: unarmored against armored militia of the same size, and armored militia against 1.5 times as many bandits.
4. Write the result table: lever, method, effect size, p value, risk. Recommend the levers for the mod.

## Acceptance criteria
- A1: `implementation-notes/levers.md` lists all candidates found, with evidence (jmap line, table and field).
- A2: At least 2 levers tested with an A/B (N at least 5 per side), with run ids.
- A3: A recommendation for the mod: which lever, Lua or pak, and the effect size reached, or a clear statement that no lever reaches the target.

## Non-goals
- No new animations, meshes or units.
- No balance tuning of the final mod. This spike only finds and measures levers.
