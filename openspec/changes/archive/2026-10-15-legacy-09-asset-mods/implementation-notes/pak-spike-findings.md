# Pak spike findings (2026-10-10)

Branch `feat/22-pak-spike`. Tools: repak 0.2.3, UAssetGUI 1.1.0 (UAssetAPI 8b8687a). Game build 25598558, UE 5.5.4.
The AES key is never written here. It sits in the git-ignored `modtools/work/aes_key.txt`. Commands use `<KEY>`.

## Result
The whole chain works on the real game:
find, extract, tojson, edit one number, fromjson, build, install, run, remove.
- Round trip of `DT_Items` (213 rows): `.uasset` (27800 bytes) and `.uexp` (34089 bytes) are byte-identical after `tojson` then `fromjson`.
- A pak with `DT_Items` where row 17 `Value` is 0.75 (vanilla 0.5) was loaded by the game. Scenario `datatable-vanilla` with the pak: pass, `item 17 Value value=0.75` (run `20261010-190411-ad07`, 54.5 s).
- Same scenario and same expectation without the pak: fail, `item 17 Value value=0.5` (run `20261010-190516-991a`, 49.0 s). This is the A/B.
- After the run `pakmod.py list` shows no pak, and `~mods` is removed again. The run summary says: "the user's save files did not change".

## What the game needs
No variant was needed. The first pak worked:
- Pak version V11, mount point `../../../../../docs/`, no compression, NOT encrypted (`repak info`: `encrypted index: false`). The game paks are encrypted, but the game accepts a plain pak.
- File name `itemvalue17_P.pak` in `ManorLords\Content\Paks\~mods\`.
- Internal paths `ManorLords/Content/NotStronghold/Data/DT_Items.uasset` and `.uexp`.
- `repak pack` with `--aes-key` before the command still writes an unencrypted pak.

## Problems found and fixed
1. The mapping. UAssetGUI 1.1.0 ignores a mapping PATH and an unknown mapping name. It exits with 0 and writes a "RawExport" JSON (140 KB, no fields). A round trip of that JSON is also byte-equal, so it looks fine but is useless.
   Fix: the `.usmap` must be a file in `%LOCALAPPDATA%\UAssetGUI\Mappings\<name>.usmap`, and the command gets the name. Setting `LOCALAPPDATA` for the process does not help. Config key `usmap_name` (new). `check` and every convert compare both files by SHA-256. `tojson` fails if the output has a `RawExport`.
   This copy is a change outside the repo (the tool's own settings folder). The user should know it.
2. The engine version. `5.5` makes `tojson` write no file (exit 0). `VER_UE5_5` works. The default is changed.
3. The bridge MCP server could not reach a game started by `run.py --keep-open` (the run uses its own bridge folder). The `.usmap` was made with `ue4ss_bridge.server.one('dump', timeout=600, kind='usmap')` and `UE4SS_BRIDGE_GAME_DIR` and `UE4SS_BRIDGE_DATA_DIR` set. It took under 1 minute. The file lands in `ue4ss\` as `ManorLords-5.5.4-40574608+++UE5+Release-5.5-5e627997.usmap` (2.4 MB).
4. `fromjson` and `tojson` need an absolute JSON path (a relative path from the repo root was refused).

## Working commands
PowerShell, repo root. The key comes from the file into the process environment only.
```
$env:MANORLORDS_AES_KEY = (Get-Content modtools\work\aes_key.txt).Trim()
$py = ".venv\Scripts\python.exe"
$a  = "ManorLords/Content/NotStronghold/Data/DT_Items"
& $py harness\tools\pakmod.py check
& $py harness\tools\pakmod.py find DT_Items
& $py harness\tools\pakmod.py roundtrip $a            # extract + tojson + fromjson + byte compare
# edit <work_dir>\json\...\DT_Items.json: Exports[0].Table.Data, row Name "17", property "Value": 0.5 -> 0.75
& $py harness\tools\pakmod.py fromjson <ABSOLUTE-PATH-TO>\DT_Items.json --to itemvalue17
& $py harness\tools\pakmod.py build itemvalue17        # -> <work_dir>\out\itemvalue17_P.pak
$env:HARNESS_EXPECT_ITEM_ROWS = '{"17": {"Value": 0.75}}'
& $py harness\run.py --scenario datatable-vanilla --pak itemvalue17    # installs, runs, always removes
& $py harness\tools\pakmod.py list                     # none
```
Raw commands behind it (with `<KEY>`):
```
repak --aes-key <KEY> list <pak>
repak --aes-key <KEY> get -s ../../../ <pak> ManorLords/Content/NotStronghold/Data/DT_Items.uasset
UAssetGUI tojson <DT_Items.uasset> <out.json> VER_UE5_5 ManorLords
UAssetGUI fromjson <out.json> <DT_Items.uasset> ManorLords
repak pack --mount-point ../../../ --version V11 <folder> <name>_P.pak
```

## Timings
| Step | Time |
|---|---|
| `find` over all paks (cached index) | a few seconds |
| `roundtrip` DT_Items | 2.2 s |
| `build` | 0.13 s |
| `datatable-vanilla` run | 49 to 55 s |
| `.usmap` dump | under 1 minute |

## Data table names
Notes: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/game-data-tables.md`. There is no `DT_units`. The unit tables are `DT_UnitTemplates` (and `DT_UnitTemplates_OLD`) and `DT_MercenaryCompanies` in `pakchunk0_s11`. No table has `Raid`, `Bandit` or `Squad` in its name.

## Runs used
3 runs: `noop` with `--keep-open` (for the dump), the A run, the B run. The counter was 85 before and is 88 now.

## Not verified / open questions
- Only a number field was changed. Strings, arrays, soft object fields and new rows are not tried. DT_Items has soft fields; the JSON edit of those is not tested.
- Only one table (`DT_Items`) was round-tripped. Other tables (`DT_UnitTemplates`) are not tried.
- A/B was one run per side, not N runs. The suite-based A/B report with `variants` is not run on a real pak.
- Whether a Steam game update keeps the mapping valid: the `.usmap` must be made again after an update.
- UAssetGUI 1.1.1 or later may accept a mapping path and `5.5`. Not tried (no download).
- Crash behavior of a wrong pak is not tried.
