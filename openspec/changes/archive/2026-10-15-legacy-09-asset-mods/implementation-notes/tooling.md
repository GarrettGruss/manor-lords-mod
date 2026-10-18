# Asset mod tooling (spec 09)

Date: 2026-10-10, branch `feat/15-pak-pipeline-repak`. Replaces the first design (UnrealPak response file), which is removed.
Command line facts: `cli-reference.md`. First check that paks may not be needed: `datatable-check.md`.

## Verified and not verified

| Part | State |
|---|---|
| Config checks, pinned SHA-256 per tool, refusal on a mismatch (exit code 3), `check --pin` | verified with unit tests and fake tools (`harness/tests/test_pakmod.py`) |
| `find` (case-insensitive, 50 results, index cache by size and mtime), `extract` (uasset, uexp, optional ubulk and uptnl), path traversal refusal | verified with a fake repak that reads a JSON fixture format of its own |
| `tojson`, `fromjson`, failures, time limit, empty or missing output, `roundtrip` report (equal, different, first offset) | verified with a fake UAssetGUI (lossless and lossy variants) |
| `build` (layout, `_P` suffix, mount point, pak version, list check, exit code 4 on a mismatch) | verified with the fake repak |
| `install`, `remove`, `list`, manifest rules, `--dry-run`, `--game-dir` | verified in temp folders |
| AES key from an environment variable; never in output, errors, dry-run text, config or work files | verified with the fake tool (the fake echoes its arguments on failure; the key is masked) |
| `uninstall.ps1 -Remove` removes harness paks | verified with a fake game folder (real PowerShell) |
| The real repak and UAssetGUI accept the command lines in `cli-reference.md` | **NOT verified.** Read from source and README only. No tool was downloaded or run |
| `repak pack` output argument is a file path; `V11` is the right pak version for this game | **NOT verified** |
| UAssetGUI `fromjson` writes the `.uexp`; it returns to the shell and sets an exit code | **NOT verified** |
| A round trip of a real 5.5 asset is byte equal, or the result loads in the game | **NOT verified** (the spike decides) |
| The game paks are encrypted; the internal path layout and the mount point `../../../../../docs/` | **NOT verified** |
| The game loads a `_P.pak` from `~mods` and a changed asset shows in the game | **NOT verified** |
| The `.usmap` made by the UE4SS dumper is accepted by UAssetGUI | **NOT verified** |

The fake tools prove the glue code only. They cannot show how the real tools behave.

## Design

- Local config `harness/pakmod.local.json` (gitignored, example: `harness/pakmod.local.example.json`):
  `repak` and `uassetgui` (`path`, `sha256`), `usmap`, `engine_version`, `work_dir`, optional `pak_version` (default `V11`), `mount_point` (default `../../../../../docs/`),
  `aes_key_env` (the NAME of an environment variable), `templates` (argument templates that replace the defaults).
- Every tool call: the file must exist and match the pinned hash (hash remembered per file size and mtime). Then it runs as a list without a shell, with a time limit
  (repak list and get 300 s, pack 300 s, UAssetGUI 120 s). A `.py` tool path is started with the current Python (used by tests only).
- AES key: `--aes-key <key>` is added in front of the repak command only. The key is read from the environment at call time. Messages and tool output are scrubbed of it, and the dry-run command shows `***`.
- Work folder layout: `extracted\<internal path>.uasset|uexp|ubulk|uptnl`, `json\<internal path>.json`, `fromjson\` (default target of `fromjson`) or `<mod name>\` (`fromjson --to`),
  `roundtrip\` (second asset for the comparison), `out\<name>_P.pak`, `.index-cache\<pak name>.json`. These names cannot be used as a mod name.
- `find` searches `*.pak` in `ManorLords\Content\Paks` only (not `~mods`). If several paks hold one asset, `extract` uses the last by name and says so.
- `build` runs `repak pack`, then `repak list` on the result and compares it with the folder. A difference is reported and gives exit code 4.
- Manifest, `install`, `remove`, `uninstall.ps1 -Remove`: unchanged from the first design (`~mods\.harness-paks.json` with `version`, `created_dir`, `files` as name to SHA-256;
  no overwrite of a file that is not in the manifest; remove only when the hash still matches; a path part in an entry is refused).

## Exit codes

0 ok. 1 error. 2 bad command line. 3 a tool does not match its pinned hash. 4 the built pak lists other files than the folder.
`roundtrip` prints "equal" or "different" and exits 0 in both cases.

## Scenario datatable-vanilla (unchanged)

`harness/vanilla/itemStats.json` holds the row count 213 and 24 rows with `Weight`, `Value`, `spoilageRate`, recorded without a pak.
`HARNESS_EXPECT_ITEM_ROWS='{"17": {"Value": 0.75}}'` replaces expected values. Real runs 2026-10-10: `20261010-092110-9587`, `20261010-092200-5e32`, `20261010-092249-590b`, all pass (~49 s).

## What the user must supply

The `repak` and `UAssetGUI` binaries (from their official release pages, reviewed by the user), a `.usmap` from the UE4SS dumper, and possibly the AES key. See `harness/README.md`, section "Asset mods".
Then run the spike (spec 09, implementation plan item 4).
