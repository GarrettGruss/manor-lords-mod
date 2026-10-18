# buildmod (plan step 5)

Status: code and fake tests done. The real-game check (acceptance A3) is open.

## How it works
- `pakmod.py buildmod <Name>` reads `mod/<Name>/mod.json` and the patches `data/<feature>/patches/*.json`. Order: feature order of `mod.json`, then file name.
- Checks run before any tool starts: patch format, conflicts, id ranges. A failure names the patch file (conflicts name both files).
- Then, for each table that a patch uses: `extract` from the current game paks, `tojson`, apply the patches, `fromjson --to <Name>`. Then the assets are copied, `build <Name>` runs, and the pak is copied to `mod/<Name>/paks/<Name>_P.pak`.
- The work folder `<work_dir>/<Name>` is wiped at the start, so no stale file stays in the pak.
- Pure logic is in `harness/tools/modpak.py`. The tools are passed in as functions, so tests use fakes (`harness/tests/test_modpak.py`).

## Rules
- Tables: `buildingStats`, `DT_Upgrades` (asset paths in `modpak.TABLES`). Other tables need a new entry and, if rows are added, an `ids` check.
- `add` needs `from` (the row to clone). `set` changes existing fields. A scalar value replaces the field value. A list value rebuilds an array field from its first element.
- Conflict: the same row added twice (any files), or the same field of a row set by two different features. Two patches of one feature may set the same field (the later file wins).
- Id range: every `add` needs a range for its table in the feature's `ids`. Ranges come from spec 23: `buildingStats` blocks of 100 from 1000 (feature 0: 1000 to 1099), `DT_Upgrades` 117 to 999 (feature 0: 117 to 126).
- Two features may not ship the same asset file.

## Not done
- Name-table rows (`DT_Translation_BuildingNames`) are not patchable yet.
- No dry run of the patches without the game (the `--dry-run` flag only prints the plan).
- Real-game check (A3): see below.

## Real-game check of step 5 (A3)
1. Add a second feature to `mod.json` with its own patches (for example one more `buildingStats` row in its range, and a `set` on an existing row).
2. Run `uv run python harness\tools\pakmod.py buildmod InvasionMod` with the game paks present. Expect a pak in `mod/InvasionMod/paks/`, and `build` verified the pak list.
3. Run a scenario with `--pak InvasionMod` (installs the pak). Read the new rows through the bridge (`building_stat`, `upgrade_stat`): row 1000 exists and is visible, upgrade 117 points to 1000, and the set field has the new value. No crash.
4. Plant a conflict and a bad id, and check that the build fails with the file names (fake tests already cover this).
