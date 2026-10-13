# Spec 09: Asset mods (pak editing and repacking)

Status: in progress (since 2026-10-10). The user decided on the toolchain (repak and the UAssetGUI command line) and asked to begin implementation.
The tooling is built and tested with fake tools. The real chain is VERIFIED by the first spike (2026-10-10, `implementation-notes/pak-spike-findings.md`): a round trip of `DT_Items` is byte-identical, a pak with one changed number is loaded by the game, and the A/B with `--pak` shows the change.
Still open: other field types (strings, soft objects, new rows), other tables, and an A/B with N runs per side (needs the game; no real A/B suite ran yet).

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

## Toolchain decision (2026-10-10, by the user)
| Layer | Tool | Role |
|---|---|---|
| Archive (`.pak`) | **repak** (github.com/trumank/repak), command line | `list`, `info`, `get` (one file), `unpack`, `pack <folder>`, `hash-list`. Reads encrypted paks with `--aes-key`. Pak versions up to 11 |
| Asset (`.uasset`, `.uexp`, `.umap`) | **UAssetGUI**, command line | `tojson <asset> <json> <engine version> [mappings]` and `fromjson <json> <asset> [mappings]`. It converts ONE asset. It does not read or write `.pak` files |
| Mapping | A `.usmap` file | Made by the UE4SS dumper (the bridge has a `dump` tool). Passed to UAssetGUI. Must match the game build |
| Test and verification | This harness | Scenarios, telemetry, suites, and (new) A/B variants |
| Glue | `harness/tools/pakmod.py` | Finds, extracts, converts, round-trips, builds, installs and removes |

Why repak and not the alternatives:
- **Epic's UnrealPak** is the reference tool, but it only ships inside an Unreal Engine install (multi-gigabyte). It stays an option as a cross-check, and as the packer if UE 5.5 is installed for level C work.
- **The third-party repository `allcoolthingsatoneplace/UnrealPakTool`** (a copy of UnrealPak 4.27 binaries committed by a third party) is **rejected**: the binaries cannot be verified (no releases, no hashes, the README links to another owner), it is a 4.27 tool for a 5.5.4 game, and redistributing Epic binaries has an unclear license.
- **retoc** is for IoStore (`.utoc`/`.ucas`). The game uses plain `.pak` files.
- **FModel** is optional: useful for a person to browse assets. It is not part of the agent loop.

Rules for third-party tools: the user places the binaries (or approves a download from the official release page). `pakmod.py check` pins the SHA-256 of each tool in the local config
and refuses to run a tool whose hash differs. Tools run without a shell, with a time limit, and never with a path outside the work folder and the game's `~mods` folder.

## Pipeline (the agent loop)
1. `pakmod find <asset>`: search the pak indexes of the game (`repak list` on each pak) and say which pak holds the asset. The jmap gives the package path of a DataTable.
2. `pakmod extract <asset>`: `repak get` the `.uasset` and its `.uexp` into the work folder (never unpack a whole 700 MB pak).
3. `pakmod roundtrip <asset>`: convert to JSON and back with UAssetGUI and compare with the original. Edit only when this matches (or the result still loads in the game).
4. The agent edits the JSON (a text diff shows the change), and `pakmod fromjson` writes the asset.
5. `pakmod build <name>`: build a folder with the game's exact internal path layout and run `repak pack`. The output is `<name>_P.pak` (the `_P` suffix gives it load priority).
6. `pakmod install <name>`: copy it to `ManorLords\Content\Paks\~mods\` and record it in the manifest.
7. `run.py --pak <name> --scenario <s>`: run the scenario with the pak installed for the run (installed in preflight, removed in teardown).
8. Compare. For A/B: a suite entry with `"paks": ["name"]` and the same entry without paks, N runs each (see spec 08). The report shows both groups.
9. `pakmod remove <name>` or `uninstall.ps1 -Remove`: back to vanilla.

## Implementation plan (2026-10-10)
1. Spec update. Done in this change.
2. Done (2026-10-10, fake tools only). `pakmod.py` for repak and UAssetGUI: config with pinned hashes, `check`, `find`, `extract`, `tojson`, `fromjson`, `roundtrip`, `build` (folder and `repak pack`), `install`, `remove`, `list`. Unit tests with fake tools (small scripts that mimic the command lines). The old response-file packer path is removed.
3. Done (2026-10-10, fake runs only). `run.py --pak <name>` (install in preflight, always removed after teardown; install code shared in `harness/runlib/paks.py`) and suite variants with an A/B report (spec 10, U4; `docs/specs/10-invasion-testability/implementation-notes/ab-statistics.md`). Not verified: a real pak in a real run.
4. Spike with the real tools (needs the user): repak and UAssetGUI in place, a `.usmap` made, then: find and extract `DT_units` (or another small table), round trip it, change one number, build and install a pak, run `datatable-vanilla` with the expected new value (`HARNESS_EXPECT_ITEM_ROWS` or its successor), run the A/B comparison, and remove the pak. Record the evidence in `implementation-notes/`.
5. Docs, README, changelog.

Open questions for the spike: the game's pak version, whether the game paks are encrypted, whether UAssetGUI round-trips this game's 5.5 assets and how it treats `.uexp`, the exact internal path layout and mount point, and whether the game loads a `_P.pak` from `~mods`.

## Decision log
- 2026-10-10: deferred. Reason: the first features can use Lua and the bridge. No asset change is needed.
- First check before building: read and write a `DataTable` row at runtime. If that works, most "data mods" do not need paks.
- 2026-10-10: first check done (`implementation-notes/datatable-check.md`). In the real game a Lua mod read 213 rows of `RTSMultiEngineCPP.itemStats` (`GetRowNames`, `FindRow`)
  and changed the number field `Value` of row 17 (0.5 -> 0.75, read back, restored to 0.5). So paks are still **not needed** for number changes. Spec 09 stays deferred.
  Limits found: the bridge cannot read rows (`RowStruct` read and `getItem` crash the game, because `Item` has a `SoftClassProperty`), so rows are read by field name in a Lua mod only.
  Not verified: that game logic uses the changed value, persistence over a new load, strings and soft fields.

- 2026-10-10: tooling built in `feat/11-asset-mod-tool` (`harness/tools/pakmod.py`, `uninstall.ps1 -Remove` removes harness paks, scenario `datatable-vanilla`). Verified with a fake packer and temp folders, and `datatable-vanilla` passed 3 of 3 in the real game (no pak). NOT verified: a real packer, a real edited asset, a real pak in the game. The decision "Lua first" is unchanged.
  `deploy.ps1` is not changed: `pakmod.py install` does the copy and writes its own manifest (`~mods\.harness-paks.json`), because a pak is built outside the repo.


- 2026-10-10: the user chose repak as the packer and the UAssetGUI command line for assets, and asked to begin implementation. The earlier decision to defer the real pak build is replaced by this one (the deferred item is now in progress). The third-party `UnrealPakTool` repository was reviewed and rejected (see the toolchain decision).

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

## Acceptance criteria
- [x] (new) `pakmod roundtrip` shows that an untouched asset survives `tojson` then `fromjson`, or that the result still loads in the game. Proven for `DT_Items` (byte-identical, 2026-10-10).
- [x] (new) A trivial pak built with repak is installed in `~mods`, the game starts, and a scenario sees the changed value. Proven: item 17 `Value` 0.75 (run `20261010-190411-ad07`).
- [ ] (new) An A/B comparison (same scenario, with and without the pak, N runs each) shows the difference in the report, and `pakmod remove` returns the game to vanilla. Partly proven: one run per side differs (0.75 vs 0.5) and the pak is removed after the run. N runs with the suite report are not done.
- (old criteria, still valid):
- A trivial asset change (one number in one data row) is built into a pak, deployed, seen by a scenario, and removed by the uninstall script.
  Status: the whole chain ran with a real pak on 2026-10-10 (`pak-spike-findings.md`). `uninstall.ps1 -Remove` is not run on a real pak (`run.py` removed it).
- The tool refuses to write outside its work folder and the game's `~mods` folder.
- Nothing from FModel exports or AES keys is committed.
