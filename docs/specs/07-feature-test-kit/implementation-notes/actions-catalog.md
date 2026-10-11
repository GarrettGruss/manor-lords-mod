# Actions catalog (spec 07)

Date: 2026-10-10. Source: probe runs in the real game with `harness/scenarios/probe_actions.py` (hidden scenario, group chosen with `HARNESS_PROBE`),
then scenario runs. Every number below was read back from the game. Run ids are in `runs/` (not in git): `probe-money`, `probe-time`,
`probe-region`, `probe-cheat`, `probe-cheat2`, `probe-cheat3`, `probe-names`, `probe-weather`, `probe-hud2`, `probe-helper3`.

Status words: `verified` = the effect was read back in the real game. `partial` = it works with a limit. `not possible` = see the reason.
"In actions.py" says if `harness/runlib/actions.py` has the action (`ctx.actions.<name>`).

## Summary

| Action | Status | In actions.py | Call |
|---|---|---|---|
| add silver | verified | `add_silver(n)` | `PawnCPP:changeSilver(n)` |
| set silver | verified | `set_silver(n)` | `set silver` |
| add / set influence | verified | `add_influence`, `set_influence` | `PawnCPP:changeInfluence(float)`, `set influence` |
| add king's favour | verified | `add_kings_favour(n)` | `PawnCPP:changeKingsFavour(n)` |
| set day / set season | verified | `set_day(n)`, `set_season(name)` | `RTSMultiEngineCPP:setDay(n)` |
| set region value (Approval, publicOrder, regionalWealth) | partial: the read-back is immediate, the game may recalculate it later | `set_region_value` | `set <property>` on the Region |
| set supplies_food | partial: recalculated at the next day tick | `set_region_value` | `set supplies_food` |
| add regional wealth | verified | `add_regional_wealth(n)` | `Region:addRegionalWealth(n)` |
| give item (goods in the stock) | verified | `give_item(id or name, n)` | `MLCheatManager:GiveItemByID` |
| set settlement level | verified for level 1 | `set_settlement_level(n)` | `MLCheatManager:SetSettlementLevel` |
| set weather values | partial: the game moves them back in seconds | `set_weather(name, v)` | `set raining` and others on the TemporalComponent |
| start rain (`RainNow`) | partial: rain rises slowly (0.04 after 3 s, 0.11 after 13 s) | no | `MLCheatManager:RainNow` |
| spawn a bandit squad | verified (+18 units) | `spawn_bandit_squad()` | `MLCheatManager:SpawnBanditSquad` |
| place a building (real OS mouse) | verified (HitchingPost, 10 of 10 runs with the good point; uses the OS mouse and focus) | `place_building(type_id, fx, fy)` | `activateBuildingMode`, real click (`osinput.py`) |
| send a letter | verified, only with the helper mod `HarnessActions` | `send_letter(paragraphs, sender)` | command channel, then `PawnCPP:sendLetter` |
| close pop-ups ("Hunger!" and similar) | verified (3 real pop-ups at 8x; the clock resumes at the old speed). Needs the mod `HarnessActions` version 6 | `close_popups()`, `popup_state()`, `ctx.popups()` | command `close_popups`: press the Accept handler of `popupMessageWidget_C` (spec 10, S8) |
| read InBox / outbox | verified (read only) | `ctx.bridge.read_property` | `get InBox` |
| read the HUD silver number | verified | `ctx.bridge.hud_treasury_text()` | `TreasuryNumeric:GetText()` |
| save state to a new fixture | **not possible** | `save_state` raises | `PawnCPP:requestSaveFile` |
| show a message (`playEventMessage`) | see the row "show a banner text" below (the first try crashed: a plain string was given for a `Name`) | `show_message` | |
| read item data (`getItem`) | **not possible** (crash) | `get_item_info` raises | |
| remove all families | not possible (no effect seen) | `remove_all_families` raises | `MLCheatManager:RemoveAllFamilies` |
| spawn raiders / bandit camp | verified in spec 10: `spawnRaiders` +18 a squad, `spawnEliteRaiders` +54, `spawnBanditCamp` +18 (the cheat `SpawnRaidersOfType` still has no effect) | `spawn_raid`, `spawn_bandit_camp` | helper command, see spec 10 `spike-S2.md` |
| raid timer | verified in spec 10: write holds, raid on the day tick that reaches 0 | `set_raid_timer` | `TemporalComponent.daysUntilNextRaid` |
| kill units, write loot per unit, count units | verified in spec 10 | `kill_units`, `set_unit_loot`, `units_census` | helper commands, `spike-S3.md`, `spike-S5.md` |
| count and take a share of buildings, goods and families (burn or collapse, remove goods, kill families) | verified in spec 10 (`sack-village` and others, 3 of 3 real runs). Needs `HarnessActions` version 8 | `sack_census`, `sack_buildings`, `sack_goods`, `sack_people`, `sack_village` | `StartFire`, `collapseBuilding`, `consumeGoodNoCheck`, `SMUnit:just_die` on a family; see `spike-S6.md` |
| loot on the ground | **no such thing in the base game.** A stand-in ledger (piles as Lua tables, recovery with `GiveItemByID`) is verified in spec 10 | `drop_loot`, `loot_piles`, `recover_loot` | helper commands, `spike-R3.md` |
| read the unit table (rows and number fields) | verified in spec 10 (`unit-data`). `DT_UnitTemplates` is a loaded DataTable; 25 rows (29 names with 4 separator lines); fields `cost`, `maxSize`, `minMeleeTraining`, `minArcheryTraining`, `minHouseLv`, `combatExperience`. Needs `HarnessActions` version 9 | `datatable_info("units")`, `datatable_rows`, `datatable_read(..., table="units")` | helper command with `"table":"units"`; `spike-S7.md` |
| write a unit data field | verified: `maxSize` 32 -> 10 changed the next squad to 10 units. In memory only | `datatable_write(row, field, value, table="units")` | `row[field] = value` in Lua |
| spawn units of a chosen template on a side | verified: `spearMilitia` 32 units, `retinue_tier3` 36, `Brigands` 18; side `player` or `bandit` by the owner pawn | `spawn_units(side, template, count, dx, dy)` | `RTSMultiEngineCPP:spawnArmy` from Lua with the player or bandit pawn |
| count living units, casualties and experience of those squads | verified (registry by squad id; `unitTemp` of a unit still reads None) | `battle_state(detail)`, `clear_battle(side)`, `set_squad_experience(squad, value)` | `spike-C1.md`, `spike-C2.md` |
| hire a mercenary company | verified: silver falls by the cost, the offer leaves the list, units are there at once. The game does not check the cost; the action does | `mercenary_offers()`, `hire_mercenaries(company)` | `RTSMultiEngineCPP:hireMercs(company, pawn)` from Lua; `spike-P5.md` |
| rebuild cost of a ruin | verified in spec 10 (`rebuild-cost`, 3 of 3). No cost table can be read, but a construction site lists its goods: `building_sites(type)` gives `needs` (Dunghill: Planks 4). A rebuild is "demolish the ruin, place again" and costs the full amount in the base game. Needs `HarnessActions` version 11 | `building_sites`, `ruin_building(type, method)`, `demolish_ruins`, `set_site_cost(type, good, amount)` | helper commands; `constructionGoods`, `StartFire`, `demolish(true)`; `spike-R8.md` |
| lower the goods a construction site needs | verified: `amt` 4 -> 2 on a site, the builders used 2 planks. Lower only | `set_site_cost` | write `constructionGoods[i].amt` |
| show a banner text and read it back | verified: `playEventMessage(FName("Default"), text, text2)` creates `genericAchievement_EventMessage_C`; `Text` and `main_txt` hold the text. The banner fades. Needs `HarnessActions` version 10. Replaces the old "not possible (crash)" row: the crash came from a plain string for the Name parameter | `show_message(text, subtext)`, `read_message()`, `list_messages()` | helper command; `spike-S9.md` |

## Answers to the open questions of the spec

- Is there an `MLCheatManager` instance? **Yes.** `FindAllOf("MLCheatManager")` gives 1 object, and `PlayerController.CheatManager` returns the same one.
  It exists because the stock UE4SS mod `CheatManagerEnablerMod` is on in `ue4ss\Mods\mods.txt` (`UE4SS.log`: "Constructed CheatManager").
  **Caveat:** if that mod is turned off, the cheat manager actions fail. The console command `EnableCheats` did not create one (it was there already, so this is not proof).
- Do setters on `Approval` hold? Not always. See the region rows below.
- Is there a reflected function that places a building or starts a raid? No function that places a building from a bridge call was found (a real OS mouse click does place one: `place_building`, third attempt in `building-placement.md`) (second search and probe: `building-placement.md`; a third attempt with a faked mouse hook and a raw spawn call also placed nothing, 2026-10-10). `RTSMultiEngineCPP:spawnRaiders(NumSquads, ArmyCenter struct)` exists, but it was not called (struct parameter). The cheat `SpawnRaidersOfType("Bandit")` changed nothing.

## Player values (probe-money)

All calls were made while the game was paused. Before: silver 0, influence 0, kingsFavour 0, predictedIncome 0.

| Step | Result |
|---|---|
| `changeSilver(100)` | silver 0 -> 100 |
| `ChangeTreasury(100)` (same pawn) | 100 -> 200 (it adds, like `changeSilver`) |
| `changeSilver(-50)` | 200 -> 150 |
| `changeInfluence(10.0)` | influence 0 -> 10. The parameter is a const reference float in the jmap, but the bridge call works |
| `changeKingsFavour(5)` | kingsFavour 0 -> 5 |
| `set silver = 500` | 150 -> 500. The bridge answers `{previous, current}` |
| `set influence = 50` | 10 -> 50 |
| after 6 game seconds | silver 500, influence 50, kingsFavour 5, predictedIncome 0 (nothing overwritten) |

Cheat manager (probe-cheat, probe-cheat2): console `ChangeTreasury 77` (through the bridge `console` op) gave silver 0 -> 77.
`first:MLCheatManager` `ChangeTreasury(50)` gave 100 -> 150. So the cheat **adds**, whatever the parameter name `InNewTreasury` says.

## HUD (probe-hud2, scenario silver-change)

- The silver number of the HUD is `W_HUD_LordPanel_V2_C.TreasuryNumeric` (class `MLNumericTextBlock`). `objects` finds two panels: use the one under `/Engine/Transient` (the other is the class template, and its `TreasuryNumeric` is invalid).
- `TreasuryNumeric:GetText()` returned `"0"` before and `"100"` 3 game seconds after `changeSilver(100)`. `GetCurrentValue` cannot be called.
- The HUD writes 1000 and more as `"1.2k"` (silver 1150). Compare exact numbers only below 1000.
- The HUD updates only while the game runs. With the game paused, it did not follow a new silver value within 10 s. Run a few game seconds first.

## Calendar (probe-time)

Start: day 61, month 3, Season 1 (spring), daysTotal 0, gameSpeed 0.

| Call | day | month | Season | daysTotal |
|---|---|---|---|---|
| `setDay(10)` | 10 | 1 | 0 winter (`isWinter` true) | 1 |
| `setDay(100)` | 100 | 4 | 1 spring | 2 |
| `setDay(200)` | 200 | 7 | 2 summer | 3 |
| `setDay(300)` | 300 | 10 | 3 autumn | 4 |

- `daysTotal` grows by 1 for each `setDay` call, so a test that uses `run_game_days` must compare differences.
- After 6 running game seconds the date stayed 300 (not overwritten). `set Season = 3` and `UpdateDateAndSeason()` changed nothing (the season was already 3).
- Only the calendar was read. Whether trees, snow and the look of the world follow is **not verified**.
- `RTSMultiEngineCPP:setGameSpeed(3.0)`: gameSpeed read 3 and the clock moved 9.4 in 3 s. It works, but `ctx.time` (changeGameSpeed with the speed index) is the checked way. `setGameSpeed(0)` does not pause (spec 02).

## Weather (probe-time, probe-weather, probe-cheat2)

- `TemporalComponent:setWeatherSpeed(5.0)`: no error, no visible change in `wind`, `raining`, `snowing`.
- `set raining = true` has no effect (the property is a float: it stayed 0). Use floats.
- Values written, read back at once, and read again after 6 running game seconds:

| Property | written | after 6 s |
|---|---|---|
| raining | 1.0 | 0.95 |
| snowing | 1.0 | 0.95 (snowLevel 0 -> 0.012) |
| droughtLevel | 0.5 | 0.45 (`isDrought` stayed false) |
| wind | 0.9 | 0.39 |
| fogLevel | 0.8 | 0.8 |

  So the game moves the weather back toward its own target. A weather test must read the effect soon after the write.
- `MLCheatManager:RainNow()`: raining 0 -> 0.036 after 3 game seconds -> 0.115 after 13 game seconds. The rain rises slowly.

## Region values (probe-region, scenario winter-region)

probe-region used the first settled region of the list (`Wilde Wand`). The winter-region scenario used the region of the player (`PawnCPP.currentRegion`).
Region names change between runs, so a test must not rely on a name.

| Step (probe-region) | Result |
|---|---|
| `set Approval = 77` | 50 -> 77 |
| `set publicOrder = 33` | 100 -> 33 |
| `set regionalWealth = 123` | 50 -> 123 |
| `set supplies_food = 55.0` | 3 -> 55 |
| `Region:addRegionalWealth(25)` | 123 -> 148 |
| after 6 running game seconds | all four values unchanged |
| after one more game day (40 s) | Approval 77, publicOrder 33, regionalWealth 148 (kept). **supplies_food 2** (recalculated) |

Player region, scenario winter-region (3 runs): `Approval 80` written, **49, 47 and 50 after 3 game days**. `publicOrder` went from 100 to 90 by itself.
`regionalWealth = 200` was **still 200** after 3 game days (3 of 3 runs, also in the telemetry samples).
Conclusion: wealth holds. Approval and supplies_food are recalculated by the game within one to three game days. Tests that need a special Approval must read it soon after the write.
The data does not show when exactly the game recalculates Approval.

## Cheat manager goods and world (probe-cheat2, probe-cheat3, probe-names)

Stock was read with `Region:getStockOfGood(id, false, false)` of the player region.

| Call | Result |
|---|---|
| `GiveItemByID(1, 40)` | stock of item 1: 0 -> 40 |
| `GiveItemByName("Timber", 7)` | item 16: 8 -> 15 |
| `GiveItemByName("Planks", 7)` | item 17: 0 -> 7 |
| `GiveItemByName("Fish", 7)` | item 30: 0 -> 7 |
| `GiveItemByName` with Wood, Log, Logs, Bread, Firewood, Stone, Iron, Wheat, Meat, Berries | no change in any of the ids 0 to 79 (not item names) |
| `MLBlueprintFunctionLibrary:TypeToName(i)` / `TypeToStr(i)` | return the number as text. They give no names |
| `SetSettlementLevel(1)` | `settlementLevel` 0 -> 1 (`tier` stayed 0) |
| `SpawnBanditSquad()` | `SMUnit` objects 189 -> 207 (+18); population stayed 10 |
| `SpawnRaidersOfType("Bandit")` | no change in the unit count |
| `RemoveAllFamilies()` | population 10 and families 5, unchanged after the call |
| `RTSMultiEngineCPP:spawnBanditCamp()` | no error; the effect was not measured |

Item names with a confirmed effect: `Timber` (16), `Planks` (17), `Fish` (30). The real item table is `DT_Items`; reading its properties through the bridge crashed the game.

## Letters (probe-mail, probe-helper3, scenario letter-delivery)

- `PawnCPP.InBox` and `outbox` can be read through the bridge. Both are empty after the load. The welcome letter did not arrive in 45 game seconds in this fixture.
  (An earlier note saw `welcome_from_hildebolt` in the InBox at `daySent` 6 in another session.)
- A `Letter` has: `Guid`, `daySent`, `paras` (names), `read`, `recipient`, `sender`, `recipientSetupIndex`, `senderSetupIndex`, `wasOpened`.
- `PawnCPP:sendLetter(recipient: PawnCPP, Letter: Array<Name>)` through the bridge: error `Value must be UObject or nil`. The bridge cannot pass an object.
- Through the helper mod `HarnessActions` (`FName` values for the names): InBox 0 -> 1 with `paras = ["welcome_from_hildebolt"]`, `sender` an `PawnCPP_AI`, `recipient` the player.
  Passing plain strings for the names **crashed the game** (first helper run). `FName(name)` works.
- The `read` flag of the new letter was false in one run and true in two others: do not assert on it.
- Only the paragraph `welcome_from_hildebolt` was tried. Other names may be missing in the game data, so `send_letter` accepts only the tried one.
- Not verified: the "A New Message" banner on screen.

## Not possible

### save_state (`PawnCPP:requestSaveFile`)
`requestSaveFile("saveGame_9", "probe-save")` returned true. It wrote into the **user's real save folder** (`%LOCALAPPDATA%\ManorLords\Saved\SaveGames`),
not into the private `LOCALAPPDATA` of the run. The launcher guard failed the run (`harness_error`: changed `saveGame_9.sav`, `saveGame_9_coat_1.png`, `saveGame_9_coat_2.png`,
`saveGame_9_descr.sav`; new `saveGame_9_coat_3.png`, `saveGame_9_coat_4.png`). `IoHandler:DoesSaveGameExist("saveGame_9")` was already true before the call, so the
IoHandler reads and writes the real folder. The private folder only got its own `saveGame_0` files.
**This overwrote the user's `saveGame_9`** (an old save from 2024). The folder `SaveGames-backup` next to `SaveGames` holds an older copy of the six files. See the report of this work for the restore step.
The probe does not call `requestSaveFile` any more. The same risk applies to any other call that goes through the IoHandler (autosave, `SaveGameToSlot`, `DeleteGameInSlot`).
Make fixtures with `harness/tools/fixtures.py` instead. The launcher guard worked as designed.

### playEventMessage
`PawnCPP:playEventMessage("Default", "Probe title", "Probe text")` ended the game process. A crash report exists (access violation in `push_nameproperty`: a string was given for a `Name` parameter). The scenario `selftest-crash` uses it on purpose.

### getItem and DT_Items
`RTSMultiEngineCPP:getItem(1)` (returns a struct) and reading the properties of `DT_Items` both ended the game process. Not tried again.

### RemoveAllFamilies, SpawnRaidersOfType, spawnBanditCamp
No effect on the numbers that were read. They may need a selection, a valid type name, or more time. Not verified.

## Bridge limits seen

- Return values that are structs come back as dicts (the Letter in the InBox). A call that returns a struct can crash the game (`getItem`).
- `console` works for exec functions: `ChangeTreasury 77` changed silver. A direct call on `first:MLCheatManager` also works and is simpler to check.
- A game crash gives the verdict `crash`; `mod.log` and `UE4SS.log` stay. The UE crash report lands in the user's REAL `Crashes` folder and is now copied into `<run>/crash/` (found on 2026-10-10, see `03-run-launcher/implementation-notes/real-crash-report.md`).
  Causes: `getItem` crashes UE4SS on the `SoftClassProperty` of the returned `Item`. `playEventMessage` crashes because a plain string was given for a `Name` parameter (needs `FName`).
- One probe run takes 40 to 110 s, mostly the boot (about 30 s).
