# Fresh start (part E, 2026-10-12)

## Method
- The load bug of part C showed that a map that opens while `MLGameInstance.savefileToLoad` is empty starts a new game.
- HarnessBoot (`HARNESS_NEW_GAME=1`) skips the load screen and runs the console command `open /Game/NotStronghold/Maps/NewMapSets/<map>`.
- No eval was used. The launcher passes `HARNESS_NEW_GAME_MAP` (default `Jagged_Cliffs`).

## Results
- Run `fresh-start-1`: `PlayerController:ConsoleCommand` fails (`attempt to call a TrivialObject value`). The boot ended in FAILED, as designed.
- Run `fresh-start-2` (after the fix to `KismetSystemLibrary:ExecuteConsoleCommand(world, command, controller)`): READY after 28 s.
  - Boot log: `new game confirmed: savefileToLoad is empty`; autosave timer 600 s -> 31535400 s; one `pauseGame` call after the intro cinematic.
  - Telemetry: day 61, March, year 1; region Hochweg settled, 5 homeless families, population 10, food 3.
  - User save folder: 240 files, fingerprint `4d4304b366f5` before and after.
- The start region is random (earlier new games had other names). A start region choice is not done.

## Not verified
- Maps other than `Jagged_Cliffs`. A wrong map name ends in FAILED after the READY time limit (180 s); not run in the real game.
- `autosave_status` through HarnessActions (no scenario step in these runs).
