# Spec 18: Custom composite buildings

Status: Siege Camp build spike (#94) done in part: the camp has no build path (notes `siege-camp-build.md`). static, Lua part-edit and pak spikes done (2026-10-13). Placement of a new type id is open (needs the real mouse). Hidden and unused buildings: `implementation-notes/hidden-buildings.md`. Issue: #69. Branch: `feat/18-composite-buildings`. Mouse-free normal placement (#104, #115, 2026-10-15): not achieved, see `implementation-notes/mousefree-placement.md`. Real mouse back (2026-10-15): placement of vanilla row 30 and new row 125 works, see `implementation-notes/real-mouse-placement-proof.md`.

Spec 13 lead (2026-10-14): MLArmyCampMod makes no buildable camp and no garrison (squad skills Encamp and Decamp by a native DLL; no row, no BM_ class), see `../13-mod-inspection/implementation-notes/ml-army-camp.md`. SwapShrine shows a Lua-only mesh swap on a finished building (`LoadAsset_Blocking` plus `SetStaticMesh`), see `../13-mod-inspection/implementation-notes/swap-shrine.md`.

## Goal

Find out if we can make new composite buildings and ship them in a pak as new structures.
A composite building is one `SMBuildingMaster` that holds `SMBuilding` parts.
The tent, the bandit camp and the burgage plot are built this way.

## Known facts

From spec 15 notes (`tent-placement.md`, `burgage-placement-events.md`):

- A tent is an `SMBuildingMaster` of type 87, `buildingFunction` 7, with about 17 prop parts. It holds families in `occupantFamilyIDs`.
- A bandit camp is the same model: type 100, `buildingFunction` 17, owner `PawnCPP_AI`.
- A burgage plot is a master with parts. The house is one mesh part. `Extensions[]` holds the yard, with its own parts and a `Type`.
- Manor modules (tax office 58, garrison 57, tower 472) are `SMBuilding` parts of the manor (spec 14 notes).
- A live write to a `buildingStats` slot is ignored by buildings that already exist.

## Non-goals

- Ship a finished content pak. This spec is a spike that answers if it is possible.
- Change the manor module system. That is #65.
- Place normal buildings inside the bailey. That is spec 17 (#68).

## Plan

1. Data: find where the parts of a building type are defined (data table, blueprint class, building stats). Find how each part mesh is chosen. Use the pak tools of spec 09 and spec 11 on exported data only. No game assets go in git.
2. Run time: test if Lua can add or remove a part on a built master, in a test game.
3. Pak (BLOCKED on the AES key, no extract or repack possible): make a minimal pak that adds one new building type with its own part list. Check if it loads, shows in the build menu, and can be placed.
4. Function (BLOCKED, needs step 3): test if the new type can carry a building function, for example housing families like the tent.
5. Write findings to `implementation-notes/`, one file per topic.

## Open questions

- Which asset holds the part list of a building type?
- Does the build menu read its list from data, or is it fixed in native code?
- Does a new type need a new `EBuildingType` value? Enums are native, so this may block a pak.
- Can a new type reuse an existing type id with a different part list?

## Acceptance criteria

- [x] A note names the asset or code that defines the parts of a building type, with evidence. `implementation-notes/building-parts-static.md` (row -> `BM_*` class; link for tent and plot not read, partly open).
- [x] A note says if Lua can change the parts of a built master, with a test result. `implementation-notes/part-edit-test.md`: append and unlink work in memory; a visible new part is not solved.
- [x] A note says if a pak can add a new composite building type. `implementation-notes/composite-pak.md`: rows 123 and 124 load; a new part list works by pointing row 87 at another `BM_*` class (17 to 16 parts in a real run); placing a new id is not tested (mouse only).
- [x] A new composite type is placed and built in the real game with a new part list from a Blueprint made in UE 5.5.4. `implementation-notes/siege-camp-and-bm.md`: ids 123 and 124 (pak `bmcamp4`) placed with `activateBuildingMode` and a real click, built in 4 days, 3 parts (Cube, Cone, Sphere), screenshot `runs/s18sc-5/screenshots/built124.png`. Part names must start with `MainBld_` or `Bld_`.
- [x] The hidden Siege Camp (row 483) shows in the Military tab with a pak and can be placed. It never builds (no region). Same note.
- [ ] A build menu card for a new id (category, art, name text) is open.

## Status (2026-10-14)
- Done: Siege Camp card and placement, new `BM_` class from UE with new meshes placed and built (see `implementation-notes/siege-camp-and-bm.md`). Open: menu card for a new id, Siege Camp build.
- Access points (#104, static): `gathering`, `workpos` and `res_<good>_<n>` + `workPos_add*` tags define entry and delivery; animal capacity is the row field `stableSpace`; no per-ox spot component found. Plan for a 4-oxen stable in `implementation-notes/access-points.md`.
- Game round (#104, 2026-10-15): pak `stable4` (row 97 and new row 125, `stableSpace` 4, class `BM_HarnessLargeStable` with two real ox sheds) gives `stableMax` 4, two sheds and 4 housed oxen (HUD 4). Placing row 125 by mouse is open: the mouse does not reach the world (`getMouse3d` Z -100000). Notes `access-points.md` "Game round".
- Real-mouse round (#104, #115, 2026-10-15): row 125 placed with a real click (white ghost, master type 125, built after 14 game days, stableMax 4, 4 oxen housed). Notes `real-mouse-placement-proof.md`.

## Earlier status (2026-10-13)
- Done: static read (`implementation-notes/building-parts-static.md`) and the Lua part-edit test (`implementation-notes/part-edit-test.md`,
  HarnessActions 38, commands `master_parts`, `master_part_add`, `master_part_remove`, probe `probe-composite`).
- Blocked: plan steps 3 and 4 (pak with a new type, building function). They need the AES key to extract and repack. Resume when the key is set.
- Open: spawn a visible part from a real `BM_*` class; read `BlueprintPath` of rows 87 and 3 safely.

## Decision (2026-10-15): ox hitch spots
- The number of ox hitch spots is native (about 2 per stable). Hooks, mesh sockets and Scene probes did not show the source. A larger shed mesh does not add spots. Notes `big-ox-shed-test.md`, `ox-hitch-hook.md`.
- Capacity 4 (`stableSpace`) is proven and stays. The 4-oxen stable is done as far as Lua and pak allow. No further hitch tests unless a way to create a hitching post (blocked by native code) is found.
