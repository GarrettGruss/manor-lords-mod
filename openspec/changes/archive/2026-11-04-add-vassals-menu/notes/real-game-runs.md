# Real game runs of `vassals-menu-window`

All runs on slot 1 (never `--slot auto`).

| Run id | Verdict | Finding |
|---|---|---|
| `20261105-040732-ffe3` | harness_error | `--new-game`: Goldhof has no AI lord in a new game, so `vassals_adopt` refuses. The scenario needs the default fixture. |
| `20261105-040913-6662` | harness_error | `menu_state` has no `open_id` key when no menu is open (scenario bug, use `.get`). |
| `20261105-041101-90fa` | fail | "class not found": `run.py --pak` installs the pak from the `work_dir` of `harness/pakmod.local.json`, not from `mod/InvasionMod/paks/`. A worktree build needs its own `pakmod.local.json` with a private `work_dir` (the old pak was installed). |
| `20261105-041257-6f72`, `20261105-041504-4068` | fail | The window works. After a window was opened and closed, `run_game_days` fails ("the clock did not move after unPauseGame"): the game was paused by the harness before the open, so it stays paused, and the clock control cannot lift it. The scenario now runs all game days before the first open. Not analysed further (also true for other menus; out of scope). |
| `20261105-042047-e3e3` | harness_error | 21 asserts passed; a metric with a text value is refused by the harness. Fixed. |
| `20261105-042459-6e9c` | passed asserts (22 of 22), teardown failed | The teardown guard reports changed save files: other agents' fixtures added `saveGame_61` and `saveGame_62` to the real save folder while the run was active (hash compare against the backup: no existing file changed). |

Pictures: a game window of another run lay over the first pictures (`20261105-041257-6f72`). The scenario now brings its own window to the front before each picture.
The bottom bar entry is opened with `menu_press` (the same path as a bar click after the hook), not with a real mouse click, so that no other agent's input is disturbed.
