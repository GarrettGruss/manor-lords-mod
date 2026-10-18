# Step 3: the launcher runs in game slots (2026-10-17)

## What was built
- `runlib/gameslots.py`: slot 0 is the game folder. Slots 1 to 3 come from `slots/.install/slots.json` (written by `install.ps1`). A slot only gives a game root; `GameInstall.steam_root` keeps the Steam manifest of the real game.
- `run.py --slot N|auto` (default 0). `auto` takes the first slot whose run lock is free. Config records `slot`.
- Run lock per slot: `runs/.lock` (slot 0, old name) and `runs/.lock-<n>`.
- `WaitLock` (waits, takes over the lock of a dead process, fails with `LockTimeoutError`):
  - `runs/.saves.lock`: every change to the user's REAL save folder and the ledger (stale slot removal, fixture install with its slot number, the save check, `save_game` for its whole save).
  - `runs/.iterations.lock`: the run counter.
  - `runs/.input.lock`: each OS mouse or keyboard action of a scenario (`place_with_mouse`, `click_with_mouse`, `order_with_mouse`, `hover_with_mouse`, `press_key`). There is one cursor for all slots.
- Ledger entries record `owner_pid` and `owner_started`. `uninstall_all` keeps entries of another live run. The start time rules out a reused pid. Old entries without an owner are left-overs.
- The save check (`phases.user_files`) leaves out every file that the ledger lists, and, while `install.ps1` is active, `rtsSettings.sav`. The game rewrites that file when the harness settings are active; `uninstall.ps1` restores it from the backup.
- Process search by path: `find_game_processes(root)`. Preflight stops only stale games of its own slot. Teardown stops only its own slot. Screenshots and OS input use the run's own game pid.
- After READY the game window moves to the slot's tile (`gameslots.TILES`), only when the harness settings are installed.
- MCP: `run_scenario(name, slot="auto")`, one start claim per slot (`.active-launcher.json`, `.active-launcher-<n>.json`), `game_status` lists slots and `free_slots`, `stop_game(slot=0)`.

## Found on the way
- The `test_pakmod` uninstall tests ran `uninstall.ps1 -Remove` with a temp game folder but the default (real) `slots` folder. The full suite deleted the real slots and restored the user settings. No game file was lost (junctions are removed as links first; game folder 16.06 GB, all four junction targets complete).
  Fixes: the tests pass a temp `-SlotsDir`; both state files record `game_dir`, and an uninstall for another game folder leaves them alone (test `test_uninstall_for_another_game_folder_leaves_the_state_alone`). After the fix the full suite leaves the real state unchanged (hash check).
- A slot run first failed in preflight: the Steam manifest path was built from the slot folder. Fixed with `steam_root`.

## Real runs
| Runs | Result | Wall | Boot s | Fixture slots |
|---|---|---|---|---|
| 3 x `smoke`, `--slot auto` | 3 pass | 98 s | 55, 79, 71 | saveGame_51, 52, 53 |

The user's save files (all but `rtsSettings.sav`) had the same hashes before and after.

## Not done (step 4)
- The suite runner still runs one run after the other.
- `EXCLUSIVE` scenarios. The input lock prevents two clicks at the same time, but not other windows covering a game during a long mouse sequence.
