# Asset mod tooling (spec 09)

Date: 2026-10-10, branch `feat/11-asset-mod-tool`.

## Verified and not verified

| Part | State |
|---|---|
| `pakmod.py` config check, name and path guards, response file, command construction, packer failure and timeout | verified with unit tests and a fake packer (`harness/tests/test_pakmod.py`) |
| `install`, `remove`, `list`, manifest rules, `--dry-run` | verified with unit tests in temp folders |
| `uninstall.ps1 -Remove` removes harness paks | verified with a fake game folder (real PowerShell run in the test) |
| Scenario `datatable-vanilla` in the real game | verified: 3 runs, all pass (see below) |
| A real packer (UnrealPak, `retoc`) accepts the response file format and makes a pak the game loads | **NOT verified.** No tool is installed |
| Response file format `"<file>" "<mount path>"` and mount point `../../../` | **NOT verified.** Taken from the UnrealPak convention (from memory), not checked against a tool |
| The game loads a `_P.pak` from `~mods` and a changed `DT_Items` shows in `itemStats` | **NOT verified** |
| AES key need | **NOT verified.** Unknown whether the shipped paks are encrypted. A key is needed to read them, probably not to add a patch pak |
| A symlink in the asset folder is refused | the test is skipped when the system does not allow symlinks (it was skipped on this machine) |
| Nothing was installed into the real game `Paks` folder | true; all tests use temp folders |

## Design

- Local config `harness/pakmod.local.json` (gitignored): `packer`, `packer_args` (a list with `{response}` and `{output}`), `work_dir`.
  `check` lists each missing part. It does not run the packer.
- `build <name>` uses `<work_dir>\<name>\` (edited asset files). It writes `<work_dir>\out\<name>.response.txt` (one line per file: full path and mount path `../../../<relative path>`),
  runs the packer as a list without a shell (limit 300 s), and expects `<work_dir>\out\<name>_P.pak`. A packer that exits 0 without a pak is an error.
- `install <name>` copies the pak to `<game>\ManorLords\Content\Paks\~mods\`, checks the copy hash, and records it in `~mods\.harness-paks.json`
  (`{"version":1,"created_dir":bool,"files":{"<name>_P.pak":"<SHA-256>"}}`). It refuses to overwrite a file that is not in the manifest.
- `remove` deletes only manifest files, only when the SHA-256 still matches. A changed file is skipped with a message. A manifest entry with a path part is refused.
  The `~mods` folder is removed only if the harness created it and it is empty.
- `deploy.ps1` is not changed (decision: a pak is built outside the repo, so `pakmod.py install` is the deploy step).
- `uninstall.ps1 -Remove` has the same rules in PowerShell (plain pak file name, inside `~mods`, hash must match, pak manifest kept if a file was skipped).
  Default mode (disable) does not touch paks.

## Scenario datatable-vanilla

- `harness/vanilla/itemStats.json` holds the row count 213 and 24 rows (every second existing id from -1 to 120) with `Weight`, `Value`, `spoilageRate`.
  It was recorded once with the hidden scenario `datatable-record` in the real game without a pak. The values match the earlier check (row 16 Value 0, row 17 0.5, row 1 1.5).
  `Weight` is 0 in all recorded rows.
- The scenario reads each field through `ctx.actions.datatable_read` and compares with tolerance 1e-4 (73 checks: row count and 72 fields).
- `HARNESS_EXPECT_ITEM_ROWS='{"17": {"Value": 0.75}}'` replaces the expected values of single fields. Use it for a pak that changes them.
- Real runs, 2026-10-10: `20261010-092110-9587` 49.1 s, `20261010-092200-5e32` 48.7 s, `20261010-092249-590b` 48.6 s. All pass. The scenario phase takes about 14.6 s.
- The user save folder guard of the launcher reported no change.

## Bug found and fixed on the way

The first recording run (122 row reads) failed with `PermissionError` when Python read a result file while the mod still held it open.
`CommandChannel` now retries on `PermissionError` and on partial JSON until the timeout (`_read_answer`).

## What the user must supply to finish spec 09

A pak tool, an edited `DT_Items` asset in the work folder (made with FModel, UAssetGUI and the `.usmap`), possibly the AES key, and `harness/pakmod.local.json`.
Then: `build`, `install`, `run.py --scenario datatable-vanilla` with `HARNESS_EXPECT_ITEM_ROWS`, `remove`, and a final `datatable-vanilla` run without it.
