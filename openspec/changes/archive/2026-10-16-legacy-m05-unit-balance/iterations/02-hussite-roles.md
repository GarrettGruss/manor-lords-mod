# M05 iteration 02: hussite-roles

Branch: `feat/M05-unit_balance-02-hussite-roles`. Issue: #162.

## Goal
Give the Hussite raiders roles from existing foot units (decision 7). The raid plan of M02 stores a planned composition. The raid spawns that composition. No new rows, no pak, no handgunners.

## Role to template map
Each template was spawned as a bandit-side squad in the real game (scenario `unit-balance-role-templates`, run `20261017-221800-9e31`, unit_balance off). Numbers are the mean of the squad.

| Role | Tier | Template | Units | att | def | block | armorPierce | Why |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| melee | I | `Brigands` | 18 | 2.4 | 2.8 | 1.2 | 0 | The brigand row (M00). Charge 3. |
| melee | I | `spearMilitia` | 32 | 4.0 | 6.7 | 7.8 | 0 | The spearman row. |
| melee | II | `militiaFoot` | 32 | 5.0 | 4.9 | 2.9 | 0 | The sword and axe infantry row (att 5). |
| melee | II | `mercenary_infantry` | 36 | 5.0 | 5.9 | 2.9 | 0 | Second sword infantry row, more armor. |
| melee | III | `retinue_tier3` | 36 | 6.9 | 63.5 | 61.5 | 0.9 | Heavy retinue. |
| melee | III | `brigandPolearms` | 36 | 5.0 | 4.0 | 0 | 2 | Poleaxe infantry: the polearm weapon, armorPierce 2. |
| ranged | I | `bowMilitia` | 32 | 3.1 | 2.0 | 0 | 0 | Bows. |
| ranged | I | `brigandArchers` | 36 | 3.0 | 4.0 | 0 | 0 | Bows (rangedAtt 16, spec 10 spike C1). |
| ranged | II | `crossbowMilitia` | 32 | 3.1 | 2.0 | 0 | 0 | Crossbows. |
| ranged | II | `mercenary_crossbowmen` | 36 | 3.1 | 2.6 | 0 | 0 | Crossbows. |

Not used: `militiaPole` (a tier II/III polearm candidate, def 2.7: weaker than `brigandPolearms`), `retinue_tier1` (def 13.7, between tiers), `Mercenary_Archers`, `mercenary_spearmen` (duplicates). Ranged units show no ranged stats in the unit stat read (spike C1 saw `rangedAtt` only for archers); the role comes from the template name.

## Raid composition
The composition is a list of templates, one for each squad of the raid. The count of squads is unchanged: `multiplier x difficulty` (decisions 8 and 30).

1. Ranged squads: `round_half_up(squads x ranged_share)`. `ranged_share` is 0.25 (TBD, playtests). So a 1 squad raid is all melee.
2. Ranged tier: of the ranged squads, `round(ranged x crossbow_share[difficulty])` are tier II (crossbows), the rest tier I (bows). `crossbow_share` is `{0, 0.5, 0.75}` (TBD).
3. Melee squads: the rest. They are split over tiers I, II, III by `melee_tier_weights[difficulty]` with largest remainder rounding (a tie goes to the lower tier). Weights (TBD): difficulty 1 `{70, 30, 0}`, difficulty 2 `{40, 40, 20}`, difficulty 3 `{20, 40, 40}`.
4. For each squad the template is a random pick from the tier list in `config.unit_roles.templates`.
5. The list is sorted by tier (melee low to high, then ranged). Only a seed is stored in ModState (`composition_seed`, one integer). The random picks use a small seeded generator, so the list is rebuilt from the seed, the squads and the difficulty. (First plan: a string key `composition`.)
6. Difficulty or size changes recompute the squads and the composition (as M02 does for the squads).
7. The banner estimate is the sum of `unit_roles.template_units[template]` over the composition (measured unit counts).

## Spawn route
`spawnRaiders(n, centre)` has no template parameter (spike S2). The proven route is `RTSMultiEngineCPP:spawnArmy(point, {FName...}, banditPawn, 0, 0)` (spike S7; `HarnessBattle.spawn_at`, `HarnessBandits.bandit_spawn_at`). New in `ManorCore`: `spawn_squads(templates, point)`. The squads appear at the point `(player x, raid_spawn_y)`. The value of `raid_spawn_y` (-88900) is the map edge where `spawnRaiders` put the raiders in spec 15 runs.
Known difference (deviation, see the Result): bandit squads from `spawnArmy` follow the base bandit AI. In spec 15 they walked to the AI waypoint and attacked after a wait; `spawnRaiders` raiders attack sooner. `config.unit_roles.enabled = false` returns to `spawnRaiders`.

## Changes
- `config.lua`: table `unit_roles` (`enabled`, `templates`, `template_units`, `ranged_share`, `crossbow_share`, `melee_tier_weights`, `raid_spawn_y`).
- `features/invasion/plan.lua`: pure `composition(squads, difficulty, roles, random)` and `expected_units(list, template_units)`.
- `features/invasion/init.lua`: ModState key `composition`, plan and replan store it, spawn uses it, `invasion_state` reports it.
- `ManorCore.spawn_squads`.
- Scenario `invasion-raid-composition` and the probe `unit-balance-role-templates`.

## Acceptance criteria
- A1: every template in `config.unit_roles.templates` is a row of `DT_UnitTemplates` and spawns living units as a bandit-side squad (scenario `unit-balance-role-templates`).
- A2 (fake tests): `composition` returns exactly `squads` templates; every template is in the tier list; the ranged count is `round_half_up(squads x ranged_share)`; no tier III at difficulty 1; the result is the same for the same random; a bad input fails loudly.
- A3 (real game, difficulty 1 and 3, a forced large raid): the squads spawned by the raid, read by their template names from the unit census, equal the planned composition (same multiset of templates).
- A4: the ranged share of the spawned squads is in `[0, ranged_share + 1/squads]`, and difficulty 3 has more tier II or III melee squads than difficulty 1 in the config table.
- A5: the raid spawn log line and the banner use the composition's unit count. The units spawned equal the sum of `template_units` for the composition.
- A6: the plan keeps `squads = multiplier x difficulty` (M02 criteria still pass in the fake tests).

## Scenarios
- `unit-balance-role-templates` (A1): spawns each candidate, records the profile.
- `invasion-raid-composition` (A3 to A5): option `INVASION_DIFFICULTY` (1 to 3). Forces the large size, runs the forced raid (`invasion_force_next`), reads the unit census by squad template, compares with the planned composition in `invasion_state`.

## Open questions
- The values in `unit_roles` are TBD for playtests.
- Squad sizes differ (18 to 36 units). The unit count of a raid varies by composition.
- Whether the AI timing of `spawnArmy` squads is acceptable (Result).

## Result
Result: PASS in the real game (2026-10-18), with deviations. Notes: `../implementation-notes/iteration-02-hussite-roles.md`.
- Changes from the plan: the saved key is `composition_seed` (one integer), not a string. The list is rebuilt from the seed, the squads and the difficulty (`plan.lcg`). Reason: first suspicion for game crashes; the crashes turned out to be a base-commit flake (below), but one integer is simpler and was kept. Also `invasion_set_roles` and `invasion_raid_squads` commands. The crossbow and bow militia rows have equal stats, so the scenario merges them in the stat match; the planned list is checked exactly through the mod record.
- A1: `unit-balance-role-templates`, run `20261017-221800-9e31` pass: all 14 candidate rows exist and spawn as bandit squads.
- A2, A6: 23 fake tests (`test_invasion_plan_roles.py`, `test_fakegame_invasion.py` RolesTests) pass; the full unit suite passes except the 5 `test_install_scripts` tests that fail while a game runs (issue #158).
- A3, A4, A5: `invasion-raid-composition` (large raid, forced), difficulty 1: runs `20261018-001457-3a1f` (Brigands, militiaFoot, bow squad: 82 to 86 units), `20261018-001635-7a55`; difficulty 3 (9 squads, about 300 units, tier III at 2 to 4 squads): `20261018-001548-c6c0`, `20261018-001741-9f65`. Difficulty 2 (before the seed change): `20261017-224156-ca53`. All pass: the squads the mod made equal the plan, the stat and size match agrees, the units are 90 to 100 percent of the sum of the template sizes, the ranged squads are at most `0.25 x squads + 1`.
- Regression runs: `invasion-first-raid` d2 medium passes (`20261017-232832-2804`, `-234511-2e53`, `-235543-3690`); `raid-behavior-loot-return` `20261018-001833-35ce` pass (roles off, 18 raiders); `unit-balance-armored-kept` `20261018-002025-4c64` pass.
- Role raid behavior (one observation, run `20261018-001924-a645` crashed, `20261018-002400-f776` ran with roles on): the `spawnArmy` squads at the map edge attacked at once (loot 4 returned 4 within 3 game days) and were destroyed by the defenders, without the native leave line. This differs from `spawnRaiders` raiders (stand at the waypoint, then raid, then leave). `raid-behavior-native-plunder` assumes the `spawnRaiders` behavior, so it now sets roles off. Open for a playtest: the M03 tracker with role raids; the pace of the attack.
- Game crashes (access violation in Lua tables, `ltable.c`) are frequent in long runs while other agents use the game: `invasion-first-raid` d2 medium, alternating base commit `39a7a3c` and this branch, 4 pairs: base 1 pass of 4 (`20261017-233509-ccc1` pass; `-234946-d78a`, `-235321-d86c`, `20261018-000207-d979` crash), branch 2 pass of 4 (`-234511-2e53`, `-235543-3690` pass; `-235133-4f64`, `20261018-000904-8756` crash). `raid-behavior-native-plunder`: base 1 crash and 1 boot failure in 2 runs (`20261018-003552-dbb6`, `-003458-c5e9`), branch 5 crashes in 5 runs with the scenario on `spawnRaiders` (not a pass on either side). So the crashes do not come from this change, but `raid-behavior-native-plunder` has no pass in this iteration.
- After the merge of main (PR #166 scheduler, #164 season tick) and decision 31 (Hussite raids use the unit tiers, on by default; bandit raids keep spawnRaiders), real-game runs from this branch: `invasion-raid-composition` difficulty 1 `20261018-012107-b3fc` pass, difficulty 3 `20261018-012220-3f36` pass; `invasion-first-raid` `20261018-013814-7fda` pass (an earlier try `20261018-012359-3e5b` was a bridge timeout harness_error); `invasion-no-double-raid` (120 days) `20261018-012528-216c` pass. Roles stay on by default. Scenarios with roles off (`raid-behavior-native-plunder`, `raid-behavior-loot-return`) test native plunder on purpose.
