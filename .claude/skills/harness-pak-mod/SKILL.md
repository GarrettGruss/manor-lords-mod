---
name: harness-pak-mod
description: Change game data tables through a repacked .pak (extract, edit JSON, rebuild, install, test with --pak). Use when a value cannot be changed from Lua at run time, or when adding rows, text or units through data.
---

# Pak mods (spec 09)

First check if Lua can do it. A Lua mod can read and write number fields of the item table at run time (`datatable_write`). Use a pak only when it cannot: new rows, text, strings, soft objects, or tables Lua cannot reach.

## What the game gives you
- The game paks are in `...\Manor Lords\ManorLords\Content\Paks\`. All 20 are encrypted (pak V11, mount `../../../`). Original paks are only read, never written.
- A pak you build is unencrypted, named `<name>_P.pak`, and goes to `Paks\~mods\`. The game loads it after the base paks, so its assets replace the originals.
- Data tables are under `ManorLords/Content/NotStronghold/Data/` (`DT_Items`, `DT_UnitTemplates`, `DT_MercenaryCompanies`, `DT_PolicyTypes`, `DT_Upgrades`, `DT_Quests`) and `ManorLords/Content/ManorLords/Database/` (`DT_Alerts`, `DT_Approval`). The list of names is in `docs/harness/10-invasion-testability/implementation-notes/game-data-tables.md`. There is no raid table: raid logic is in code.

## Setup (done on this machine, see `harness/pakmod.local.json`, git-ignored)
- In a worktree, copy `harness/pakmod.local.json` from the main checkout (it is git-ignored).
- repak 0.2.3 (`C:\Program Files\repak_cli\bin\repak.exe`) and UAssetGUI 1.1.0 (`modtools\UAssetGUI.exe`), both pinned by SHA-256 (`pakmod.py check`).
- The `.usmap` mapping comes from the running game (bridge `dump`, kind `usmap`). UAssetGUI 1.1.0 ignores a mapping path: the mapping must be a file in `%LOCALAPPDATA%\UAssetGUI\Mappings\<name>.usmap` (config key `usmap_name`). Make it again after a game update.
- Engine version string is `VER_UE5_5`. JSON paths for the converter must be absolute.
- The AES key is in `modtools\work\aes_key.txt`. In a worktree the file does not exist: use the main checkout path `C:\Users\garre\development\manor-lords-mod\modtools\work\aes_key.txt`. Give it to tools ONLY through the environment variable `MANORLORDS_AES_KEY`, set from that file inside the command. Never print it, write it into a note, a commit, a changelog, a PR or chat. Before every commit: grep the diff for it.

## Commands (`uv run python harness\tools\pakmod.py ...`)
`check [--pin]`, `find <text>`, `extract <asset>`, `tojson`, `fromjson <abs json> --to <name>`, `roundtrip <asset>`, `build <name>`, `install`, `remove [--all]`, `list`, `buildmod <ModName>` (see below). Exit codes: 0 ok, 1 error, 3 hash mismatch, 4 pak list mismatch.

## Working sequence (verified 2026-10-10)
1. `check`, then `roundtrip ManorLords/Content/NotStronghold/Data/DT_Items` (must be byte-equal).
2. Edit the JSON (`Exports[0].Table.Data`), for example item 17 `Value` 0.5 to 0.75.
3. `fromjson <abs path> --to itemvalue17`, then `build itemvalue17`.
4. Run the scenario with the pak: `run.py --scenario datatable-vanilla --pak itemvalue17` with `HARNESS_EXPECT_ITEM_ROWS` set to the new expectation. The run installs the pak and removes it after teardown.
5. Check A and B: with the pak the value is new and the run passes. Without the pak the same expectation fails.

## Traps
- UAssetGUI exits 0 on errors and can write a useless "RawExport" JSON that still round-trips. `tojson` now fails on it. A missing mapping is the usual cause.
- Compiled mod paks (`*_P.pak`) may be committed (user decision 2026-10-13). A mod keeps its pak at `mod/<Name>/paks/<pak>_P.pak`. Original game paks, extracts, `.usmap` files, `modtools/work` files and the AES key stay out of git. Grep the diff for the key before each commit. The work folder is `modtools/work` (git-ignored).
- To put a 3D model in a pak, see skill `harness-meshy` (import, material instance, cook).
- A mod pak for a release stays in `mod/<Name>/paks/` and is named in `mod.json` (skill `harness-release`). A committed pak over 10 MB gives a release warning.
- Spec 18 notes: a pak can add `buildingStats` rows cloned from the tent and retarget a row to another blueprint class (`docs/harness/18-composite-buildings/implementation-notes/composite-pak.md`). Spike #65: `harness/tools/s65_edit_json.py` clones a row (`manor-module-pak.md` in spec 12).
- After a run killed by a timeout, check `pakmod.py list`.
- New rows in `DT_UnitTemplates` and `DT_Items` are proven (spec 29). `harness/tools/clone_table_row.py <json> <source row> <new row> --set f=v --array f=1,2` clones a row. `fromjson --to <name>` writes a flat file name: move the files to the full game path in the work folder before `build`. A `--keep-open` run with `--pak` cannot remove the pak; stop the game and run `pakmod.py remove --all`.
- Only number fields in one table are proven. Test strings, new rows and other tables with a round trip first.

## Widget pak (UI, spec 16)
A cooked Widget Blueprint is a pak too. Sources: mod/InvasionMod/ue/ (copy to the UE workspace C:\Users\garre\development\mlm-ue\ManorLords). Make the asset: UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=make_raid_widget.py (or make_tech_widget.py) -unattended -nullrhi. Cook: -run=cook -targetplatform=Windows -unversioned -nopak -skipeditorcontent (20 s when cached). Copy the cooked .uasset and .uexp into the pak work folder, then run pakmod.py build. Load from Lua with AssetRegistryHelpers:GetAsset. Do not run the editor while a game screenshot is taken. Details: spec 16 policy-menu-followups.md.

## Widget clicks (spec 34)
A Button in our cooked widget has no hookable click (no graph). Use the click button pattern instead. Shared module `mod/shared/HarnessClickHooks` (add `"HarnessClickHooks"` to `shared` in mod.json), pak widget `WBP_ClickButton` (make it with `mod/shared/HarnessClickHooks/ue/make_click_button.py` in the UE workspace, copy the cooked `WBP_ClickButton.uasset` and `.uexp` into every menu pak work folder).
- In the menu script use a `Border` (brush colour alpha 0) where a button belongs. In Lua: `handle = clickhooks.attach(border, controller, {owner = S, ...})` for each button, then ONE `clickhooks.bind_texts(handles)`, then `set_text`, `set_visible`. In the scheduler tick: `for _, h in ipairs(clickhooks.drain(S)) do ... end`. Call `release(handles)` when the menu closes.
- Why a copy: editor Python cannot create graph nodes. The click button is a copy of `/AudioWidgets/AudioButtonToggle/AudioButtonToggle` (its Button01 OnClicked is a UFunction that `RegisterHook` sees). Details and the Lua state finding (do not tick faster than 100 ms, do not rewrite labels each tick, no `FindAllOf` for each button): `docs/harness/34-widget-click-hooks/`.
- Test: scenario `tech-tree-widget-clicks` (real mouse, EXCLUSIVE).

## UI art (images for a widget pak)
- Make images with `uv run python harness/tools/genimage.py --prompt "..." --out <file.png>` (Gemini API, key from `GEMINI_API_KEY`; never print it). `--list-models` shows the image models. Every call is logged in `runs/genimage/log.jsonl`; keep a set small and check the spend.
- Keep one shared style prompt per art set (see `harness/tools/make_policy_art.py`). Ask for "no text, no letters": the model still writes words sometimes, so look at every image.
- Review a set with `harness/tools/contact_sheet.py OUT.png IN...` and read the sheet.
- Originals stay in `runs/genimage/` (git-ignored). Commit only resized copies in `mod/<Name>/art/`. `art/`, `ue/` and `paks/` are not deployed and not zipped.

## Generated meshes (spec 21)
Workflow verified 2026-10-14 (note `docs/harness/21-mesh-generation/implementation-notes/spike-a-ladder.md`):
1. Two reference views with `genimage.py` (plain background, no ground, no text). Then `uv run python harness/tools/genmesh.py multi --image a.png --image b.png --out runs/genmesh/<name> --polycount 2000` (key `MESHY_API_KEY`, never printed; caps 60 per call and 200 per day; log `runs/genmesh/log.jsonl`; `genmesh.py balance` shows credits). One textured call costs 30 credits.
2. Import headless in the UE workspace: copy `mod/HarnessActions/ue/import_mesh.py`, set `MESH_FBX` and `MESH_NAME`, run `UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=import_mesh.py -unattended -nullrhi`. It logs size (cm), vertices and material. It caps textures (1024 colour and normal, 512 others) to keep the pak near 3 MB.
3. `make_bm.py` with `BM_NAME` and `BM_PARTS` (JSON list of `[component name, mesh path, [x,y,z], [sx,sy,sz]]`). Use the prefixes `MainBld_`, `Bld_`, `clutter_`, `res_`.
4. Cook (`-run=cook -targetplatform=Windows -unversioned -nopak -skipeditorcontent`), copy `BM_*` and `Meshes/` into `modtools/work/<pak>/ManorLords/Content/HarnessMod/`, add a `buildingStats` row (`s65_edit_json.py stats`, `blueprint`, `visible`) with a free id, `pakmod.py fromjson --to <pak>`, `pakmod.py build <pak>`.
5. Run `run.py --scenario noop --keep-open --pak <pak>`, then `s94_drive.py` (`camera`, `ghost`, `place`, `days`), `s21_locate.py` and `s21_view.py` (wheel zoom and screenshot). Place only on a WHITE ghost. Close the game, then `pakmod.py remove --all`.

## Mod pack pak (spec 22)
`pakmod.py buildmod <ModName>` builds `mod/<ModName>/paks/<ModName>_P.pak` from `mod/<ModName>/data/<feature>/patches/*.json` (patch format: spec 22 README) and `data/<feature>/assets/**`. It extracts the tables from the current game paks each time. It fails with the file names on a bad patch, a conflict (same row added, same field set by two features) or a new row outside the feature's `ids` range in `mod.json`. Tables: `buildingStats`, `DT_Upgrades`. Logic: `harness/tools/modpak.py`. Notes: `docs/harness/22-mod-pack-layout/implementation-notes/buildmod.md`.

### Camp or prop without a menu card (spec 30)
- To change how the game's own spawn looks, retarget the row, not the class: `s65_edit_json.py blueprint <json> 100 /Game/HarnessMod/BM_X BM_X_C` makes every bandit camp use `BM_X` (and saved camps follow at load). The tent class `BM_HomelessTents` stays untouched.
- To show a mesh in neutral or AI land, use `load_pak_blueprint` then `encampment_spawn` (a plain actor, not saved by the game). `encampment_sites` reads camp masters, `encampment_regions` the region points. Probe: `probe-wagenburg`. Notes: `docs/harness/30-wagenburg-encampment/`.

### Meshy mesh looks flat grey (spec 33)
Cause: a material cooked in the mod project has no shader code in the pak (the code is in a shader library file that is not shipped), so the game draws a fallback grey. Fix: the import scripts now call `mod/HarnessActions/ue/meshy_material.py`. It makes `MI_Meshy`, an instance of the game master `/Game/NotStronghold/Buildings/TudorWall/tudorWall01` (params `d`, `n`, `AO`, `spec`), and a stub master (never shipped). Copy to the UE workspace with the import scripts. Pak only `MI_Meshy`, the mesh, `texture_0`, `texture_0_normal`, `texture_0_roughness`. Fix an old import with `retarget_material.py` (`MESH_PATH`). Notes: `docs/harness/33-meshy-materials/implementation-notes/cause-and-fix.md`.
