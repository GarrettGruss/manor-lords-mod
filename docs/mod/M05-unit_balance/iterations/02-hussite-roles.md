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
5. The list is shuffled-free and sorted by tier (melee low to high, then ranged) so that it is easy to read. It is stored in ModState as the key `composition` (templates joined with `-`; ModState strings allow only `A-Z a-z 0-9 _ . -`).
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
