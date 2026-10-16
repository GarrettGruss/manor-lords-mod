# Battlefield Loot And Bandit Loot (UnifiedLoot v1.2.0, Nexus 390)

Source: `Downloads\Battlefield Loot And Bandit Loot 0.8.104 390 1 2026-09-24T15-44Z sZ2otzdbD\UnifiedLoot\`.
Target: Manor Lords 0.8.104 (`config.lua:3`). Pure Lua. No DLL. Nothing was run.

## What it does for the player
- Ctrl+Alt+L: after a battle, takes the weapons, shields, helmets and armor of dead enemy soldiers and puts them in the player's storehouse as trade goods.
- Ctrl+Alt+K: the same for dead soldiers of the player's own army.
- Bandit camp spoils: when the player clears a camp and picks a reward, the mod adds seasonal goods to storage and can scale the money reward (`README_EN.txt`, `config.lua:10,14`).
- The Chinese texts (`README_CN.txt`, `MONEY_CONFIG_CN.txt`, `PERFORMANCE_TEST_CN.txt`, the install note) say the same. The install note tells the user to disable an older mod, `FriendlyEquipmentRecovery`.

## How: the loot method (the answer for criterion R3)
The mod does NOT put loot on the ground. It never spawns a pickup. It moves equipment from a dead unit into a building inventory.

Reads (all in `Scripts/main.lua`):
- Units: `FindAllOf("SMUnit")` and `FindAllOf("VAMP_DefaultUnit_C")` (`main.lua:1385`). Properties `dead`, `assignedSquadID`, `closestEnemy` (`main.lua:1445-1458`).
- Corpse gear: `unit:getEquippedID(slot)` for slots 0 to 3 = body armor, weapon, shield, helmet (`main.lua:1058-1060`, `1164`). Fallback: array `equipmentOnRally` (`main.lua:1184`). `getCurrentEquipmentVariation(slot)` gives text such as "crossbow" to choose a good (`main.lua:1091-1145`).
- Player army: `PawnCPP:getAllCommandedSquads()`; per squad `ID`, `isEngaged`, `enemySpotted`, `engagementPercentage`, `unitArr`, `assignedRecruits`, `equippedRecruits` (`main.lua:287`, `368`). The base game clears `assignedSquadID` on corpses (`main.lua:355`), so the mod remembers unit objects while they are alive (snapshots).
- Player: `RTSMultiEngineCPP:getPawnBySetupIndex(i)` with `isMainPlayer` (`main.lua:242-251`); the comment says `FindFirstOf(MyPawnCPP_BP3_C)` can return the wrong pawn.

Writes:
- Item table `RAW_EQUIPMENT_TO_GOOD` maps raw ids to trade-good ids: 133 spear, 163 gambeson, 164 mail, 177 sidearms, 178 polearms, 205 warbow, 206 crossbow, 270 small shield, 271 large shield, 273 helmet, 293 plate armor (`main.lua:1065-1082`). Food ids are 28, 30, 141, 147, 171, 172, 220, 230, 296, 320 (`main.lua:704`).
- Storage: finds a storehouse or granary by `SMBuildingMaster.Data.bType` = 99 (large store), 72 (small store), 68 (large granary), 80 (small granary), or by name (`main.lua:519-536`). It scans `FindAllOf("SMBuildingMaster")` because `region.buildings` is empty on 0.8.104 (`main.lua:619-625`).
- Deposit: `building.addToInventory({Type=id, amt=n})`, then `updateResources`, `region.updateStorage`, and a log line with `pawn:addLog(FName("UnifiedLoot"), "... <img id=\"ItemID_N\"></> ...")` (`main.lua:709-761`).
- Corpse visual: `unit:unequip(slot)` for slots 1 to 3. Slot 0 is kept on purpose: removing it leaves a head-only corpse, and the older native mod's `Equip(311, ...)` call crashes the game (`main.lua:1212-1252`).
- Dedupe: table `lootedCorpses` by object name. One scan per hotkey. No permanent poll (`CHANGELOG.txt:11-12`).

Bandit camp path:
- Hooks the two choice buttons of `/Game/UI/Elements/MessageFullscreen.MessageFullscreen_C` (`BndEvt__Button_ChoiceA...` and `...ChoiceB...` delegate signatures; `main.lua:978-1010`). It loads the asset first with `LoadAsset`.
- A quest is a camp reward when `Quest.descr == "spoils_of_war_descr"` (`main.lua:830`). It reads `Quest.regions[1]` and `Quest.rewards[*].regionalWealth`.
- Choice A (town): adds the goods table `seasonalCampGoods(month)` (`main.lua:771-816`) to storage and writes `Region.regionalWealth` directly. Choice B (treasury): writes `Pawn.silver` directly (`main.lua:943-976`).
- Month comes from `WeatherMaster.month`.

Triggers: `RegisterKeyBind` (Ctrl+Alt+L, Ctrl+Alt+K), `RegisterHook` on `PawnCPP:playCinematicSequence` (load: snapshots at 15, 30, 60 s), `RegisterHook` on a recruit button event (`addSquadCard...unitButton...OnButtonReleasedEvent`, snapshot after 2.5 s), `LoopAsync` only to wait until the UI classes load.

## Version and signs of staleness
Checked against the 0.8.111 jmap.

| Name used | Result |
|---|---|
| `SMUnit.dead`, `assignedSquadID` (struct `SquadHandle`), `equipmentOnRally` | yes |
| `SMUnit:GetEquippedID(Slot: EEquipmentSlot)` | yes (capital G; Lua call `getEquippedID` is likely fine, UE names ignore case) |
| `SMUnit:unequip(Slot)`, `getCurrentEquipmentVariation`, `changeEquipmentVariation` | yes |
| `SMUnit.closestEnemy` | no. Renamed `ClosestEnemyUnit` |
| `SMBuildingMaster:addToInventory(Good)`, struct `Good{Type, amt, belongsTo, belongsToUnit}` | yes. Same fields as the mod's table |
| `SMBuildingMaster.Data.bType` (`BuildingDataStruct`) | yes |
| `SMBuildingMaster:updateResources`, `Region:updateStorage`, `Region.updateStatUI` | no. The mod wraps them in `pcall`, so a miss is silent |
| `Region.buildings` | no. Function `Region:GetBuildings()` exists |
| `Squad.ID/isEngaged/enemySpotted/engagementPercentage/unitArr/assignedRecruits/equippedRecruits` | yes |
| `PawnCPP:getAllCommandedSquads/getSquadByID/getAllCommandedRegions/addLog/playEventMessage/playCinematicSequence/updateStatUI`, `silver` | yes |
| `Quest.descr/regions/rewards`, `Reward.regionalWealth`, `Region.regionalWealth` | yes |
| `MessageFullscreen_C` ChoiceA and ChoiceB `BndEvt__` functions | yes (same long names) |
| `/Game/UI/HUD/addSquadCard.addSquadCard_C` | no object with that name. The recruit hook may never register |
| class `WeatherMaster` (month) | no; see `refugees-expanded.md`. Camp goods fall back to month 6 |

The mod is mostly current. The likely failures: calendar read, `closestEnemy`, the recruit hook.

## Risk review
- Pure Lua, about 70 KB. No DLL, no network, no process or shell call. Files: it only prints to the UE4SS log. It reads its own `config.lua` with `require("config")` (shared module name, which can clash with other mods; Refugees avoids this).
- Writes live game state: building inventories, `Region.regionalWealth`, `Pawn.silver`, unit equipment. No save function is called (checked by reading: no `SaveGame`, `requestSaveFile` or `Autosave`).
- `unit.unequip` on corpses is called only in slots 1 to 3. The author found a crash with another call sequence and avoided it (`main.lua:1212-1221`).
- License: none given. No author named.

## Lessons for us
R3 (loot on the ground): no method. The mod gives a good stand-in model: the item flow "dead unit -> trade good -> storehouse inventory". Base game still has no ground loot.
- Useful for our R3 stand-in: the ledger can read the same fields. `SMUnit.ItemsLooted` (IntProperty, offset 3284) exists in the jmap and this mod does not touch it, so we cannot learn its meaning from here. Spike S3 owns that question.
- A real inventory deposit is easy: `SMBuildingMaster:addToInventory({Type=<good id>, amt=<n>})`. This gives a measurable result without ground items. The harness can read it back with `getInventory(false)`. Loot goods ids in the table (163, 164, 177, 205, 206, 270, 271, 273, 293) are the equipment trade goods.
- Slot mapping `getEquippedID(0..3)` = armor, weapon, shield, helmet gives the equipment of a dead unit. This is useful to assert what an enemy dropped.
- Spoils of war: quest id text `spoils_of_war_descr` and the ChoiceA/ChoiceB button hooks are a way to test the bandit camp reward flow, and a hint for how a raid reward could be shown.
- Danger found by the author: `Equip(311, true, false)` on a dead body crashes the game. Do not call it in probes.

Test idea:
1. Fixture with a storehouse and a finished battle with corpses (spike).
2. Call `addToInventory` with one good (type 177, amt 1) through the bridge on the game thread, then read `getInventory`. Assert +1 in range.
3. For R3, read `getEquippedID(0..3)` on a dead enemy before and after the army pass, then compare with the storehouse delta.
