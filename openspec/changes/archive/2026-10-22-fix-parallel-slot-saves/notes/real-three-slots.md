# Real run on three game slots (task 3.2)

Slot 0 (kept open): run 20261023-041019-dbd9, scenario noop, `--keep-open`. Fixture `base-corpse-pit` installed as `saveGame_52` (8 files; ledger entry has `game_slot` 0 and `game_root`).
While slot 0 stayed open:
- Slot 1: run 20261023-041108-82e4, noop, pass.
- Slot 2: run 20261023-041236-4ef0, noop, pass.
- After each of them all 8 files of `saveGame_52` still existed. No run aborted on `rtsSettings.sav`.

Stop: MCP `stop_game` slot 0 (pid ended). The fixture slot stays after a stop (the ledger entry stays too), as designed for a kept-open game. Removed with `harness/tools/fixtures.py uninstall`: `saveGame_52` is gone.

Save folder check: the folder is identical (SHA-256 of every file) to the backup `backups/saves-20261022-220445-queue` taken before the runs.

Tests: `test_runlib*` pass. `test_suitelib*` prints a "suite abx fail" line from a test of a failing suite (expected output of the test).
