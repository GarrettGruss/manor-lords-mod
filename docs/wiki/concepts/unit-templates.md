---
type: Concept
title: Unit templates of the game
description: The unit types of Manor Lords from the data table DT_UnitTemplates (militia, retinue, mercenaries, bandits), their row names and maximum squad sizes, which ones native raids use, and how mods read or add unit types.
tags: [units, data-table, DT_UnitTemplates, militia, retinue, mercenary, bandits, hussite]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-22T00:00:00Z }
sources:
  - resource: repo://mod/shared/HarnessDataTable/HarnessDataTable.lua
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/game-data-tables.md
  - resource: repo://openspec/specs/mod/raid_behavior/spec.md
---
# Unit templates of the game

The game keeps its unit types as rows of the data table `DT_UnitTemplates` (`/Game/NotStronghold/Data/DT_UnitTemplates`). Read on 2026-10-22 from the extracted table (`modtools/work/json/ManorLords/Content/NotStronghold/Data/DT_UnitTemplates.json`, not in git). The extract may be from an older game version.

## Unit types

The row name is the id that code and pak mods use. "Max size" is the field `maxSize`, the largest squad of that type.

**Militia** (raised from villagers):

| Row | Unit | Max size |
|---|---|---|
| `spearMilitia` | Spear militia | 32 |
| `militiaPole` | Polearm militia | 32 |
| `militiaFoot` | Foot militia | 32 |
| `bowMilitia` | Bow militia | 32 |
| `crossbowMilitia` | Crossbow militia | 32 |
| `militia` | Peasant Militia | 32 |

**Retinue** (the lord's own troops):

| Row | Unit | Max size |
|---|---|---|
| `retinue_tier1` | Retinue, tier 1 | 60 |
| `retinue_tier3` | Retinue, tier 3 | 60 |
| `reginaldsRetinue` | Retinue of the AI lord Reginald (tier 1 template) | 60 |

**Mercenaries** (hired companies):

| Row | Unit | Max size |
|---|---|---|
| `mercenary_spearmen` | Spearmen | 60 |
| `mercenary_infantry` | Infantry | 60 |
| `mercenary_archers` | Archers | 60 |
| `mercenary_heavy_archers` | Heavy archers | 60 |
| `mercenary_crossbowmen` | Crossbowmen | 60 |

**Bandits:**

| Row | Unit | Max size |
|---|---|---|
| `brigands` | Brigands | 60 |
| `brigandArchers` | Brigand archers | 60 |
| `brigandPolearms` | Brigand polearms | 60 |
| `basket` | Basketmen | 60 |
| `sherwoodBow` | Sherwood Bowmen | 60 |

Not real units: `wrong_unit_type`, `single` ("single guy for testing", max size 1), `militiaFoot_testing`, `spearMilitiaTesting`, `brigands_old`, `retinue_tier1_old`, and the rows named `--------------------------` (dividers).

The table also has a `cost` field (25 or 100 for most rows). Its meaning is not known.

## What this means for mods

- A native raid of the game uses only Brigands. The game has no Hussite unit. A Hussite raid of the Invasion Mod runs under the baron AI, so it can use the lord unit types (retinue, militia, mercenaries) and bring a mix of archers, spearmen and retinue (`mod/raid_behavior`, Purpose).
- `HarnessDataTable` reads and writes single number fields of `DT_UnitTemplates` rows at run time (memory only). Do not read a whole row struct: it crashes the game.
- A pak mod can add new rows to `DT_UnitTemplates` (proven in spec 29), so the mod can add unit types of its own. See [Pak mods](../workflows/pak-mods.md).
