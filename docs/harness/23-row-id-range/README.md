# Spec 23: Row id range spike

Status: real-game round done (2026-10-16). Issue: #127. Branch: `feat/23-row-id-range`.
Needed by: spec 22 (reserved id ranges for each mod feature, plan step 5).

## Goal
Find which ids are safe for NEW rows in the game data tables that the mod will extend. Then set an id range for each mod feature.
Known so far: `buildingStats` row 125 (cloned from row 97) loads, shows, is placed by a real click and is built (spec 18, `real-mouse-placement-proof.md`). The vanilla building ids end at 484 (see `implementation-notes/id-types.md`). Id 125 is a free vanilla id.

## Non-goals
- No save and load test. A save function is forbidden (CLAUDE.md Safety). Save persistence of new ids stays an open question.
- No feature content. The test rows are copies of vanilla rows.
- Not every table. Only the tables the mod is likely to extend first.

## Questions
- Q1: How is a row found: by the row name, by an id field in the row, or by its index? Is the id stored as a byte, a short or an int?
- Q2: Does native code use the id as an array index (for example an array sized by the highest vanilla id)? Then a large id may crash or be ignored.
- Q3: Which ids load, show in the build menu, can be placed and built, and work after 30 game days, for each table below?
- Q4: Do gaps in the ids cause problems (for example ids 126 to 999 unused)?

## Tables
Start with `buildingStats` and `DT_Upgrades`. Then, if time allows, the units, items and text tables. Static reads first (UAssetGUI JSON, jmap), as in spec 18 `access-points.md`.

## Plan
1. Static: read the id type and the key of each table (row name vs field). Search the jmap for arrays and maps keyed by building type. Write `implementation-notes/id-types.md`.
2. Pak `ids`: clone a vanilla row (for example the hitching post, row 30) at ids 126, 200, 255, 256, 1000, 2000, 32767 and 65536 (only the ids that the type from step 1 allows).
3. Real game (`--pak ids`): for each id read the row through the bridge, check the build menu, place one building with a real click, build it, run 30 game days. Record crashes as results (spec 03).
4. Same for one new `DT_Upgrades` row that points to a new building id.
5. Result table: table × id → load / show / place / build / 30 days / crash. Propose the id ranges for the features and the rule for the mod.

## Acceptance criteria
- A1: `implementation-notes/id-types.md` states the key and the id type of each studied table, with the evidence.
- A2: The result table covers at least `buildingStats` at 6 ids and `DT_Upgrades` at 2 ids, each with a run id.
- A3: A proposed id range per feature is written into spec 22 (`mod.json` example and rule 3), or the spec says why no safe large range exists.
- A4: Every crash has its crash report copied into the run folder.

## Risks
- Large ids may work in the menu but break native systems that are not visible at once (AI build lists, save files). The 30-day run reduces this risk but does not remove it.
- Mouse placement needs the real mouse (#115).

## Result and proposed id ranges (A2, A3)
Details: `implementation-notes/id-results.md`. In the real game, buildingStats ids 126, 486, 1000, 2000, 32767 and 65536 all load, show in the build menu, are placed with a real click, are built and survive 45 game days with no crash. Two DT_Upgrades rows (117, 118) load. Their use in the game is not tested.

Proposal for spec 22 (`mod.json` and rule 3):
- Vanilla building ids are 1 to 484. The enum sentinel is 485. Do not use ids 1 to 485, and keep 200, 255 and 256 free (other tables use them).
- Every mod feature gets a block of 100 building ids in the range 1000 to 9999. Block start = 1000 + 100 * feature number (feature 22 gets 3200 to 3299, for example). Use the feature number of its spec.
- Ids 10000 to 32766 are a reserve. Do not use ids above 32767 (65536 worked, but the reserve is enough and 16 bit values stay safe).
- Existing test rows 123 and 125 stay as they are. Do not add new rows there.
- Upgrade ids: only 117 and 118 were read. Use 117 to 999 for new upgrade rows until a larger id is tested in the game.
- Text keys: add `buildingID_<id>` for each new id.
- Open: save and load of a new id, upgrade use, AI build lists.
