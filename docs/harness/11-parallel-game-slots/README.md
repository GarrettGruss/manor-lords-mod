# Spec 11: Parallel game slots

Status: proposed (2026-10-10). Idea from the user: the game runs without Steam, so it may be possible to run several copies of the game at the same time. Nothing is built yet.

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
- The game uses about 1.3 GB of RAM per process (seen on a running process, 2026-10-10). The machine has 16 GB RAM, an 8-core Ryzen 7 3700X, an RTX 3070 (8 GB video memory) and about 47 GB free disk.
- The game paks are about 14 GB (20 files). They are read only.
- Crash reports go to the real `%LOCALAPPDATA%\ManorLords\Saved\Crashes`, not to the private one. The launcher copies them.

## Design
1. **Slot folder.** A slot is a folder `slots/<n>/` (git-ignored) with its own copy of `ManorLords\Binaries\Win64\` (executable, UE4SS, mods) and a directory junction for the read-only content. The junction points to the original `ManorLords\Content`, so the 14 GB are not copied. If a junction does not work for the game, use a full copy of one slot and measure the disk cost.
2. **Config.** A local config (git-ignored, like `pakmod.local.json`) lists the slots: id, game folder path. Slot 0 is the normal game folder. A run takes a slot with `--slot <n>` or the next free one.
3. **Locks.** One lock file per slot (`runs/.lock-<n>`). A run takes the slot lock, not a global lock. The global parts stay global and are protected by a short lock: the iteration counter and the user-save hash check.
4. **Deploy.** `deploy.ps1` gets a `-Slot` option and deploys to the slot folder. Each slot folder is deployed before its run, as today.
5. **Process search.** The launcher, `stop_game` and the teardown find the game process by its executable path (the slot folder), not by name. A run never ends a game in another slot.
6. **Private data.** Every run keeps its own `LOCALAPPDATA`. Crash reports are matched to a slot by process id and time.
7. **Suite runner.** `harness/suite.py` starts up to N runs at once (a worker per slot) and keeps the A and B variants interleaved across slots. A slot that fails to start is marked bad and the suite continues with the others.
8. **MCP tools.** `run_scenario` gets an optional `slot` argument. `game_status` lists every slot, its lock holder and its game process. `wait_for_run` is unchanged.
9. **Exclusive scenarios.** A scenario can declare `EXCLUSIVE = True` (real mouse or keyboard input, screenshots of the screen). Such a scenario runs alone: the suite runner waits for the other slots to finish first.

## Resource budget
- RAM: Windows and tools use about 6 to 8 GB. Each game about 1.3 GB. Three games fit, four are the limit. The runner refuses more slots than a config value (`max_slots`, default 3) and checks free memory before it starts a slot (refuse below a floor, default 2 GB free).
- CPU: each game uses several threads. At 8x speed the game is CPU heavy. Expect a lower speed when three run at once. Scenarios already assert ranges, not exact times.
- GPU: three windows render at once. Test with the lowest graphics settings if the game allows it.
- Disk: junction slots cost a few hundred MB each. A full copy costs about 14 GB.

## Plan
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
- [ ] The spike shows a slot boots to READY with all mods loaded, and records its disk size.
- [ ] Two and three games run at once on this machine. RAM, boot time and clock rate are recorded in a note.
- [ ] A run in slot 1 never stops, deploys over or reads files of slot 0 (tested with the stub launcher and a real check).
- [ ] The user-save hash guard still reports any change of the real save folder, also with parallel runs.
- [ ] The suite runner finishes a 3 slot suite in clearly less wall time than the same suite on 1 slot, with the same verdicts.
- [ ] An `EXCLUSIVE` scenario never runs at the same time as another game.
- [ ] A slot that fails to start does not fail the other slots.
- [ ] Unit tests for slot config, locks, deploy options, process search and the suite worker pool.
- [ ] No game file, key or slot folder is in git.
