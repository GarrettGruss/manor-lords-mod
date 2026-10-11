# Spike S6: sack primitives (buildings, goods, people)

Date: 2026-10-10. Branch `feat/27-sack-primitives`. Game: real game, base fixture (`saveGame_0`, Jagged_Cliffs), game paused unless noted.
Tools: a keep-open game (run `s6-explore`) with the bridge for the first questions, then Lua in the new shared modules `HarnessSack` and `HarnessLoot` (hot reloaded), then the scenarios.
Verdict: **all three primitives work from Lua, and every one is counted before and after with a read command.**
S1 (a share is removed), R7 (loss per store is observed) and R3 (stand-in ledger) have a verified test method. R8 is verified for the ruin state only. The rebuild cost cannot be read.

## The start village (base fixture)
4 or 5 buildings (it differs between runs): one HitchingPost (type 30), two Supplies crates (type 88, they hold the goods), one HomelessTents (87), sometimes one more.
Stock about 79 items in 6 goods (the goods sit in the two crates). 5 families, 10 people. One region of the player (`ownerPawn` is the player pawn; the region that the pawn stands in can be another).

## (a) Destroy or burn a building
| Call | Result |
|---|---|
| `SMBuildingMaster:StartFire()` | works. `onFire` true, `fireAmt` rises about 0.02 a game second, `Region.bAnyBuildingOnFire` true. `IsRubble()` is true at once. After about 39 game seconds (two buildings, 4.8 wall seconds at speed 3) the fire is out: `onFire` false, `Data.bType` becomes **75 (`EBuildingType::Rubble`)**, `typeBeforeChange` keeps the old type, `Data.hp` 0 and `maxHp` 100. **The goods inside are destroyed** (a Supplies crate with 8 Timber lost them; the stock fell by 8). |
| `SMBuildingMaster:collapseBuilding()` | works. The building is rubble (type 75) **at once**. The goods inside stay in the rubble and in the stock. |
| `SMBuildingMaster:demolish(true)` on a ruin | the ruin leaves `GetBuildings` (4 to 3) and `getBuildingCount(75, false)` falls (2 to 1). No refund was seen (the ruin held no goods). `canBeDemolished` is false for a Supplies crate, true for a HitchingPost and for rubble. |
| `MLCheatManager:SetFireToNumBuildings(1)` | no effect seen: no `onFire`, no change in 12 s at 1x. Not used. `CollapseNumBuildings` and `CollapseAllBuildings` were not tried (the direct call is better, it picks the building). |
- A burned or collapsed building **stays in `Region:GetBuildings()`** until it is demolished. So the building count does not fall. Count the **standing** buildings (`IsRubble() == false`) and the rubble. `getBuildingCount(75, false)` counts the rubble (the argument `-1` for all types gives 0, do not use it).
- The census (`HarnessSack.census`) reads `IsRubble`, `onFire` and `Data.bType` of each building. It stays correct while a fire burns (`burning`, `rubble`, `standing`).
- Used in the scenarios: `sack_buildings(percent= or count=, method="fire"|"collapse")`. The order is the order of `GetBuildings`; buildings are taken in that order.

## (b) Remove goods
| Call | Result |
|---|---|
| `SMBuildingMaster:consumeGoodNoCheck(goodType)` | removes **one unit** from that building. The region stock (`getStock(false)`) falls by one too. Works through the bridge and in Lua. The module loops (at most 5000 units a call) and stops when the game refuses (no endless loop). |
| `Region:consumeGood(goodType, amt, preferredBuilding, scramble, respect, redistribute)` | not usable through the bridge: the bridge cannot pass an object or `nil` (`nil` is dropped from the argument list: "expected 6 parameters, received 5"; a path string is refused: "Value must be UObject or nil"). Not tried from Lua; `consumeGoodNoCheck` is enough. |
| write `Inventory[i].amt` | not tried. |
| `MLCheatManager:AddItemToBuilding(name, item, count)` | no effect with three forms of the building name (short name, full name, `Timber`). Not used. |
| `MLCheatManager:GiveItemByID/GiveItemByName` | adds goods. They land in **a store that has space** (not always the same building: in one run the Planks went into the first building, in another into a Supplies crate). |
- Where goods live: `SMBuildingMaster.Inventory` (array of `Good {Type, amt}`) per building, and the region stock is the sum (`Region:getStock(false)`). So a store is a building with a non-empty `Inventory`, and a per-store stock read is exact.
- The census lists `stores` (id = number at the end of the building name, type, goods, by_good). The command `sack_goods` removes `percent` of every good, or `amount` of one `good`, optionally from one `store`.
- A returned TArray is a plain Lua table in UE4SS; its elements are `RemoteUnrealParam` and need `:get()`. The property arrays (`Inventory`, `workerFamilies`) are real TArrays (`GetArrayNum`). The module handles both.

## (c) Remove people
| Call | Result |
|---|---|
| `SMUnit:just_die()` on every member of one `Region.workerFamilies[i].familyMembers` | works. `getTotalNumFamilies` 5 to 4, `getNumTotalPopulation` and `getNumHumanResidents` 10 to 8 **at once** (also after a game day at speed 3: they do not come back). `Region.corpses` grows by the dead members. |
| `kill_units(side="civil")` | takes any civil unit in the world (an ox, a hare). It killed an ox of the village once: `residents` fell by one, the human counts did not move. Use the family list for people. |
| `Region:removeWorkerFamilyAt(familyID)`, `RemoveAllFamilies` | not tried / no effect seen (spec 07). Not needed. |
- `sack_people(percent= or count=)` kills the members of whole families (the first families of the list). A percent is therefore only as exact as one family (20% of 5 families).

## Criteria
| Criterion | Scenario | Result |
|---|---|---|
| S1 share removed | `sack-village` | `sack_village(50, 50, 40)` on 4 buildings, 79 items, 5 families: rubble +2 (50%), stock lost 49.4% (range 45 to 55: each good is rounded alone), families -2 (40%). Zero percent changes nothing. 101 percent is refused in Python and in the mod. One game day later nothing came back. |
| R8 ruins and rebuild | `sack-ruins` (no COVERS tag: the coverage tool would count R8 as verified) | State verified: fire, then rubble (type 75), `IsRubble`, hp 0, the ruin stays in the list, the goods inside are gone, `getBuildingCount(75)` agrees. **Rebuild cost not verified**: no reflected function gives the cost of a building (`GetUpgradeResourceCost` is for upgrades only, `getCastleReconstructionCost` for castles), the building data table is not loaded as an object (no `DataTable` with building costs in the jmap dump), and a construction site (`constructionGoods`) needs a building placed with the OS mouse (`place_building`), which this spike did not use. "Partial" also needs the full cost to compare with. `criteria.json` keeps R8 as not verified. |
| R7 guard and lock | `sack-store-trip` | The base game has **no guard or lock concept** (searched the jmap: no such class or function). The observation method is verified: two named stores lose different shares (open barn 50% a trip, guarded granary 10% a trip, two trips, a third store untouched) and each loss is read per store. The guard and lock rule is defined by the scenario (the loss factor). The real mod must define it; the same scenario then runs against it. |
| R3 loot on the ground | `loot-drop-recovery` | See `spike-R3.md`. |

## Traps found
- `require("X")` returns two values in the fake kit (lupa): wrap it in parentheses in tests.
- The bridge cannot pass `nil` or an object. Calls that need one must run in Lua (helper mod).
- `Region:GetBuildings()` includes ruins. A census that counts it as "the buildings" never falls.
- GiveItem goes to any store with space, so a test must not assume the building.
- **Unit tests stopped a real game.** Three runs of a series ended with "game process ended during boot" (exit code 15, the code of a terminate) while unit tests ran in the same shell. Cause found and proven: `test_runlib_phases.py::test_missing_fixture_source_fails` called the real `_stop_stale_game`, which stops every running game. With a game started by `run.py --keep-open` the game was gone after that file; after the fix (the test patches `_stop_stale_game`) the whole `test_runlib*` set left the game alive. This probably explains the unexplained exit code 15 in `spike-S8.md` (not proven for that case).

## Not verified
- The rebuild cost of a ruin (R8). Reading a construction site, or the building cost table (spec 09 pak tools), is the next step.
- A real guard or lock (R7) and a real ground pile with a walking peasant (R3): both are mod-defined.
- A fire that spreads to the neighbours (the fires stayed on the buildings that were lit in the runs).
- Sack effects on a larger village (the fixture has 4 or 5 buildings), on production, approval or the economy.
- `CollapseNumBuildings`, `Region:consumeGood` from Lua, `removeWorkerFamilyAt`, writing `Inventory[i].amt`.

## Harness changes from this spike
`mod/shared/HarnessSack`, `mod/shared/HarnessLoot`, `HarnessActions` version 8 (commands `sack_census`, `sack_buildings`, `sack_goods`, `sack_people`, `sack_village`, `drop_loot`, `loot_piles`, `recover_loot`),
`harness/runlib/sack.py`, actions in `harness/runlib/actions.py`, scenarios `sack-village`, `sack-ruins`, `sack-store-trip`, `loot-drop-recovery`.
Tests: `test_runlib_sack.py`, `test_fakegame_harnesssack.py`, `test_fakegame_sack_scenarios.py`.
