# Spike C1: counters (casualties by unit type)

Date: 2026-10-10. Branch `feat/28-unit-data-combat`. Real game, base fixture. Runs: `s7-explore2` (probes), `s7-c1`, series of `counters-ab` (3 of 3: `20261011-023859-3f1d`, `-024157-4fe2`, `-024453-4f7c`, about 175 s each), suite `counters-ab` (run `20261011-024748-7fe6`, 8 runs, 1296 s).
Verdict: **method verified, with one limit: the base game has no horse unit.** Typed squads fight in a controlled way, casualties are counted by side and template, and an N-run A/B reports the difference with statistics.

## What is possible (answer to the S2 limit)
Spike S2 could not choose a unit type for raiders. `spawnArmy(position, {template names}, ownerPawn, 0, 0)` can (see `spike-S7.md`): the owner pawn gives the side, the template gives the type.
Two squads that spawn 2500 units apart walk to each other and fight without any order (player squads included). A fight takes 25 to 45 wall seconds at speed 3 (180 to 365 game seconds). It ends when one side is gone or when the survivors stop (one side breaks: for example 12 against 21 left, no more deaths for 10 wall seconds).
Dead units leave the unit list, so casualties = start size - living units, per squad id (registry in `HarnessBattle`). `unitTemp` still reads None, which is why the registry exists.
Per-unit stats differ by template (`att`, `def`, `block`, `charge`, `range`, `rangedAtt`): `retinue_tier3` def 62 and block 60 (heavy), `Brigands` charge 5, `brigandArchers` rangedAtt 16, `militiaPole` def 4 and range 75. `bowMilitia` and `crossbowMilitia` show no ranged stats at spawn (equipment may load later); they fought in melee in the probes.

## Horse: not possible with the base game
No template in `DT_UnitTemplates` has a mount (`mounts` empty in all current rows). So "spearmen against horse archers" cannot be built from the base data. The method covers the templates that exist: spear (`spearMilitia`), sword (`militiaFoot`), polearm (`militiaPole`), bow, heavy retinue (`retinue_tier3`), `Brigands` and the mercenary rows. The mod adds its own horse rows (pak, spec 09); the same scenario then takes the template names from `COUNTERS_PLAYER` and `COUNTERS_BANDIT`.

## Scenario `counters-ab` (COVERS C1) and suite
One run: 3 rounds; each round clears the old squads, spawns one player squad and one bandit squad of the chosen templates (`--env COUNTERS_PLAYER=`, `COUNTERS_BANDIT=`, `COUNTERS_ROUNDS=`, read with `ctx.variant_option`), runs the fight, and checks: both squads have at least 10 units, at least 3 casualties in total, the fight ended. Metrics: `player_loss_rate`, `bandit_loss_rate`, `loss_ratio` (bandit casualties / player casualties), `player_casualties`, `bandit_casualties`, `fight_wall_s`.
Default (spear against sword), 3 real runs, mean of 3 rounds: player loss rate 0.72, 1.00, 0.66; bandit loss rate 0.45, 0.40, 0.35. The bandit side wins most fights (it attacks, the player squad waits).

## Real A/B (suite `counters-ab`, 4 runs a variant, 3 rounds a run)
| Variant (player squad against a sword bandit squad) | player loss rate (median) | player casualties | loss ratio |
|---|---|---|---|
| spear (`spearMilitia`, 32 units) | 0.72 | 23.0 | 0.54 |
| heavy (`retinue_tier3`, 36 units) | 0.15 | 5.3 | 5.04 |
Verdict `different` (effect size -5.6, p 0.029, ranges do not overlap). The expectation "player_loss_rate lower by at least 0.3" was MET. So a unit type changes the casualty ratio by a large, measurable amount, and the harness reports it with a pass or fail rule. A real "spearmen counter horse" range needs horse rows.
Single fights are noisy (spear against sword: 15 and 2 casualties on the two sides in one probe, 17 against 2 the other way in another), so one run says little; use N runs.

## Not verified
Horse units, ranged against melee (bow stats do not show at spawn), shield wall formation, orders (steering a squad is still not possible), terrain, and fights with more than two squads. The 3 of 3 series runs used the default variant; the suite covers the other variant.
