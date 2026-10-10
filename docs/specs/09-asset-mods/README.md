# Spec 09: Asset mods (pak editing and repacking)

Status: deferred. No planned feature needs it yet. This spec records when to build it and how to test it with the harness.
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

## Acceptance criteria (for when it is built)
- A trivial asset change (one number in one data row) is built into a pak, deployed, seen by a scenario, and removed by the uninstall script.
- The tool refuses to write outside its work folder and the game's `~mods` folder.
- Nothing from FModel exports or AES keys is committed.
