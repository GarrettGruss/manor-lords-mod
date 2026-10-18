# Iteration 02: hussite-roles (notes)

## Design
- Pure rules in `mod/InvasionMod/Scripts/features/invasion/plan.lua`: `role_counts`, `composition`, `apportion` (largest remainder), `join`, `split`, `expected_units`. Config in `config.lua`, table `invasion.roles` (a top-level key must be a feature name, so the table is nested in `invasion`).
- ModState key `composition_seed` (one integer) is stored with the plan. The list is rebuilt from the seed with a seeded generator (`plan.lcg`), so a size or difficulty change gives a new list with the same random picks. A plan saved before this iteration has seed 0; a seed is made on first use. The first design stored a string key; it was replaced while looking for the cause of game crashes (the crashes were a flake of the base commit too).
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
- AI behavior: `spawnArmy` squads at the map edge are bandit-side squads. In one real run (`20261018-002400-f776`, native-plunder with roles on) they attacked within 3 game days, looted 4 goods (returned 4 by M03) and were destroyed by the defenders. They gave no native leave line, and the M03 scenario assertions A1 and A5 failed (they assume `spawnRaiders` raiders). The pace of the attack and the M03 tracker with role raids need a playtest. `raid-behavior-native-plunder` sets roles off.
- `raid_spawn_y = -88900` is a measured constant for this map (spec 15). Other maps need another value.
- The unit count of a raid is no longer `18 x squads`. A large raid at difficulty 3 is about 300 units. M00 decision 16 says 15 squads for a large army; the squad count rule was kept unchanged (decisions 8, 30).
- Existing scenarios that counted 18 units per squad (`invasion-first-raid`, `invasion-no-double-raid`, `raid-behavior-native-plunder`) now use the `raiders` value of `invasion_state`. `raid-behavior-loot-return` switches roles off (it kills exactly 18 raiders).

## Crashes
- Several game crashes with access violations in Lua tables (`ltable.c`: `luaH_getint`, `luaH_next`, `mainpositionTV`) happened in `invasion-raid-composition` after the raid spawn, in `invasion-first-raid` during the countdown, and once during boot. M03 saw the same signature with its tracker (`iteration-01-native-plunder.md`, "Crash finding"). The A/B against the base commit (4 pairs of `invasion-first-raid`) shows the flake exists without this change: see the Result in the iteration file.

## Runs
See the Result of `../iterations/02-hussite-roles.md`.
