# Spec 31: Custom burgage extension

Status: spike done (2026-10-18). A new extension NUMBER is not possible with data. A working weaver extension with a custom model IS possible in an existing slot (the tailor, Type 6). See "Result" below. Issue: #230. Branch: `feat/31-burgage-extension`.

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
- [x] A note states the data model of an extension (tables, ids, classes) with evidence. `implementation-notes/data-model.md`.
- [x] A game run shows the vanilla tailor extension (baseline) with run id. It is built and gets job 10, but it made no clothes in 10 game days (`s31-base-3`, `s31-base-9`). `implementation-notes/weaver-reskin-recipe.md`.
- [x] A game run shows if a new extension number (17) loads, builds, and gets a worker. It loads and is accepted, but gives an empty yard, no cost and no job (`s31-ext17-1`, `s31-ext17-2`). `implementation-notes/new-extension-number.md`.
- [x] Recipe result: stocks before and after over game days. Weaver in the tailor slot: wool 50 -> 41 and yarn 56 -> 65 (`s31-weaver106-2`), flax 53 -> 43 and linen 50 -> 60 (`s31-weaver106-3`), 1 : 1.
- [x] Model result: the Meshy weaver shed shows on the extension, no crash (`s31-mesh-3`, screenshot in `runs/`, git-ignored). The texture is flat grey. `implementation-notes/custom-model.md`.
- [x] README status and recommendation (below).

## Result (2026-10-18)
| Question | Answer |
|---|---|
| New extension number (data only)? | NO. `EExtensionType` is native (17 values). Type 17 with a new `DT_Upgrades` row 117 is accepted but gives 0 parts, no cost, no job, and no production. |
| New row in `DT_Upgrades`? | Loads, but only useful for the 17 vanilla types. Edit of row 106 works (cost 6 -> 3 planks). |
| Weaver recipe wool -> yarn, flax -> linen, 1 : 1? | YES in an existing slot. Slot Type 6 (tailor) + `artisanJob` 14 + `EnableRecipe(148 or 12)`, written by Lua. Vanilla data already has the 1 : 1 recipes. |
| Custom model? | YES for an existing slot. Meshy shed, cooked and shipped as a replacement of `SM_MERGED_C_SG_Ext_TailorShed_Ubeam`. Grey texture. |
| Plot panel button / real player use? | Open. Needs the real mouse. |

Run ids: baseline `s31-base-1` to `s31-base-9`, `s31-census-1` to `3`, `s31-bounds-1`, `s31-job14-1`, `s31-recipe-1`, `s31-recipe-2`, `s31-lv2-1`, `s31-ext17-1`, `s31-ext17-2`, `s31-mesh-1` to `3`, `s31-weaver106-1` to `3`.

## Recommendation
- Ship ONE "weaver" by re-using the tailor slot (Type 6). The tailor then no longer exists in the game. If the tailor must stay, use a slot of a less needed artisan (for example Fishmonger, Type 16) and test the same steps: the job write (`artisanJob` 14) and the recipe are the same, the model replaces that slot's mesh.
- Cost to ship one such extension (estimate from this spike):
  - Data: 1 edit of a `DT_Upgrades` row (cost, perks, text key), 0 new rows. The pak builder `buildmod` supports `set` on `DT_Upgrades`.
  - Model: 2 Gemini images, 1 Meshy call (30 credits), one UE import and cook (about 1 minute), a pak of about 3 MB.
  - Lua (needed, because the job and the recipe are native state): a mod feature that, for a plot whose extension Type is the weaver slot, writes `artisanJob` 14 after `addArtisanChangeRequest`, calls `EnableRecipe`, and repeats after every load. About 100 lines. Mods must use named commands, not eval; the spike commands are UNSAFE test commands.
  - Real-game checks still to do: the plot panel text and icon (text keys), a save and load round trip, several plots, the texture look (material fix), the user check by eye.
- A truly new extension (a 18th Type) needs native code. This is out of reach for a data and Lua mod. Do not plan for it.
- Alternative with more freedom: a new STAND-ALONE building (new `buildingStats` row, spec 18 and 23 route). It can have its own job, recipe, blueprint and model, and is placed with the mouse like row 125.

## Tools made
- `harness/scenarios/probe_extension.py` (hidden probe), commands `master_artisan`, `master_artisan_set`, `plot_upgrade` flag `artisan`, `master_parts` `ext_limit`.
- `harness/tools/s31_make_extension_json.py` (clone or edit a `DT_Upgrades` extension row), `mod/HarnessActions/ue/import_replace_mesh.py` (import a mesh over a vanilla asset path).
- A separate pak work folder for a spike: copy `harness/pakmod.local.json`, set `work_dir` to a new folder, and pass `--pak-config` to `run.py` and `--config` to `pakmod.py`. This keeps other agents' extracts safe.
