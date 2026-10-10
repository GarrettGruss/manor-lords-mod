# Save fixtures (part C): findings and design

Date: 2026-10-10. Code: `harness/runlib/fixtures.py`, `harness/tools/fixtures.py`, `harness/fixtures/fixtures.json`,
`run.py --fixture`, `harness/runlib/phases.py`, `harness/runlib/game.py`. Tests: `test_runlib_fixtures.py`.

## Step 1: the load screen does NOT list a slot with a custom name
A copy named `harness_base` (8 files of `saveGame_0`, with and without a rewritten descriptor) was not in the list, so `HarnessBoot` failed after 30 s.
What the game does (hooks on `MLSaveLoadMenuScreen` and `IoHandler`, read only):
- The load screen calls `StartSlotDiscovery`, then `SlotNameFromIndex(i)` for i = 0 and 2 to 29. Index 0 is `autosave`, index i from 2 is `saveGame_<i-2>`.
  So only `autosave` and `saveGame_0` to `saveGame_27` are read. `SlotIndex` of a list entry is this index.
- `DoesSaveGameExist("harness_base")` is true: the file name is fine for the game. The block is the discovery.
- Workarounds that failed: setting `Descriptor.saveSlot` in memory (the game loaded another file: a garbage `.sav` loaded just as well),
  setting `MLGameInstance.savefileToLoad` (stays empty), a post-hook on `SlotNameFromIndex` that returns another name (the hook ran, the list did not change).
- The user has slots 0 to 27, so there is no free numbered slot. Swapping into a user slot was rejected (it would write a user slot).
- Useful for hooks: UE4SS passes the return value first in a post-hook callback: `function(self, returnValue, param)`.

## Design now: a private LOCALAPPDATA for every run
The launcher starts the game directly, so it sets `LOCALAPPDATA=<run folder>\appdata` for the game process only.
UE builds its `Saved` path from this variable, so the game uses `<run>\appdata\ManorLords\Saved`. The fixture is copied there as `saveGame_0`,
a name that the load screen lists. The user's save folder is never opened by the game in a run, not even for its autosave.

### Real-game results (3 runs with `--fixture base`, smoke scenario, plus a default run)
| Question | Result |
|---|---|
| Does the game start and reach `HarnessBoot` READY? | Yes. 4 of 4 runs passed (`fixrun-1..3` with `--fixture base`, `defrun` without the option). |
| Boot time | With redirect: `boot.seconds` 31.0, 30.0, 31.0 and 31.0 (default run). Without redirect (probe runs before this change): 30 to 33 s. No difference. |
| Does it use the redirected folder? | Yes. The load screen found `saveGame_0` in the private folder, and the user folder stayed identical. |
| Steam / Steamworks | The game started directly as before and played normally. Nothing failed. Steam-only features (cloud, achievements) were not tested. |
| UE4SS | Found its folder next to the exe: all mods loaded (`mod.log` and `UE4SS.log` of the runs). |
| Window size and screenshot | Same as before (`runs/fixrun-1/screenshots/end.png`: game paused at Hochweg). The user's `Saved\Config` is copied (read only) into the private folder, so graphics and window settings stay the same. |
| Where do logs go? | Nothing was written to the user's `Saved\Logs` (it holds only `NGX`). In a 30 s probe the private folder got only the copied `Config` and `SaveGames`. The UE log, shader caches and the pipeline cache were not written in that time. They are not copied (77 MB); boot time did not change without them. |
| Crash reports | **Not tested** (no crash was forced). UE writes them under the `LOCALAPPDATA` it sees, so `<run>\appdata\ManorLords\Saved\Crashes` is expected. `collect` reads that folder when the run has a private appdata, and the old folder otherwise (unit tested with a fake crash folder). |

### Decision
The redirect is the **default for all runs** (boot time and behavior are the same). The default fixture is `base`: a copy of the user's `saveGame_0`.
`run.py --fixture <name>` picks another fixture. Every fixture is installed as `saveGame_0`.

### Flow
- `preflight`: stop a stale game, build `<run>\appdata` (copy of `Saved\Config`, fixture as `saveGame_0`), hash the user's save folder (all files).
  The fixture source files must match the SHA-256 values in the manifest, or the phase fails with the command to accept the change.
- `launch`: `LOCALAPPDATA` is set for the game process only.
- `collect`: crash folders come from the private appdata.
- `teardown`: after the game ended, hash the user's save folder again, delete `<run>\appdata`, and fail the run with the file names if a user file changed, is new or is gone.
  `config.json` has the full record (`environment.fixture`). `summary.json` has `fixture`, `fixture_sav_sha256` and `user_saves_sha256` (12 characters each).
- `fixtures.py`: `list`, `record` (write a manifest entry from the files of a slot), `install <name> --appdata DIR`, `remove --appdata DIR`
  (deletes only a folder named `appdata` that holds `ManorLords/Saved`). Every command hashes the user's save files before and after and aborts (exit 3, "ABORT") on a difference.
- `uninstall.ps1` is unchanged: the `harness_*` slot removal that I had added was dropped (with its tests), because there are no such slots any more.

## Safety check in the real save folder
204 files, SHA-256 of each, before any game start of this work and after all runs (hot reload tests, the fixture experiments, 3 runs with `--fixture base`, 1 default run):
**identical** (combined hash prefix `58ec8bcb82f21ad4`). `menu.sav` and `rtsSettings.sav` did not change. No `harness_*` file is left and no game process runs.

## Not verified
- Crash reports in the private folder (no crash was forced).
- Steam cloud or achievements with a redirected folder.
- A longer session: the game's own UE log, shader caches and autosave in the private folder (all are deleted with it at teardown).
