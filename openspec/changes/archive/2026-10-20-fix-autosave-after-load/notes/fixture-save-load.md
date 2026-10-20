# Autosave push after a load of a fixture save (task 3.1)

Run 20261020-113640-0e3b: pass (branch fix/fix-autosave-after-load at 7fe8265, detached, plus a change to the test scenario).

- The run booted fixture `base` (installed as slot `saveGame_51`). The timer was far away at READY.
- The test scenario `autosave-after-load` then set no value. It checked that `savefileToLoad` was `saveGame_51` and ran `open <map>`. The map reads `savefileToLoad` on open (HarnessBoot comment), so this load reads the real fixture save file. No save function is called.
- Log: `autosave pushed away after a load: timer remaining 600.0 s -> 31535400.0 s (try 1)`.
- `autosave_status` after the load: new timer handle, remaining 31535386 s (limit 1000000 s).
- Launcher guard: "the user's save files did not change". Installed slot saveGame_51 was removed at the end.
- Backup of the save folder: `SaveGames-backup-315b-063624`.

Limit: this is a load by console `open`, not a click on the in-game load menu by the owner. Both run the same pawn BeginPlay. The log does not prove the world content came from the save (not a new game).
