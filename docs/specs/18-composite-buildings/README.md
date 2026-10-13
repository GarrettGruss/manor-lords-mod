# Spec 18: Custom composite buildings

Status: spec written (2026-10-12). Spike not started. Issue: #69. Branch: `feat/18-composite-buildings`.

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
3. Pak: make a minimal pak that adds one new building type with its own part list. Check if it loads, shows in the build menu, and can be placed.
4. Function: test if the new type can carry a building function, for example housing families like the tent.
5. Write findings to `implementation-notes/`, one file per topic.

## Open questions

- Which asset holds the part list of a building type?
- Does the build menu read its list from data, or is it fixed in native code?
- Does a new type need a new `EBuildingType` value? Enums are native, so this may block a pak.
- Can a new type reuse an existing type id with a different part list?

## Acceptance criteria

- [ ] A note names the asset or code that defines the parts of a building type, with evidence.
- [ ] A note says if Lua can change the parts of a built master, with a test result.
- [ ] A note says if a pak can add a new composite building type, with a test result or a clear reason why not.
- [ ] If the answer is no, the reason is recorded and the issue is closed as blocked or done.
