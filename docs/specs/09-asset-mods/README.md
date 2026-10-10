# Spec 09: Asset mods (pak editing and repacking)

Status: tooling built and tested with a fake packer. A real pak build is **not verified**: it needs UnrealPak or `retoc`, an edited asset and possibly the AES key. Only the user can supply them.
No planned feature needs a pak yet, so the "when to build" rule below still applies before anyone edits a real asset.
Notes: `implementation-notes/tooling.md`.
Roadmap phase: 11 (see `docs/specs/00-harness-overview/README.md`).

## Goal
Change game data that Lua cannot reach (data tables, assets) by editing and repacking `.pak` files, and test the change with the same harness.

## When to build this
Build it only when a feature spec shows that the data cannot be changed at runtime. Check this first, in order:
1. Can a Lua mod set the value at runtime (a reflected property, a `DataTable` row that is readable and writable through UE4SS)?
2. Can a Blueprint mod loader mod (UE4SS) change it?
3. Only then: edit the asset in a pak.

## Non-goals
- Replacing the Lua path. Lua stays the first choice.
- Shipping or distributing mods. This is for testing.

## Background (from the project plan, not verified here)
- Data and assets are in `.pak` files. Tools: FModel (browse and export, needs the AES key), UAssetGUI (edit assets, needs the `.usmap` mapping from UE4SS), UnrealPak or `retoc` (repack).
  A repacked pak goes to `ManorLords\Content\Paks\~mods\`.
- UE4SS can dump the `.usmap` (done with the Dumpers tab; the jmap dump in this repo already has the types).
- Item data is a `DataTable` (`RTSMultiEngineCPP.itemStats`, struct `Item`). Reading and writing its rows at runtime may be possible through UE4SS. Test this before any pak work.
- The game is single-player. A pak mod changes files in the game folder, so the harness must deploy and remove it like it does for Lua mods (`deploy.ps1`, `uninstall.ps1`).

## Design (when needed)
1. `reference/` is not in git. Exports from FModel go to a local folder named in a settings file, never into the repo.
2. A tool `harness/tools/pakmod.py build <name>` takes a folder of edited assets (`mod-assets/<name>/`) and calls the pak tool to make `<name>_P.pak`.
   The tool paths come from a local config file (not committed).
3. `deploy.ps1` copies `<name>_P.pak` to `~mods` and records it in the manifest. `uninstall.ps1` removes it.
4. A pak change needs a game restart. The run launcher already restarts the game for each run, so a scenario sees the change.
5. A scenario verifies the change by reading the data at runtime (through the bridge) and comparing with the vanilla value.

## Decision log
- 2026-10-10: deferred. Reason: the first features can use Lua and the bridge. No asset change is needed.
- First check before building: read and write a `DataTable` row at runtime. If that works, most "data mods" do not need paks.
- 2026-10-10: first check done (`implementation-notes/datatable-check.md`). In the real game a Lua mod read 213 rows of `RTSMultiEngineCPP.itemStats` (`GetRowNames`, `FindRow`)
  and changed the number field `Value` of row 17 (0.5 -> 0.75, read back, restored to 0.5). So paks are still **not needed** for number changes. Spec 09 stays deferred.
  Limits found: the bridge cannot read rows (`RowStruct` read and `getItem` crash the game, because `Item` has a `SoftClassProperty`), so rows are read by field name in a Lua mod only.
  Not verified: that game logic uses the changed value, persistence over a new load, strings and soft fields.

- 2026-10-10: tooling built in `feat/11-asset-mod-tool` (`harness/tools/pakmod.py`, `uninstall.ps1 -Remove` removes harness paks, scenario `datatable-vanilla`). Verified with a fake packer and temp folders, and `datatable-vanilla` passed 3 of 3 in the real game (no pak). NOT verified: a real packer, a real edited asset, a real pak in the game. The decision "Lua first" is unchanged.
  `deploy.ps1` is not changed: `pakmod.py install` does the copy and writes its own manifest (`~mods\.harness-paks.json`), because a pak is built outside the repo.

## Acceptance criteria (for when it is built)
- A trivial asset change (one number in one data row) is built into a pak, deployed, seen by a scenario, and removed by the uninstall script.
  Status: the pieces exist (`pakmod.py`, `datatable-vanilla` with `HARNESS_EXPECT_ITEM_ROWS`, `uninstall.ps1 -Remove`). The whole chain with a real pak is not run.
- The tool refuses to write outside its work folder and the game's `~mods` folder.
- Nothing from FModel exports or AES keys is committed.
