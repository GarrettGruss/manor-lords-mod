# Combat and armor levers (spec 25, plan step 1, static)

Date: 2026-10-15. Game build: 0.8.111 (jmap `ManorLords-5.5.4-40574608+++UE5+Release-5.5-5e627997.jmap`).
Method: read only. No game run. The jmap, `DT_Items.vanilla.json` and the notes were read. No AES key was read.
Data source: `modtools/work/` in the main repo (not in this worktree; `modtools/` is not in git).

## Summary

- No single "damage multiplier" or "armor factor" setting exists in the jmap. No settings class has a combat multiplier.
- The combat path is in `SMUnit`. It has numeric fields for attack, defence, block, charge, armor pierce, morale and stamina. It has a function `SMUnit:CombatHit(attacker, defender, isProjectile, projDist, avoidKilling)`.
- Armor is item values (`def`, `block`) in `DT_Items`. Units get them from their equipment ids.
- Unit health is not a field. `Stat.maxHp` exists, but its owner is not clear. No unit health field was found on `SMUnit`.
- Unit rows (`DT_UnitTemplates`) are binary in the repo. No JSON export exists. The id arrays must be extracted before use (see L6).
- Nothing here is tested. Each lever needs an A/B test (plan step 2).

## Levers (ranked by promise)

| Rank | Lever | Source (object or field) | Type | Lua or pak | Evidence | Expected effect | Status |
|---|---|---|---|---|---|---|---|
| 1 | Hook `CombatHit`. Read or change `att`, `def`, `block`, `armorPierce` of attacker and defender before each hit | `/Script/ManorLords.SMUnit:CombatHit` (params `attacker`, `defender`, `isProjectile`, `projDist`, `avoidKilling`) | Run-time hook | Lua | Function and params in jmap. Field names `att, def, block, armorPierce, charge` on `SMUnit` (jmap) | Per hit: lower defender `def` or `block`, or raise attacker `att` or `armorPierce`. This is the only per-hit point found | Not tested. Risk: a hook only fires if the game calls it through `ProcessEvent` (C++ calls do not fire it). Needs a spike |
| 2 | Write live `def` and `block` of spawned units (armored or unarmored) | `SMUnit.def`, `SMUnit.block`, `SMUnit.baseDefence`, `SMUnit.baseBlock` (floats) | Run-time write, per unit | Lua | Fields exist (jmap). Spike S7 showed per-template values differ (`retinue_tier3` def 62, block 60). Lua writes work on other UObject fields | Unarmored unit gets lower `def`. Armored unit keeps its value. Simple A/B: same unit, `def` 0 against `def` normal | Not tested. Risk: `def` may be recomputed when equipment changes. The write may last only until the next update |
| 3 | Change armor values in `DT_Items`: `def` and `block` of body armor, helmets and shields | `DT_Items` rows 163, 164, 293, 294, 270, 271, 273, 276, 285, 288, 289, 290 (table below) | Data table | Lua (`HarnessDataTable` write) or pak | `def`/`block` are numeric fields of `Item` (jmap). A Lua write of `Value` worked and read back (`datatable-check.md`). Use of the value in combat is not verified | Armored units get more or less `def`. Good for the 1.5 to 2 times target (armored militia against bandits) | Not tested. Only units spawned after the write may change |
| 4 | Change `armorPierce` of weapons (raw damage against armor) | `DT_Items.armorPierce`: 178 weapons_polearms (2), 250 retinue_polearms (2), 138 Pickaxe (2). Spears 133 and sidearms 177 are 0 | Data table | Lua or pak | Field `armorPierce` exists on `Item` and `SMUnit` (jmap). Non-zero values exist in the table | Spears and sidearms hit through armor. Raises lethality for armored target | Not tested |
| 5 | Change `att` of weapons (raw damage) | `DT_Items.att`: 133 spears (1), 177 weapons_sidearms (2), 278 retinue_sidearms (3), 250 retinue_polearms (5), 178 weapons_polearms (2), 223 shortAxe (5), 20 fellingAxe (5) | Data table | Lua or pak | Field `att` on `Item` and `SMUnit` (jmap) | Raises damage of every unit with that weapon. Hits both armored and unarmored | Not tested. Too broad alone: it does not favour armor |
| 6 | Change equipment id arrays on unit rows (remove armor from bandits, give mail to militia) | `DT_UnitTemplates`: `armours`, `helmets`, `shields`, `weapons` (int arrays, jmap `UnitTemplate`) | Data table | Pak only (full table replacement) | Arrays exist (jmap). `RTSMultiEngineCPP:getDefaultMilitiaEquipmentForUnitTemplate` gives default militia equipment (jmap). LargerFormations pak replaces the whole table (`larger-formations.md`) | Changes who has armor. Does not change a unit's stats directly | Not tested. Needs the rows extracted (see below) |
| 7 | Change `charge` and `chargeStop` (charge damage) | `DT_Items.charge`: 138 Pickaxe (5), 178 weapons_polearms (2), 213 bludgeon_2h_maul (5), 250 retinue_polearms (5). `SMUnit.charge`, `chargeStop`, `inChargeDistance` | Data table or run-time | Lua or pak | Fields exist (jmap). Brigands `charge` 5 (spike C1) | Charge hits hurt more. Mostly one-time per fight | Not tested. Lower promise: charge is brief |
| 8 | Change morale or stamina (earlier rout or collapse) | `SMUnit.morale`, `SMUnit.stamina`, `SMUnit.defenseBroken` (bool), `Squad.pushStanceBeforeMoraleDrop`, `Squad.moraleDropChangedStance` | Run-time | Lua | Fields exist (jmap). No rout or flee function found with those names | Units may break sooner. This changes the outcome, not the damage per hit | Not tested. Lower promise: no direct rout rule found |
| 9 | AI aggressiveness | `GameSetupParameters.AI_aggressiveness` (byte) | Game setup | Lua (before start) or save-level | Field exists (jmap). Not about damage | Bandits may attack more. Not a lethality lever | Low promise. Test only if L1 to L4 fail |

Not levers (checked, no combat effect found):
- `UnitTemplate.maxSize`: sets the number of units per spawn (spike S7). Not damage.
- `UnitTemplate.combatExperience` and `SMUnit.combatExperience`: spike C2 says new units start at 0. Not damage.
- `RTSSettings`, `GlobalSettings`, `UnitSettings`, `RaidSettings`: no combat multiplier field found.
- `EGameDifficulty` enum exists. No settings field with that type was found in the owners checked.
- `MLCheatManager:Injury`: debug cheat, not a lever.

## Data table: armor and weapon values (DT_Items, 0.8.111 vanilla)

Source: `modtools/work/DT_Items.vanilla.json` (UAssetAPI export, 213 rows). Only rows with combat values are listed. Empty means 0.

| id | name | slot | att | def | block | range | rangedAtt | shootingRange | charge | armorPierce | Value |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 163 | gambesons | Body | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 5.0 |
| 164 | mail_armor | Body | 0 | 10 | 0 | 0 | 0 | 0 | 2 | 0 | 4.0 |
| 293 | armour_retinue_tier3_variations | Body | 0 | 60 | 60 | 0 | 0 | 0 | 0 | 0 | 8.0 |
| 276 | helmets_retinue_tier1 | Helmet | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 294 | helmets_retinue_tier3 | Helmet | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 273 | militia_helmets_resource | Helmet | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 3.0 |
| 285 | helmets_militia_tier0 | Helmet | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 288 | mercenary_helmet_poor | Helmet | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 289 | mercenary_helmet_medium | Helmet | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 270 | shields_small | Shield | 0 | 2 | 3 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| 271 | shields_large | Shield | 0 | 4 | 8 | 0 | 0 | 0 | 0 | 0 | 1.5 |
| 290 | shields_retinue_small | Shield | 0 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 2.5 |
| 133 | spears | Weapon | 1 | 0 | 0 | 120 | 0 | 0 | 0 | 0 | 1.0 |
| 177 | weapons_sidearms | Weapon | 2 | 0 | 0 | 65 | 0 | 0 | 0 | 0 | 3.0 |
| 178 | weapons_polearms | Weapon | 2 | 0 | 0 | 75 | 0 | 0 | 2 | 2 | 2.0 |
| 250 | retinue_polearms | Weapon | 5 | 0 | 0 | 75 | 0 | 0 | 5 | 2 | 0 |
| 278 | retinue_sidearms | Weapon | 3 | 0 | 0 | 65 | 0 | 0 | 0 | 0 | 3.6 |
| 277 | archer_sidearm | Weapon | 2 | 0 | 0 | 60 | 0 | 0 | 0 | 0 | 0 |
| 312 | banner_carrier_sword | Weapon | 2 | 0 | 0 | 65 | 0 | 0 | 0 | 0 | 3.6 |
| 223 | shortAxe | Weapon | 5 | 0 | 0 | 130 | 0 | 0 | 0 | 0 | 0 |
| 20 | fellingAxe | Weapon | 5 | 0 | 0 | 130 | 0 | 0 | 0 | 0 | 0 |
| 138 | Pickaxe | Weapon | 1 | 0 | 0 | 150 | 0 | 0 | 5 | 2 | 0 |
| 213 | bludgeon_2h_maul | Weapon | 1 | 0 | 0 | 50 | 0 | 0 | 5 | 0 | 0 |
| 274 | townguard_weapon | Body | 2 | 0 | 0 | 120 | 0 | 0 | 0 | 0 | 3.5 |
| 205 | warbows | Shield | 0 | 0 | 0 | 0 | 16 | 12750 | 0 | 0 | 1.0 |
| 206 | crossbows | Shield | 0 | 0 | 0 | 0 | 32 | 11500 | 0 | 0 | 2.5 |
| 21 | huntingBow | Shield | 50 | 0 | 0 | 0 | 0 | 3500 | 0 | 0 | 0 |

Notes:
- Row 164 `charge` = 2.0 is in the file, but it is odd for body armor. Check it before use.
- Body and helmet rows use the `def` column for armor. Shields use `def` and `block`.
- Unit-level values seen in spikes: `retinue_tier3` def 62, block 60; `militiaPole` def 4, range 75; `Brigands` charge 5; `brigandArchers` rangedAtt 16 (spike C1, spike S7). These are sums from equipment, so the exact formula is not known.
- `DT_Items` has 213 rows. Only 0.8.111 values were read. Pak mods (for example LargerFormations) may use older data.

## Unit rows (DT_UnitTemplates): not yet read

- No JSON export exists in `modtools/work/json/`. The file is in `modtools/work/ua-scan/ManorLords/Content/NotStronghold/Data/DT_UnitTemplates.uasset` and `.uexp` (binary, from an earlier scan).
- The `pakmod.py tojson` route refused this asset (`larger-formations.md`). The row layout is known from the jmap (`UnitTemplate`). A hand decode works (LargerFormations note).
- Rows to read: `militia`, `spearMilitia`, `militiaFoot`, `bowMilitia`, `militiaPole`, `crossbowMilitia`, `Brigands`, `brigandArchers`, `brigandPolearms`, `mercenary_*`, `retinue_tier1`, `retinue_tier3`.
- Fields to read: `armours`, `helmets`, `shields`, `weapons`, `mounts`, `bonus` (int arrays, item ids), `maxSize`, `cost`, `combatExperience`.
- Health: no field. Equipment gives the strength.

## Tests to run first (plan step 2)

1. L3 (`DT_Items` `def` and `block` of body armor and shields), by Lua write, then a pak only if the Lua write does not change combat. Test: armored militia (mail 164 and shields 271) against bandits, N at least 5 per side. Expected: armored side loses fewer units. Metric: `measureSquadPower` before the fight (read only), and loss rate as in spike C1.
2. L2 (live `def` of spawned units, per unit). Test: bandit squad with normal `def` against the same squad with `def` set to 0 after spawn. Expected: higher loss for the `def` 0 side. This tests the "2 to 3 times" idea without any file change. It also shows whether a live write holds during a fight.
3. L1 (`CombatHit` pre-hook). Spike first: register the hook on `SMUnit:CombatHit`, count calls in one fight, and check that the attacker and defender names come through. Only if calls fire, add the value change (for example defender `def` set before each hit). Do not change values in a hook until the call count is known.

Spike rules: no save calls (`requestSaveFile`, `SaveToDiskWithThumbnail`, `RequestMenuSave`, `Request Autosave`). Single-player only. Cap runs.

## Open questions

- Does `CombatHit` run through `ProcessEvent` (so a Lua hook fires)?
- Does a live write to `SMUnit.def` last through a fight, or is it reset by equipment updates?
- Does a changed `DT_Items.def` change units spawned after the write?
- What is the damage formula from `att`, `def`, `block`, `armorPierce`? Not found in the jmap. The function names are not enough; a spike or the binary is needed.
- Row 164 `charge` value.
