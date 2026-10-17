# Iteration 02: hussite-roles (notes)

## Design
- Pure rules in `mod/InvasionMod/Scripts/features/invasion/plan.lua`: `role_counts`, `composition`, `apportion` (largest remainder), `join`, `split`, `expected_units`. Config in `config.lua`, table `invasion.roles` (a top-level key must be a feature name, so the table is nested in `invasion`).
- ModState key `composition` (templates joined with `-`) is stored with the plan. A size or difficulty change recomputes it (`replan_size`). A plan saved before this iteration has `none`; the spawn then composes it.
- Spawn: `ManorCore.spawn_squads(templates, point)` calls `spawnArmy` with the bandit pawn as owner (one squad for each name). The point is `(player x, raid_spawn_y)`. `spawnRaiders` has no template argument (spike S2), so this is the closest proven route (`HarnessBattle.spawn_at`, `HarnessBandits.bandit_spawn_at`).
- The banner estimate and the `raiders` value of `invasion_state` are the sum of `template_units` (measured sizes 18 to 36), not `18 x squads`.
- New commands: `invasion_set_roles enabled` (session switch; off uses `spawnRaiders`) and `invasion_raid_squads` (the squads of the last roles raid with alive units and mean `att`, `def`, `armorPierce`; reads only units of those squads).
- HarnessActions is unchanged (VERSION stays 55).

## Findings
- Template probe (`unit-balance-role-templates`, run `20261017-221800-9e31`): all 14 candidates exist and spawn as bandit-side squads. Unit counts 18 (`Brigands`), 32 (militia rows), 36 (retinue, mercenary, brigand polearms and archers). Profiles are in the iteration file.
- `bowMilitia` and `crossbowMilitia` have identical stat means (att 3.06, def 2). The scenario cannot tell them apart by stats and merges them into one label. The planned template list is still checked exactly (the mod's own record).
- Mean stats of a squad vary by a few tenths between spawns (random gear). The scenario picks the template by unit count first, then by nearest profile.
- `spawnArmy` returns the squad ids in name order. The mod records them for the report command.

## Deviations
- AI behavior: `spawnArmy` bandit squads follow the base bandit AI (spec 15: they walk to the AI waypoint, wait, then raid), not the `spawnRaiders` raid path. Not verified for the map-edge spawn point; the scenario checks the composition only. Open for a playtest: time until the first burning, and whether M03 loot tracking holds (the tracker found all units by census in `raid-behavior-native-plunder` fake tests; real run not repeated).
- `raid_spawn_y = -88900` is a measured constant for this map (spec 15). Other maps need another value.
- The unit count of a raid is no longer `18 x squads`. A large raid at difficulty 3 is about 300 units. M00 decision 16 says 15 squads for a large army; the squad count rule was kept unchanged (decisions 8, 30).
- Existing scenarios that counted 18 units per squad (`invasion-first-raid`, `invasion-no-double-raid`, `raid-behavior-native-plunder`) now use the `raiders` value of `invasion_state`. `raid-behavior-loot-return` switches roles off (it kills exactly 18 raiders).

## Crashes
- Several game crashes with access violations in Lua tables (`ltable.c`: `luaH_getint`, `luaH_next`, `mainpositionTV`) happened in `invasion-raid-composition` after the raid spawn, in `invasion-first-raid` during the countdown, and once during boot. M03 saw the same signature with its tracker (`iteration-01-native-plunder.md`, "Crash finding"). See the Result in the iteration file for the comparison with the base commit.

## Runs
See the Result of `../iterations/02-hussite-roles.md`.
