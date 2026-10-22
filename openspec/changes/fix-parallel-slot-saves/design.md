## Which slot owns a ledger entry

`saveslots.install` adds two fields to the entry: `game_slot` (the number) and `game_root` (the game folder of that slot). The run knows both from its `GameInstall`. The existing owner fields (`owner_pid`, `owner_started`) stay.

The owner process is the wrong test for a `--keep-open` run: the harness process ends and the game keeps running. So `uninstall_all` decides per entry:

1. Same `game_slot` as the new run: remove it. The new run stops that game in preflight (`_stop_stale_game`) before this step.
2. Another `game_slot`: keep it if a game process runs under `game_root` (`find_game_processes(root)`) or if the owner is alive (`has_live_owner`). Otherwise remove it.
3. No `game_slot` field (old entry): remove it, as now.

The check runs under the shared saves lock, so no entry changes in between.

## What the guard ignores

- `rtsSettings.sav`: the game rewrites it when its settings differ, at any time, in every slot. It is a settings file, not a save. Today the guard ignores it only when the `install.ps1` settings are installed; the change ignores it always.
- Files of ledger entries whose game still runs (rule 2 above). They are harness files, not user files. Teardown already ignores the entries that were listed at the start of the run; the live-game rule also covers entries that appear after the run started.
- Nothing else. The game also writes `menu.sav` (menu state) and the saves of the user. The guard keeps those strict, because a change there can mean a lost user save.

## Risk

A run that has no game slot (old tests, fake game kit) uses `game_slot = 0`. The process check uses only the game folder, so it works with the fake game kit.
