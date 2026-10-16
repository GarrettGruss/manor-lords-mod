# Spec 22: Mod pack layout (one mod, many features)

Status: approved (2026-10-15). Real-game checks of step 3 and A3 passed (2026-10-16): see implementation-notes/real-game-checks.md. Plan steps 3, 4, 6 and 7: see implementation-notes/skeleton.md. Step 5: see implementation-notes/buildmod.md. Issue: #126. Branch: `feat/22-mod-pack-layout`.

## Goal
Set up the repo so that the agent can build the Invasion Mod as one mod made of separate features (for example invasion, refugees, tech tree, and more later).
Each feature will grow with player feedback and iterations. The layout must let a feature grow, and let new features be added, without a change to the layout.
The harness must stay apart from the mod, so it can move to its own repo and be shipped later.

Decisions taken with the user (2026-10-15):
- One repo for now. The harness and the mod are split by folders and by rules, not by repos.
- Two doc tracks:
  - harness specs in `docs/harness/<NN>-<name>/` (the specs 00 to 21 moved there from `docs/specs/`);
  - mod docs in `docs/mod/` (index `docs/mod/README.md`, overview design `docs/mod/M00-invasion-mod/`).
- The mod ships as ONE pak and ONE Lua mod. Features are separate in the source and are merged at build time.
- `InvasionMod` is the internal name (folders, code, pak, tags). The player-facing name will change later. It lives only in `mod.json` (`display_name`).
- The `refugees` feature is built new from its own mod spec. `mod/RefugeeWaves` stays as it is, as a reference example (spec 15, #51).
- Game updates: every mod build starts again from the current game paks (old Q3, approved).

## Non-goals
- No split into two repos now. No Python package or Claude Code plugin for the harness now (later spec).
- No player toggle of the data part of a feature. Data rows of all features are always in the pak (see "Feature toggles").
- No load-order handling between several mod paks. There is only one mod pak.
- No Nexus Mods or Steam Workshop upload (spec 19 non-goal stays).
- No game design content. The user writes the design docs in `docs/mod/`.

## Why one pak
A pak replaces whole asset files. A data table edit rebuilds the full `.uasset` (for example `buildingStats` or `DT_Upgrades`).
If two feature paks change the same table, the game uses only one of them, and the rows of the other are lost with no error.
The features will touch the same tables (a tech tree changes `DT_Upgrades` and `buildingStats`). So feature paks would need a merge step anyway.
One pak gives one build, one install file and one hash for the release gate.

## Layout
```
mod/InvasionMod/
  mod.json                      spec 19 manifest, plus "display_name" and "features" (see below)
  CHANGELOG.md                  one changelog; each entry names its feature
  Scripts/
    main.lua                    loads ManorCore, the config and each enabled feature
    config.lua                  feature on/off and tunables (balance values) for each feature
    features/<feature>/init.lua the logic of one feature (more files when it grows)
  data/<feature>/
    patches/*.json              row patches for game tables (see "Row patches")
    assets/                     cooked assets (meshes, BM_ classes, widgets), copied into the pak
  scenarios/<feature>/*.py      real-game scenarios of the feature
  paks/InvasionMod_P.pak        the built pak (committed, AES key rules apply)
```
- `<feature>` is the same name in `Scripts/features/`, `data/`, `scenarios/` and in the mod docs. One name, used everywhere.
- A release copies `Scripts/` and the pak only. `data/` and `scenarios/` never go into a release.
- `RaidStandIn`, `InvasionStandIn`, `RefugeeWaves` and the other stand-ins stay where they are. They are not part of the mod.

## Rules that let a feature grow
1. **Feature boundary.** A feature uses `ManorCore`, its own files and the declared API of other features. It never reads another feature's local state.
   A dependency is listed in `mod.json` (`features[].requires`, may be empty). `main.lua` loads features in dependency order and fails loudly on a cycle or a missing feature.
2. **Tunables in config.** Every balance value is in `config.lua` under the feature name, not in the logic. Player feedback mostly changes numbers. A tuning change is then a config change with a clear diff. Scenarios set tunables through a named command (as `RefugeeWaves.configure` does today).
3. **Reserved id ranges.** Each feature gets a block of ids for new rows in each table. The ranges are in `mod.json`. The build fails when a patch uses an id outside its feature's range. The safe id values come from spec 23 (row id range spike).
4. **No hidden save state.** A feature keeps no state that the game cannot rebuild after a load (the RefugeeWaves rule). If a feature must keep state, its spec says how, before the code.
5. **Iterations, not rewrites.** A feature grows by iterations. Each iteration has its own file in the feature's mod spec (see `docs/mod/README.md`) with acceptance criteria and scenarios.
6. **One mod version.** The mod has one semver version. A release is gated on the scenarios of ALL enabled features (spec 19 gate).
7. **No player-facing name in code.** Text for players comes from `display_name` or from text rows, so a rename touches one place.

## Row patches
A row patch is a small JSON file that names a table, a row and the fields to set or add. Example:
```json
{ "table": "buildingStats", "row": "125", "op": "add", "from": "97",
  "set": { "stableSpace": 4, "visible": true } }
```
- Ops: `add` (new row, optionally cloned `from` a row), `set` (change fields of an existing row). `remove` is not supported in v1.
- The build reads the original tables from the current game paks (pakmod extract), applies all patches of all features in a fixed order (feature order of `mod.json`, then file name), writes the tables and builds one pak. The run summary records the game build.
- **Conflict check:** the build fails when two features set the same field of the same row, or add the same row. The message names both patch files. This is the guard against the silent overwrite.
- The existing helpers (`s65_edit_json.py`, `pakmod.py fromjson` and `build`) do the low-level work. The new part is reading patches and the conflict check.

## Feature toggles
- `config.lua` turns the logic of a feature on or off. A disabled feature's data rows stay in the pak.
- A disabled feature that adds a visible row (for example a building card) must hide it from Lua, or the feature spec must say why the row is harmless. For v1 the mod is tested with all features on.

## Plan (small steps, each one commit or more)
1. Doc tracks: move the harness specs to `docs/harness/` (done), add `docs/mod/README.md` (how mod docs are written) and `docs/mod/M00-invasion-mod/README.md` (overview design scaffold for the user).
2. CLAUDE.md and skills: doc paths, mod doc rules, branch names (`feat/M<NN>-<feature>-<iteration>`), the feature rules above.
3. Skeleton: `mod/InvasionMod/` with `mod.json`, `main.lua`, `config.lua`, the feature loader, one stub feature, and a fake-game test for the loader (order, cycle, missing feature, disabled feature). Check in the real game that `require` of a feature module under `Scripts/features/` works.
4. Harness: scenario discovery also reads `mod/<Name>/scenarios/**`. Scenario names stay unique.
5. (code done, A3 open) Harness: `pakmod.py buildmod InvasionMod` applies the row patches, runs the conflict and id-range checks, copies `data/*/assets`, builds `paks/InvasionMod_P.pak`. Fake tests for the patch rules. Needs spec 23 for the id ranges.
6. Release (spec 19): manifest fields `display_name` and `features`; gate over all features' scenarios; the zip leaves out `data/` and `scenarios/`.
7. Boundary check: a test fails when code under `harness/` names `InvasionMod` or a feature. The harness finds the mod only through `mod.json` and paths.

The features themselves (invasion, refugees, tech tree) are not in this spec. They start when the user's design docs in `docs/mod/` are broken out into feature specs.

## Manifest additions (`mod.json`)
```json
{
  "name": "InvasionMod",
  "display_name": "Invasion Mode",
  "version": "0.1.0",
  "pak": { "name": "InvasionMod", "source": "file" },
  "features": [
    { "name": "example", "requires": [], "ids": { "buildingStats": [0, 0] } }
  ],
  "gate_scenarios": []
}
```
Id ranges (spec 23): ids 1 to 485 are vanilla or enum range (keep free, also 200, 255, 256). Each feature gets a block of 100 ids in `buildingStats`, start = 1000 + 100 * feature number (feature 0: `[1000, 1099]`). `DT_Upgrades` new rows use 117 to 999 (feature 0: `[117, 126]`). Ids above 32767 are not used. The key in `ids` is the table name of the patch.

## Open questions
- Q1 (decided 2026-10-15): keep `requires`, allow it empty.
- Q2: which row ids are safe for new rows. Moved to spec 23 (`docs/harness/23-row-id-range/`).
- Q3 (decided 2026-10-15): every build starts from the current game paks.
- Q4 (decided 2026-10-15): `refugees` is built new; RefugeeWaves is a reference. The `require` check stays in plan step 3.
- Q5 (decided 2026-10-15): `InvasionMod` is the internal name; the player name is `display_name` and will change.

## Acceptance criteria
- A1: `mod/InvasionMod/` exists with the layout above, and the loader fake test passes (order, cycle, missing, disabled).
- A2: The skeleton with one stub feature loads in the real game: the stub feature logs through `HarnessLog`, and a scenario checks it.
- A3: `pakmod.py buildmod InvasionMod` builds one pak from patches of at least two features, and the pak loads in the real game (rows read through the bridge).
- A4: A planted conflict (two features set the same field) makes the build fail with both file names. A patch outside its id range makes the build fail.
- A5: `release.py --mod InvasionMod --dry-run` builds one zip with `Scripts/` and the one pak, and without `data/` and `scenarios/`.
- A6: The boundary test passes: no harness code names the mod.
- A7: CLAUDE.md and the skills describe the two doc tracks and the feature rules.
