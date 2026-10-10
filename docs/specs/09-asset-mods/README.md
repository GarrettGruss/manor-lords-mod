# Spec 09: Asset mods (pak editing and repacking)

Status: deferred item on the roadmap, by the user's decision (2026-10-10). The tooling is built and tested with a fake packer.
The real pak build is NOT verified and is not pursued now: it waits for a feature that needs it (see "Deferred roadmap item" below, which lists what it unlocks).

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


## Deferred roadmap item: the real pak build, and what it unlocks
Decision by the user (2026-10-10): the real pak build is NOT pursued now. It stays on the roadmap as a deferred item. Reason: the first features can use Lua and the bridge,
and numbers in the item table can already be changed at runtime (`HarnessDataTable`). The tooling (`pakmod.py`, the uninstall integration, the `datatable-vanilla` scenario) is built and
tested with a fake packer. Only the step with a real packer, a real edited asset and a real game start is missing.

### What a pak build unlocks (capabilities the harness does not have today)
| Capability | Why Lua and the bridge cannot do it | With a pak |
|---|---|---|
| Change data that is not a plain number | The bridge crashes on rows with soft object fields (`getItem`, `RowStruct`). `HarnessDataTable` only writes `Weight`, `Value` and `spoilageRate` | Edit any field of a data table asset: names, text keys, enums, arrays, soft object references, structs such as `BuildingDataStruct` |
| Add or remove rows and tables | A runtime edit cannot change the table layout safely | Add a new item, building or approval factor row, or replace a whole table |
| Changes that apply before the world exists | A runtime edit happens after the load, so initial values and world setup are already done | The edited asset is read when the game loads it, so start values and generation data can change |
| Changes that survive a restart without the harness | A runtime edit is lost when the game closes, and needs UE4SS and the mod to run again | The change is part of the game files until the pak is removed |
| Text and localization | Strings in string tables are not reachable through the reflected API | Replace or add strings (item names, tutorial and message texts, UI text) |
| Visual and audio assets | Not reachable at runtime | Replace textures, materials, meshes, sounds and UI widget assets |
| Blueprint logic and widgets | Reflected Blueprint functions can be hooked, but not rewritten | Replace a Blueprint asset (needs a cooked Blueprint from a UE editor project, which is heavy) |
| Sharing a mod with people who do not use UE4SS | Lua mods need UE4SS to be installed | A pak-only mod works without UE4SS |

### What a pak build does NOT unlock
- Native C++ game logic (per-tick simulation, pathfinding, AI task execution). Only a UE4SS C++ mod can touch it.
- Placing buildings or spawning actors at runtime. Those need runtime tools (the harness has a real-mouse placement action).

### Un-defer triggers (build the real pak chain when one is true)
1. A feature needs a data change that is not a plain number, or a new table row.
2. A feature needs an asset change (texture, mesh, sound, widget, text).
3. A feature must work without UE4SS or without the harness mod running, or must change the world before it is generated.

### What the user must supply (the harness cannot download or run unvetted tools)
- A packer: UnrealPak (from an Unreal Engine install) or `retoc` / `repak`, and its path in the local file `harness/pakmod.local.json` (gitignored).
- An asset extractor and editor: FModel (extract) and UAssetGUI (edit), plus the `.usmap` mapping (the UE4SS dumper makes it).
- The AES key, only if the game paks turn out to be encrypted (not known).
- About one to two hours of setup. After that, the verification chain is: build the pak, install it into `~mods`, run a scenario that reads the changed value (`HARNESS_EXPECT_ITEM_ROWS` in `datatable-vanilla`), run `uninstall.ps1 -Remove`, and check that the game is vanilla again.

### Risks to keep in mind
- A pak changes the game folder (reversible with `pakmod.py remove` and `uninstall.ps1 -Remove`, which delete only manifest-listed files).
- A game update (Early Access) can break a pak. The build number is recorded in each summary.
- A wrong pak can crash the game at start. The harness records that as a crash result and keeps the logs.
- The game has no official mod support. Never commit extracted game assets or keys (the local config file is gitignored).

## Acceptance criteria (for when it is built)
- A trivial asset change (one number in one data row) is built into a pak, deployed, seen by a scenario, and removed by the uninstall script.
  Status: the pieces exist (`pakmod.py`, `datatable-vanilla` with `HARNESS_EXPECT_ITEM_ROWS`, `uninstall.ps1 -Remove`). The whole chain with a real pak is not run.
- The tool refuses to write outside its work folder and the game's `~mods` folder.
- Nothing from FModel exports or AES keys is committed.
