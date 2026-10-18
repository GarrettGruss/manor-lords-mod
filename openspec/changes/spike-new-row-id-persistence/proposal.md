# Proposal: Spike new row id persistence

Issue: #284. Legacy source: `docs/harness/23-row-id-range/README.md` ("Risks", "Result and proposed id ranges": Open list) and `docs/harness/23-row-id-range/implementation-notes/id-results.md`.

## Why
Spec 23 found that new `buildingStats` ids (126 to 65536) load, show, are placed, are built and survive 45 game days. The id ranges are in use (`mod.json` of the Invasion Mod, row patches). Three checks are still open:
- Save and load of a building with a new id. The spec forbade a save call then. The guarded `save_game` exists now.
- Use of a new `DT_Upgrades` row in the game. Only ids 117 and 118 were read.
- AI build lists: does an AI lord ignore, or crash on, a new building id?

Large ids may work in the menu and break systems that are not visible at once (save files, AI lists). The 45 day runs lower this risk but do not remove it.

## What Changes
- Build a building with a new id, save with `save_game`, load the slot, and check the building.
- Use a new upgrade row in the game (research or place) and check the effect.
- Run an AI lord village next to a new id and check for errors.
- Write the results to `notes/`, and update the id rule if a range fails.

## Non-goals
- New features or new ids for real content.
- Text key checks beyond `buildingID_<id>`.

## Legacy folders
`docs/harness/23-row-id-range/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None now. A failed range changes the id rule in `harness/pak-mods`.

## Impact
Needs the real game, the real mouse for placement (exclusive), a fresh save backup, and the user informed before the first `save_game` call.
