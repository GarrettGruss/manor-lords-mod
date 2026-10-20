# Widget build (tasks 3.1 and 3.2)

- Script: `mod/InvasionMod/ue/make_liege_widget.py`. Copy of the raid widget method. Widget `/Game/HarnessMod/WBP_LiegeTribute`.
- Widgets: `TitleText`, `InfluenceText`, `TributeInfoText` (TextBlock); `TributeButton`, `CloseButton` (Border placeholders for `WBP_ClickButton`).
- Made in UE 5.5.4 (`UnrealEditor-Cmd -ExecutePythonScript`, workspace `mlm-ue\ManorLords`). The asset exists. The script printed no `LIEGE:` line to stdout, but the editor exit code was 0.
- Cook (`-run=cook ... -skipeditorcontent`): exit 1 with "13 error(s)", but `WBP_LiegeTribute.uasset` (4500 B) and `.uexp` (626 B) were cooked. The errors were not read in detail; they look unrelated (other assets).
- Copied `WBP_LiegeTribute.*` and `WBP_ClickButton.*` into `modtools/work/raidmenu/ManorLords/Content/HarnessMod/`. `WBP_ClickButton` was already there with the same hash.
- `mod.json` already lists `HarnessClickHooks` in `shared`. No change needed.
- Not verified: `pakmod.py buildmod InvasionMod` stops with "MANORLORDS_AES_KEY is not set". `buildmod` also builds row patches, not the widget pak. The widget pak step is `pakmod.py build raidmenu` (not run: it needs the key and would change the committed `raidmenu_P.pak`).
- Not verified: the widget in the game.

## Pak build (verified 2026-10-19)

- `uv run python harness/tools/pakmod.py build raidmenu` (key from the gitignored `.env`; `harness/pakmod.local.json` copied from the main checkout into the worktree, it is gitignored). Result: 6 files, 27119 bytes, "the pak lists the same 6 files as the folder": `WBP_RaidMenu`, `WBP_LiegeTribute`, `WBP_ClickButton` (each `.uasset` + `.uexp`). Copied to `mod/InvasionMod/paks/raidmenu_P.pak` (was 21777 bytes).
- The 13 cook errors: the editor log shows `WBP_ClickButton` compile errors ("Can't connect pins Self and Button", an old widget) and "Content is missing from cook" lines. None names `WBP_LiegeTribute`. Treated as unrelated.
- Still not verified: the widget in the game.
