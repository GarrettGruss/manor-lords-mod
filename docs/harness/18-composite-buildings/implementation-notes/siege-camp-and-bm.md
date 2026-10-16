# Siege Camp in the menu, and a new composite building from a pak (2026-10-14)

Spec 18, issue #69. Game 0.8.111, fixture `base`, single player. 6 game launches (runs `s18sc-1` to `s18sc-6`, all `noop --keep-open`, driven by the bridge and the real OS mouse).
No save function was called. The AES key came only from the environment. The game is closed and `~mods` is removed.
Screenshots are in git-ignored run folders (`runs/<id>/screenshots/`).

## Part A: Siege Camp (row 483, `BM_SiegeCamp_C`)

Pak `siege483` (`mod/HarnessActions/paks/siege483_P.pak`): row 483 has `bVisibleInUi` true. The writer needs `IsZero` false too (see Traps).

| Check | Result |
|---|---|
| Card in the build menu | YES. Military tab (castle icon) shows 3 cards: Settlers Camp, Manor gatehouse, Siege Camp. Hover text: "Siege Camp. Work in Progress. Placing nearby friendly units allows utilizing Siege Equipment." No cost line. Screenshots `runs/s18sc-1/screenshots/menu_military2.png`, `hover3.png`. |
| Place with `activateBuildingMode(483)` + real click | YES. Two placements gave two `SMBuildingMaster` of type 483. Tooltip "Siege Camp (under construction)". `runs/s18sc-1/screenshots/placed2.png`. |
| Parts of a master of type 483 | 4 parts (`SMBuilding`, 3 with tag `adjustSlope`, 1 with tag `clutter`) and 2 resource slots `res_16_*` (timber). `maxHp` 100. |
| Built | NO. 28 game days at speed 3 with 100 timber and 100 planks given: `built` false, `constructed` false, 4 parts. |
| `Region` of the master | `<invalid>` (a normal building has the village region). The two sites stood about 1.5 k units from the village. A property write of `Region` through the bridge does nothing. Reason not proven. Guess: the Siege Camp needs an army or a map mode, and has no region logic in this mode. |
| Building count | `getBuildingCount(483)` stays 0 (no region), unlike the tent (0 to 1). |

### Placement rules seen (user correction during the run)
- A valid ghost is WHITE. A red or orange hatched ghost is invalid.
- The first click was on a filled burgage plot: "no road access" error and nothing placed. Place on open grass next to the road network, away from plot outlines. Check the ghost in a screenshot before the click.
- The harness `place_building` needs the camera over open ground. Move the camera by `K2_TeleportTo` on the player pawn (the pawn is the camera). Window fractions: the tent ghost at (0.54, 0.30) was valid after teleport to the village centre.
- The mod command limit `MAX_TYPE` was 300 in `HarnessBuild` and `HarnessHousing`. It is now 600, so `master_parts` and `building_stat` accept 483. The shared Lua module stays cached after `reload_mods`, so the old limit stayed until the game restarted. A raw bridge read of `SMBuildingMaster.Data.bType` was used instead.

## Part B: a new composite building made in UE 5.5.4

Blueprint `BM_HarnessCamp` (parent `StaticMeshActor`), made headless with `mod/HarnessActions/ue/make_bm.py` in `C:\Users\garre\development\mlm-ue\ManorLords`. It has 3 `StaticMeshComponent` parts with engine meshes `/Engine/BasicShapes/Cube`, `Cone`, `Sphere`. Cooked with `-run=cook` (about 1 min), packed with `pakmod.py build`.
Pak `bmcamp4` (`mod/HarnessActions/paks/bmcamp4_P.pak`): row 123 (clone of the tent row 87) points at the vanilla path `/Game/CPP_BP/BuildingMasterAssemble/BM_HuntingCamp` (the pak replaces that asset with the 3-mesh Blueprint). Row 124 (clone of row 87) points at the new path `/Game/HarnessMod/BM_HarnessCamp`. Both rows have `bVisibleInUi` true.

### Results
| Check | Result |
|---|---|
| Placement of new ids 123 and 124 (`activateBuildingMode` + real click, white ghost) | YES. `getBuildingCount` 0 to 1 each. Both ids exist only in the pak. |
| Built | YES. `built` true after 4 game days (the tent costs nothing). |
| Parts | YES. 3 parts each (`SMBuilding`), meshes Cube, Cone, Sphere at the planned offsets (checked with `StaticMesh` and component location). |
| Screenshot | `runs/s18sc-5/screenshots/built124.png`: a grey cube with a cone and a sphere in the meadow, for 124 (centre) and 123 (right). Also `runs/s18sc-6/screenshots/built124_nopreload.png`. |
| New asset path `/Game/HarnessMod/...` without any Lua preload | WORKS (run 6). The class was NOT loaded by Lua before the click. |
| Build menu card for 123 and 124 | NO. The Military tab shows only 2 cards (run 2). The tent row category is not Military. A card for a type of another category was not looked for in the other tabs. A card needs the right `BuildingCategory` and art (not tested). |
| Function | Comes from the row (tent: `buildingFunction` 7, same as row 87). Not changed. |

### The part name rule (important)
- First try (run 2 to 4): components named `Part0..2`. The master was placed and built but had 0 parts, with the class loaded or not.
- The vanilla `BM_HuntingCamp` has components named by prefix: `MainBld_*`, `Bld_*`, `bench_*`, `clutter_*`, `lazyBld_*`, `Dirt_*`, `res_<good>_<n>` (see the Siege Camp resource slots `res_16_0`). The master classifies parts by this prefix.
- With `MainBld_900`, `MainBld_901`, `Bld_902` all 3 parts appear (runs 5 and 6). `make_bm.py` names them this way.
- Control (run 3): row 123 pointed at the vanilla `BM_HuntingCamp_C` gives 16 parts. So a new id with an existing class works, and the pak class was the only difference.

## Answers
- Can a pak add a new composite building type that is placed, built and shows new parts? YES (ids 123 and 124).
- Is a new type id placeable without the menu card? YES, with `activateBuildingMode(id)`.
- Is the Siege Camp usable? It shows in the menu and can be placed, but it stays an unbuilt site with no region. Siege use needs an army (not tested).

## Traps
- `bVisibleInUi` in a row JSON has `IsZero` true when false. Set `IsZero` false and `Value` true (new command `s65_edit_json.py visible`), or the value may not be written.
- The workspace config `Config/DefaultGame.ini` needs `+DirectoriesToAlwaysCook=(Path="/Game/CPP_BP/BuildingMasterAssemble")` to cook an asset at a vanilla path (outside `/Game/HarnessMod`). I added that line to the workspace outside the repo.
- `run.py --keep-open` with `--pak` ends with a `harness_error` (`paks-remove` cannot delete the pak that the game uses). The game keeps running with the pak. Remove the pak after closing the game: `pakmod.py remove --all`.
- The command channel (`CommandChannel`) numbers requests from 1 in each Python process and the mod expects the next number. A second client process gets stale results unless the mod is reloaded (`reload_mods.py`) and the `commands` folder is emptied.
- Placing needs the camera over open ground. Do not run the UE editor while a game screenshot is taken.

## Changes outside the repo
- Game folder: `Paks\~mods\` had `siege483_P`, `bmcamp123_P`, `bmcamp2_P`, `bmcamp3_P`, `bmcamp4_P` in turn. All removed. `~mods` does not exist now.
- UE workspace `mlm-ue\ManorLords`: `make_bm.py`, assets `Content/HarnessMod/BM_HarnessCamp`, `Content/CPP_BP/BuildingMasterAssemble/BM_HuntingCamp`, one added line in `Config/DefaultGame.ini`.
- `modtools/work`: folders `siege483`, `bmcamp123`, `bmcamp2`, `bmcamp3`, `bmcamp4`, `siege483json` (git-ignored). The vanilla `buildingStats.json` was restored after each use (hash checked).

## Open
- Why the Siege Camp master has no region and is never built (needs an army, or a flag in the invasion code).
- A menu card for a new id: set `BuildingCategory` of the row, and check the other tabs. A new card art needs a widget pak (spec 16 method).
- Replace a vanilla path was only needed as a check. It is not needed.
- A name text for ids 123 and 124 (`DT_Translation_BuildingNames`).
