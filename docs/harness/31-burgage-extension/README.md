# Spec 31: Custom burgage extension

Status: started (2026-10-18). Issue: #230. Branch: `feat/31-burgage-extension`.

## Goal
Find out if a mod can add a NEW burgage plot extension (a backyard add-on like the vegetable garden, orchard, chicken coop, goat shed, or an artisan workshop such as the tailor).
If it can, make one: a weaver extension with a custom model that turns 1 wool into 1 yarn, or 1 flax into 1 linen.

## Non-goals
- No new game logic in native code. Only data (pak rows, cooked assets) and Lua.
- No mouse tests with the real mouse. If only the mouse works, record it as open.
- No save or load test. No save function is called.
- No finished content pak for release. This is a spike.

## Known facts (from specs 15, 18, 22, 23)
- A plot is an `SMBuildingMaster` (type 3). `Extensions[]` holds the yard. Each entry has a `Type` number (0 = clutter, 6 = tailor, 8 = vegetable garden, ...).
- `PawnCPP:addExtensionChangeRequest({buildingMaster, upgradeID = <extension number>, Slot})` builds an extension without the mouse. `upgradesDone` stores number + 100.
- `DT_Upgrades` rows 100 to 116 are the vanilla extensions 0 to 16. Rows 117 to 999 are free for new upgrade rows.
- `DT_IndependentBuildingPartAssemblies` lists the part blueprints of each extension (`extension_tailorShed` -> `BM_SG_Ext_TailorShed`).
- The vanilla weaver is a stand-alone building (`buildingStats` row 33, job 14, input flax 11 and wool 23, output linen 12 and yarn 148).

## Plan
1. Static: read how an extension number maps to a part blueprint, a job and a recipe (data tables, blueprint classes, native enum `EExtensionType`). Notes in `implementation-notes/`.
2. Game: on a vanilla plot, add the tailor extension (6) by Lua. Read the plot, the worker and the stocks over days. This is the baseline.
3. Pak: add `DT_Upgrades` row 117 (clone of a vanilla extension, one visible field changed) and a part assembly row. Try extension number 17 on a plot.
4. Recipe: find where the recipe of an extension workshop lives. Change it to wool -> yarn, flax -> linen if it is data.
5. Model: make a small weaver shed mesh (Meshy if a key exists, else a placeholder), cook it, use it as the extension part. Screenshot it.
6. Write findings and a recommendation.

## Open questions
- Is `Extension.Type` checked against the native enum `EExtensionType` (17 values)?
- Does the job and recipe of an extension workshop come from data, from the part blueprint, or from native code keyed by the number?
- Can a new extension be offered in the plot panel without the mouse?

## Acceptance criteria
- [ ] A note states the data model of an extension (tables, ids, classes) with evidence.
- [ ] A game run shows the vanilla tailor extension working (baseline) with run id.
- [ ] A game run shows if a new extension number (17) loads, builds, and gets a worker.
- [ ] Recipe result: stocks before and after over game days, or a note why it is not possible.
- [ ] Model result: screenshot of a custom mesh on the extension, or a note why not.
- [ ] README status and recommendation (what works, cost to ship one custom extension).
