# Spec 11: Parallel game slots

Status: steps 1 to 3 done (2026-10-17): `install.ps1` builds slots, and `run.py --slot N|auto` and the MCP `run_scenario(slot="auto")` run up to 3 games at once (3 x smoke passed in 98 s). Notes: `implementation-notes/spike-1-2-slots-low-settings.md`, `implementation-notes/step3-launcher-slots.md`. Step 4 done (2026-10-17): `suite.py --slots N|all` and `EXCLUSIVE` scenarios (`implementation-notes/step4-parallel-suite.md`). The `core` suite on 3 slots passes in 247 s against about 290 s on 1 slot: short scenarios are bound by the boot. Step 5 (a real A/B suite on 3 slots against 1 slot) is open. Idea from the user (2026-10-10): the game runs without Steam, so several copies can run at the same time.

## Goal
Run N independent game instances ("slots") on this machine at the same time, so that suites with many runs (A/B statistics, soak checks, flake finding) finish in a fraction of the wall time. Each slot gives the same results and guards as a single run today.

## Why
- Combat and raids are not deterministic. Spec 10 needs N runs per variant (`harness/suitelib/ab.py`). One run takes 40 to 70 s, and runs go one after the other.
- A suite of 6 scenarios with 3 runs each takes about 15 minutes today. With 3 slots it should take about 5 to 6 minutes.
- The run budget (cap 400) is not the limit here, wall time is.

## Non-goals
- Multiplayer or network play. Single-player only, localhost only (CLAUDE.md).
- More than the machine can carry. The target is 3 slots on this machine (see "Resource budget").
- Running scenarios that need the real screen or mouse in parallel (see "Exclusive scenarios").
- Distributing the game or any game file. Slots are local and git-ignored.

## Background (checked facts)
- The game starts directly without Steam (spec 03).
- Each run already has its own `LOCALAPPDATA` with fixture saves, its own run folder and its own bridge folder (`HARNESS_RUN_DIR`). Two runs do not share saves, logs or command files.
- The shared parts today: one game folder (`...\Manor Lords\ManorLords\Binaries\Win64\` holds the executable, UE4SS and the mods), one run lock (`runs/.lock`, `harness/runlib/runfolder.py`), one iteration counter (`runs/.iterations`), and one process search (the launcher and `stop_game` find the game by name).
- The game uses 3.3 to 3.7 GB RAM (RSS) and about 2.2 to 2.5 GB GPU memory per process (2026-10-17). Low settings save only about 0.3 GB GPU. The game reads AND writes its settings in the REAL user folder, not the private LOCALAPPDATA. Never change cvars through the console. The machine has 16 GB RAM, an 8-core Ryzen 7 3700X, an RTX 3070 (8 GB video memory) and about 47 GB free disk.
- The game paks are about 14 GB (20 files). They are read only.
- Crash reports go to the real `%LOCALAPPDATA%\ManorLords\Saved\Crashes`, not to the private one. The launcher copies them.

## Design
1. **Slot folder.** A slot is `slots/<n>/Manor Lords/` (git-ignored). `Win64` is a full copy (exe, UE4SS, mods). `Content/Paks` is a real folder with hard links to the game paks and its own `~mods`, so pak A/B tests do not mix. `Engine`, `Plugins`, `Content/Movies` and `Content/Slate` are junctions. About 0.6 GB per slot (spike 1). Slot 0 is the normal game folder.
2. **Config.** A local config (git-ignored, like `pakmod.local.json`) lists the slots: id, game folder path. Slot 0 is the normal game folder. A run takes a slot with `--slot <n>` or the next free one.
3. **Locks.** One lock file per slot (`runs/.lock-<n>`). A run takes the slot lock, not a global lock. The global parts stay global and are protected by a short lock: the iteration counter and the user-save hash check. All checkouts share these files (the main checkout and its git worktrees, `runlib/shared.py`), and the slots, the fixture ledger and the input lock too.
4. **Deploy.** `deploy.ps1` gets a `-Slot` option and deploys to the slot folder. Each slot folder is deployed before its run, as today.
5. **Process search.** The launcher, `stop_game` and the teardown find the game process by its executable path (the slot folder), not by name. A run never ends a game in another slot.
6. **Private data.** Every run keeps its own `LOCALAPPDATA`. Crash reports are matched to a slot by process id and time.
7. **Suite runner.** `harness/suite.py` starts up to N runs at once (a worker per slot) and keeps the A and B variants interleaved across slots. A slot that fails to start is marked bad and the suite continues with the others.
8. **MCP tools.** `run_scenario` gets an optional `slot` argument. `game_status` lists every slot, its lock holder and its game process. `wait_for_run` is unchanged.
9. **Exclusive scenarios.** A scenario can declare `EXCLUSIVE = True` (real mouse or keyboard input, screenshots of the screen). Such a scenario runs alone: the suite runner waits for the other slots to finish first.
10. **Install and uninstall (decided by the user, 2026-10-17).** The game reads and writes its settings in the REAL user folder (spike 2), so a run cannot have private settings. Instead the harness is installed into a state and uninstalled back:
    - `harness/install.ps1` backs up the user's `Config/Windows/GameUserSettings.ini`, `Config/Windows/UserSettings.ini` and `SaveGames/rtsSettings.sav` with SHA-256 (once: a second install never replaces the backup), then writes the harness values (low quality, windowed 1280x720, 30 fps) into the real files. Other keys (key bindings) stay. It builds the slot folders and deploys the mods to each slot with `deploy.ps1 -GameDir`.
    - `harness/uninstall.ps1` restores the backed-up files and checks their hashes, also in the default mode. `-Remove` also deletes the slot folders. It removes the junctions first, as links, so a delete never reaches the game folder.
    - State: `slots/.install/settings.json` (backup list and hashes, files in `slots/.install/backup/`) and `slots/.install/slots.json`. The state file is written before the first change.
    - Both scripts refuse to work while a game process runs, because the game writes its settings when it exits.
    - While installed, the user's own play also uses the harness settings. The user runs `uninstall.ps1` before playing.
    - Launch arguments `-windowed -ResX=1280 -ResY=720` and a `SetWindowPos` move place each slot window in its own screen tile, for OS mouse scenarios. The map load applies the settings file, so with the harness values in the file it stays 1280x720.
## Resource budget
- RAM: Windows and tools use about 6 to 8 GB. Each game about 1.3 GB. Three games fit, four are the limit. The runner refuses more slots than a config value (`max_slots`, default 3) and checks free memory before it starts a slot (refuse below a floor, default 2 GB free).
- CPU: each game uses several threads. At 8x speed the game is CPU heavy. Expect a lower speed when three run at once. Scenarios already assert ranges, not exact times.
- GPU: three windows render at once. Test with the lowest graphics settings if the game allows it.
- Disk: junction slots cost a few hundred MB each. A full copy costs about 14 GB.

## Plan
0. Done (2026-10-17): spikes 1 and 2, install and uninstall (design 10), step 3 (`implementation-notes/step3-launcher-slots.md`) and step 4 (`implementation-notes/step4-parallel-suite.md`). Next: step 5.
1. Spike (no harness change): build one junction slot by hand, start the game from it with a private `LOCALAPPDATA`, check that it boots to READY and that the mods load. Record the size on disk.
2. Spike: run two games at once. Measure RAM, boot time, the game clock rate at 1x and 8x, and compare with a single run. Then three games.
3. Build the slot support (config, per-slot lock, deploy, process search, MCP tools) with tests that use the fake game and stub launcher.
4. Parallel suite runner and `EXCLUSIVE` scenarios, with tests (including a slot that fails to start, and two runs that must not see each other's files).
5. Real runs: `raid-tiers` A/B on 3 slots against the same suite on 1 slot (same result ranges, shorter wall time).
6. Update `harness/README.md`, spec 00 roadmap and CHANGELOG.

## Risks and open questions
- Does the game accept a content junction (path checks, file locks, the `Saved` folder next to the executable)? The spike answers this.
- Does the game take a named mutex or a lock file that blocks a second instance? UE games usually do not, but not checked.
- Do two games fight for the same focus or audio device? Audio could be muted with a launch option. Not checked.
- Timing: slower games may break scenario time limits. Mitigation: measure per slot count and set limits from the measurement.
- The user-save guard compares hashes before and after each run. With parallel runs the guard must wait for the last run of a batch or compare a hash taken at batch start and batch end.
- A run killed by a suite timeout cannot remove its pak (spec 09 note). With slots, stale pak files must be cleaned per slot.
- Crash report matching when two games crash close to each other.

## Acceptance criteria
- [x] `install.ps1` then `uninstall.ps1` gives back the user's settings files bit for bit (hash check), also after a game run changed them. A second install keeps the first backup. Tested with temp folders and real PowerShell.
- [x] `uninstall.ps1 -Remove` deletes the slots and never a file in the game folder (test: a junction target survives).
- [x] The spike shows a slot boots to READY with all mods loaded, and records its disk size.
- [x] Two and three games run at once on this machine. RAM, boot time and clock rate are recorded in a note.
- [x] A run in slot 1 never stops, deploys over or reads files of slot 0 (process search by path, per-slot lock; real check: 3 parallel smoke runs).
- [x] The user-save hash guard still reports any change of the real save folder, also with parallel runs (harness files of the ledger and, while installed, `rtsSettings.sav` are left out; the check runs under `runs/.saves.lock`).
- [ ] The suite runner finishes a 3 slot suite in clearly less wall time than the same suite on 1 slot, with the same verdicts.
- [x] An `EXCLUSIVE` scenario never runs at the same time as another game (pool tests).
- [x] A slot that fails to start does not fail the other slots (pool tests and a CLI test with the stub launcher).
- [x] Unit tests for slot config, locks, deploy options, process search and the suite worker pool.
- [ ] No game file, key or slot folder is in git.
