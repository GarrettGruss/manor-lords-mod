# Corpse pit: class, building id, body carry, delivery (task 1.1)

Runs (slot 2, fixture `base`, game 0.8.111): `corpse-3` (pit built, bodies collected, one crash), `corpse-4` (full chain, delivery, pictures). `corpse-2` was lost before any test (the game process was gone; cause unknown, another game was started on the machine at the same time). Probe code was Lua through `eval_lua` (approved) with `allow_eval = true` in the slot 2 copy of `UEBridge/scripts/settings.lua`, then the bridge op `reload`. `deploy` resets that file on each run.

## Facts
- Building row `DT_Buildings` / `buildingStats.json` id 113, name "Corpse Pit". Master class `SMBuildingMaster` (`Data.bType = 113`). Visual Blueprint `/Game/CPP_BP/BuildingMasterAssemble/BM_CorpsePit.BM_CorpsePit_C`. It is a `StaticMeshActor` Blueprint with only components (`workpos_0..4`, `Dirt_6_7`, `exclusion_0`, `bld_0`). It has NO Blueprint functions and no logic. Load it with the asset registry call (`AssetRegistryHelpers:GetAsset`), as `HarnessActions` does for pak classes.
- Row 113: `job` 65, `isWork` true, `workerTypes` (0,4,0,0) = 4 worker slots, `range` 1500, no construction goods, `constructionCost` 0, `needsRoad` false.
- Placement: `HarnessPlace` (no mouse) does NOT work for a normal building (archived spec 18 notes). The real mouse works when a mouse device exists: ghost hover at window fraction (0.35, 0.3) with the camera centred on (-37164, -51658), white ghost, click, then `getBuildingCount(113)` = 1, master not constructed. No action in `HarnessActions` places it. See "Hazards".
- Built after about 3 game days at speed 3 (cost 0, builders came by themselves).
- The game assigns NO worker by itself: 0 workers and 0 bodies moved over 8 game days while 3 families had no workplace (run `corpse-3`). The command `building_assign_worker type=113` (HarnessActions, issue 104, no mouse) assigns one family (3 people; `getAllWorkers` returned 9 units for 3 families). With workers, bodies start to move at once.
- Bodies: a body is the dead `SMUnit` itself (`VAMP_DefaultUnit_C`, `dead = true`). Animals count too (`VAMP_Hare_C` bodies are collected). The list is `Region.corpses` of the region where the unit died, not only the player region (three raider bodies died in region Eichenhau and stayed in its list).
- Carry sequence seen (run `corpse-4`, 1 to 3 game second steps):
  1. A pit worker gets the task label `collecting_body` (`SMUnit.taskLabelOverride`) and walks to a body. Distance does not matter: bodies 22 000 units away were fetched by road (up to about 3 game days).
  2. Pick-up: the body leaves `Region.corpses` when the worker reaches it, and the worker `Inventory` goes from 0 to 1 entry (label `None`).
  3. The worker walks to the pit (`realPos` near the pit centre).
  4. Delivery: the worker `Inventory` goes 1 -> 0 and `SMBuildingMaster.Inventory` of the pit shows one entry `Type = 233` ("corpse", `DT_Items` row 233) whose `amt` grows by 1 per body. 9 bodies delivered = `amt 9`. `numStoredGeneric` stays 0.
- Whether the body actor is destroyed afterwards was not checked.

## Can Lua hook the moment of delivery? Not by function
- The reflected surface has no pit function: `Region` has the property `corpses` and no corpse function; `SMUnit` has `just_die`, `deathAnimationEnded`, `getTaskLabel`, `setTask`; `SMBuildingMaster` has `addToInventory`, `getAllWorkers` and `getNumActiveWorkerFamilies` (it stays 0 even with workers: do not use it).
- Bridge hooks on `SMBuildingMaster:addToInventory` and `SMUnit:setTask` got 0 events over about 9 pick-ups and 9 deliveries. The game does this in native code (no ProcessEvent).
- So the mod must poll (about once a second, like the raid tick): read the pit `Inventory` entry `Type 233` `amt`. Each increase is one delivered body. A pick-up is a body that leaves `Region.corpses`.
- Safe reads used: `b.Inventory[i].Type`, `.amt`, `#unit.Inventory`, `unit.taskLabelOverride:ToString()`, `unit.realPos`, `b:getAllWorkers()`.

## Hazards found
- Reading `unit.currAnim`, `unit.dropsTo:GetFName()` and `unit.Speed` in one eval crashed the game (`EXCEPTION_ACCESS_VIOLATION reading address 0x18`, run `corpse-3`; the report is in the REAL `%LOCALAPPDATA%\ManorLords\Saved\Crashes`). Do not read them. Which of the three is the cause was not separated.
- The real-mouse tools (`s94_drive.py`, `place_building`) pick the game window of ANY game process. With two games on one machine they hover over and screenshot the wrong window (another agent's menu). Pin the window to the own PID (`pick_game_window(list_windows(), {pid})`). The camera also drifts (edge scroll) when the cursor is outside the window: move the cursor to the window centre before `centre_camera_on`.
