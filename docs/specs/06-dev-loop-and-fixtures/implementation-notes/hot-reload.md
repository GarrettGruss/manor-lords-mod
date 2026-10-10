# Hot reload (part A): findings and results

Date: 2026-10-10. Tested in the real game (build 25598558, UE4SS experimental, Lua 5.4) with a game that was paused after boot.
Code: `mod/HarnessReload/Scripts/main.lua`, `harness/tools/reload_mods.py`. Tests: `test_fakegame_harnessreload.py`, `test_reload_mods.py`.

## Result in short
- A Lua change reaches the running game in **2.1 to 2.3 s** (tool time, 3 runs in a row), with no game restart. The target was 30 s.
- Method: `RestartMod(name)` of the UE4SS Lua API, called by the new mod `HarnessReload` on a request file. UE4SS also had auto reload on.
- No double hooks and no duplicate loops were seen after more than 10 reloads.

## How the game was kept running for the tests
A small script (not in the repo) used `runlib.game` (`GameInstall`, `build_game_environment`, `read_boot_file`): it created a run folder,
started `ManorLords-Win64-Shipping.exe` with `HARNESS_RUN_DIR`, `HARNESS_AUTOBOOT=1` and `HARNESS_TEST_SAVE=saveGame_0`,
waited for `READY` in `boot.json`, and stayed alive until a `stop` file appeared. Then it terminated the game. Boot took about 31 s.
`reload_mods.py` finds the run folder itself: it reads `HARNESS_RUN_DIR` from the environment of the game process (`psutil`).

## Option 1: UE4SS hot reload (Ctrl+R) and auto reload
- `UE4SS-settings.ini` in this install **already** has `EnableHotReloadSystem = 1` and `EnableAutoReloadingLuaMods = 1`
  (file date 2026-10-09 21:20; the spec said 0). I did not change the file. If it is 0 on another machine, `HarnessReload` still works (option 2).
- Ctrl+R was **not tested** (no key press was sent). It restarts all mods, which is the wrong tool here (it would restart `HarnessBoot`).
- Auto reload works. A deploy changed one file; about 1 s later UE4SS.log had `Stopping mod 'X' for uninstall` and `Auto-reloading Lua mod 'X'`, and the mod logged its new version.
  Only that one mod is restarted.
- **Problem: with two changed mods in one deploy, only one is reloaded** (seen twice: the other mod kept the old code, with no message).
  So auto reload alone is not safe for a multi-file change. `reload_mods.py` always restarts every changed mod itself.
- Auto reload and `RestartMod` can both fire for the same change: the mod then loads twice within the same second (seen in 2 of 3 timed runs).
  This is harmless: UE4SS unregisters the hooks of the old state each time (see below).
- A syntax error in the new file: UE4SS.log has `Error loading script: ...main.lua:19: unexpected symbol near '='` and `Failed to execute main script`.
  The mod is not loaded, and the game keeps running. After the file was fixed, the next deploy loaded it again. The error is **not** in `mod.log`.

## Option 2: `RestartMod` and `HarnessReload`
- The UE4SS Lua API has `RestartMod(name)`, `RestartCurrentMod()`, `UninstallMod(name)` (docs: `ue4ss/Docs/lua-api/global-functions/modmanagement.md` in the game folder).
  `RestartMod` works from a Lua mod of another name. A restart takes 0.4 to 0.6 s until the new code logs its version line.
- `RestartMod("Nope")` does **not** fail. UE4SS.log only says `Could not find mod to reinstall: Nope`. So `HarnessReload` checks that
  `Mods/<name>/Scripts/main.lua` exists first, and the tool checks that `mod/<name>` exists.
- A restart gives the mod a **new Lua state**. Evidence: UE4SS.log has `Unregistering hook by id 'getGameTimeAdjusted#7' for mod HarnessLogTest` for every hook of the old state,
  then a new `Registered native hook`. The old `LoopAsync` loop stopped at once (the v2 heartbeat stopped when v3 loaded).
  So a `dofile` guard like the generation counter in `UEBridge` is **not needed** with `RestartMod`.
- Side-effect test (temporary code in `HarnessLogTest`: a `RegisterHook` on `RTSMultiEngineCPP:getGameTimeAdjusted`, a 5 s loop, a key bind):
  after 4 `RestartMod` calls and 2 auto reloads, there was exactly one `hook fired` and one `heartbeat` line per 5 s.
  After a double load (auto reload and `RestartMod` in the same second), the hook ids were 29/30, then 31/32, and again one line per 5 s.
  The key bind was registered but never pressed, so duplicate key binds were **not** checked.
- `HarnessTelemetry` was restarted too: one sample every 5 s before and after (no second sampler).
- UE4SS passes the return value first in a post-hook callback (`function(self, returnValue, param)`), not last. (Found while testing fixtures.)

## The request protocol
- Request: `<HARNESS_RUN_DIR>/reload.json` = `{"mod": "Name", "id": "unique"}`. The tool writes `reload.json.tmp` and renames it.
- `HarnessReload` polls every 200 ms (`LoopAsync`), deletes the file when read, handles an id once, and calls `RestartMod` inside `ExecuteInGameThread`.
  It reads the request with two patterns, not a JSON parser. A mod name must match `[%w_]+`.
- It refuses `HarnessReload` itself (a restart of itself would drop its own result). While it waits for an answer, it reads no other request.
- It waits up to 20 s for a new line `[<Name>] loaded version <v>` in `mod.log` (only text after the position before the restart counts).
- Result: `reload.result.json` = `{"id","mod","ok","version","line","error","seconds"}`, written atomically. The tool deletes an old result before it writes a request.
- Tested: unknown mod, bad name and self in the real game; also no id, repeated id, restart error, timeout and a waiting second request in the mock test.

## The pattern for a reloadable mod
1. Put `local VERSION = "1"` near the top of `Scripts/main.lua`. Change it when you want the tool to prove that the new code runs.
2. Log one line through `HarnessLog` with the **folder name as tag**: `log.info("MyMod", "loaded version " .. VERSION)`.
   The tool compares the version with the `VERSION` line in `mod/MyMod/Scripts/main.lua`. Text after the version is allowed (start it with a space or a comma).
3. Register hooks, loops and key binds as usual. Do not guard them. The restart removes them.
4. Do not keep state in globals and expect it to live on. Use `ModRef:SetSharedVariable` for values that must survive (the UE4SS docs say these are not reset).
5. A mod with a once-per-game job must not be restarted. `HarnessBoot` would load the save again. The tool skips `HarnessBoot` and `HarnessReload`
   unless they are named with `--mod`. `HarnessReload` refuses its own restart. A change to `HarnessReload` is picked up by auto reload when it is the only change, or by a game restart.
6. A change in a `shared/` module restarts every mod that calls `require("<Module>")` (found by text search).

Mods with a version line now: `HarnessLogTest`, `HarnessReload`, `HarnessTelemetry`, `HarnessLoadProbe`.
`UEBridge` has its own `reload` op (`dofile` with a generation counter) and no version line in `mod.log`. `HarnessBoot` has none.

## Timings (tool `reload_mods.py`, deploy included, game running)
| Run | Change | Tool seconds | Mod restart seconds |
|---|---|---|---|
| 1 | `HarnessLogTest` VERSION 6 to 7 | 2.3 | 0.6 |
| 2 | VERSION 7 to 8 | 2.1 | 0.4 |
| 3 | VERSION 8 to 9 | 2.1 | 0.4 |
| 4 | 3 mods at once (`HarnessLoadProbe`, `HarnessLogTest`, `HarnessTelemetry`) | 3.2 | 0.6 / 0.4 / 0.4 |

Most of the tool time is the start of `powershell` and `deploy.ps1` (hashing). The start of Python is not in these numbers.

## Not verified
- Ctrl+R (not pressed). Auto reload with `EnableAutoReloadingLuaMods = 0` (then only `RestartMod` is used; it does not depend on the setting, but I did not turn the setting off).
- A changed `shared/` module: the mapping to dependent mods is unit tested; a real reload after a change of a shared file was not run.
- A restart during a pop-up or while the game is unpaused. The game was paused after boot in every test.
- A game that was started without `HARNESS_RUN_DIR` (the tool needs the run folder).
- Duplicate key binds after a restart (the key was not pressed).
