# Spec 00: Harness overview and roadmap

Status: all specs in the roadmap are built, tested with the real game, and merged (spec 09 is deferred on purpose).
This spec holds the plan for all other specs. Update it when a spec is finished or changes.
Follow-up items are listed at the end of this file.

## Purpose
Let an AI agent develop and test Manor Lords mods in a loop, with no human in the loop:
edit the mod, deploy it, run the game, read the result, and repeat.

**Main objective:** the agent changes a mod and, within about 2 to 3 minutes, gets a trustworthy result (pass, fail or crash) with evidence.

## What "90% of testing" means
For each mod feature:
1. The spec states its acceptance criteria as measurable game state (ranges, not exact values).
2. At least one scenario checks each criterion, and the agent can run it alone.
3. The agent reads `summary.json` and decides what to do next. It opens logs and screenshots only if needed.

A criterion counts as "automated" when a scenario checks it. The target is that **at least 90% of the acceptance criteria of each feature are automated**.
The remaining criteria are for the human: how the feature looks and feels, balance, and the final review of a pull request.
Each feature spec lists which criteria are automated and which are human.

## Test layers (fast to slow)

| Layer | What it checks | Speed | Status |
|---|---|---|---|
| 0. Syntax | Lua files compile (`harness/tests/lua_syntax.py`) | seconds | built |
| 1. Mock tests | mod logic against a fake game API (`harness/tests/boot_state_machine.py`) | seconds | built for HarnessBoot. A reusable kit is planned (spec 06) |
| 2. Live probe | read, set and call things in a running game through the bridge | seconds per query | built (specs 01 and 02) |
| 3. Scenario run | cold start, load save, run a scenario, collect results, stop the game | 1 to 2 min | spec 03, in progress |
| 4. Regression suite | many scenarios and saves, compared with baseline ranges | minutes to hours | spec 08 |
| 5. Human | look and feel, balance, final review | n/a | stays with the user |

An agent uses the fastest layer that can answer its question. It moves to a slower layer only when it must.

## Roadmap

| Spec | Name | Goal | Status |
|---|---|---|---|
| 01 | ue4ss-bridge | Live control channel into the running game | done (PR 1) |
| 02 | save-autoload | Load a fixed save and report ready, with the game paused | done (PR 2). The save copy is solved in spec 06 |
| 03 | run-launcher | One command makes one run folder with `summary.json` | done (PR 3). `harness/run.py`, scenarios, screenshots, crash and timeout cases |
| 04 | telemetry-and-assertions | Sample game state, assert ranges, define the scenario format, control game time | done (PR 4). `ctx.time`, `ctx.expect`, `HarnessTelemetry` |
| 05 | agent-tools | MCP tools so the agent drives the harness directly | done (PR 5). Open: a check in a real Claude Code session |
| 06 | dev-loop-and-fixtures | Hot reload without a game restart, a reusable mock kit, several test saves | done (hot reload, mock kit, fixtures through a private LOCALAPPDATA) |
| 07 | feature-test-kit | Helpers to give resources, place buildings, trigger events, advance time | done (15 checked actions, `ctx.actions`, helper mod for letters; building placement with the real OS mouse) |
| 08 | regression-suite | Run many scenarios and saves, compare with baselines, find flaky tests | done (PR 6). Baselines are thin (2 to 4 runs) |
| 09 | asset-mods | Pak editing and repacking for changes that Lua cannot reach | tooling built and tested with a fake packer (`feat/11-asset-mod-tool`). A real pak build is not verified: it needs a pak tool, an edited asset and maybe the AES key from the user. The spec says when to build it |

Order and reasons:
- 03 comes first: every later spec needs a run folder and a summary.
- 04 next: without telemetry and assertions a run cannot say pass or fail for a feature.
- 05 can start after 03 and 04 work by hand. It is the step that lets the agent work without the user starting commands.
- 06 and 07 are the main work for the 90% goal. 06 makes iteration fast. 07 lets a scenario create the situation that a feature needs.
- 08 comes when there are enough scenarios to protect against regressions.

### Gate for each spec
A spec is done when its acceptance criteria are met and the notes in `implementation-notes/` record the evidence.
Then update the status here and in the changelog.

## Feature workflow (what an agent does for a new mod feature)
1. Write or update the feature spec in `docs/specs/<NN>-<name>/` with acceptance criteria as measurable game state. Mark each criterion automated or human.
2. Check what the game exposes: search the jmap, and probe through the bridge. Record the names in `implementation-notes/`.
3. Write the mod code. Test the logic at layer 1 (mock), with a syntax check at layer 0.
4. Try it live at layer 2: deploy, reload, and query the running game.
5. Write the scenario for each automated criterion. Run it at layer 3. Read `summary.json`.
6. Fix and repeat. Run the scenario several times to see if it is flaky.
7. Run the regression suite (layer 4) before the pull request.
8. In the pull request: show the summary evidence, list the human criteria, and note what was not verified.

## Principles
- Assert ranges, not exact values. The simulation is not deterministic.
- A crash is a result with logs. It is not a harness failure.
- Each run uses its own folder. No state is shared between runs.
- The summary comes first. Logs and screenshots are for follow-up.
- Every wait has a time limit. A run that hangs is a timeout result.
- Repeat runs to measure flakiness (as the 10-launch series did). Do not trust one pass.
- The harness never writes to the user's saves. Saves are copied or read only.
- Safety rails stay on: an iteration cap, a run lock, and the uninstall script (`harness/uninstall.ps1`) as a kill switch.
- Keep a run short (under 3 minutes) so the loop stays fast.
- Record findings in the spec's `implementation-notes/`. A finding that changes a decision updates the spec in the same commit.

## What is verified today (see the specs for evidence)
- The bridge reads and writes game state and calls functions (spec 01). Some limits: no object-reference or out parameters, and a nil name once crashed the game (fixed by patch P8).
- A cold start loads `saveGame_0` and reaches a paused game in 42 to 44 s, 10 of 10 runs (spec 02).
- The game does not close on request. The harness stops it with a kill.
- The game restarts its clock once after our first pause. The harness holds the pause (spec 02).
- A direct launch of the game executable passes environment variables, so each run can have its own folder (spec 03).
- Game state is readable: calendar, region approval, public order, wealth, food, population, player silver, letters (`InBox`).
- One command (`python harness/run.py --scenario <name>`) runs a full iteration in 40 to 90 s and writes a `summary.json` under 4 KB (spec 03). Verdicts: pass, fail, crash, timeout, harness error.
- A scenario can control game speed (1x, 4x, 8x) and run N game days, sample state every 5 s, and assert ranges (spec 04). One game day is 40 game seconds.
- An agent can start a run, wait for it, and read results through MCP tools without shell commands (spec 05, tested with the tool functions and a real run).
- A suite of scenarios runs with one command, with baselines, drift and flake detection (spec 08). The `core` suite (5 runs) takes about 280 s.
- A Lua change reaches the running game in about 2 s (spec 06). A mod can be tested without the game with the fake game kit.
- Each run has a private save folder (`LOCALAPPDATA` redirect). The game's saves are copies of the fixture, and the user's save folder is hashed before and after every run.
- A scenario can change game state with checked actions: silver, influence, the day, regional wealth, items, settlement level, bandits, letters (spec 07).

## Main risks and unknowns

| Risk | Effect | Plan |
|---|---|---|
| Core simulation logic is not reflected (only state and some functions are) | Some features can only be checked through their effects | Write criteria as state ranges. Use hooks on reflected functions where they exist |
| Actions that need UI clicks (placing a building, for example) may have no callable function | The kit (spec 07) cannot create some situations | Search the jmap for the function behind each UI action. Fall back to save fixtures that already contain the situation |
| A game update changes hooks or names | Scenarios break | Pin the game build. Record the build in each summary. Disable auto-update |
| Screenshots may not show the game when it is behind another window | Visual checks fail | Test `mss` in spec 03. Keep the game window in front during runs |
| The game restarts its clock after a load, and the cause is unknown | The pause can fail in a new case | Hold the pause and check the clock. Find the cause later (optional) |
| Steam must be running for a direct launch | A run fails to start | Spec 03 checks it in `preflight` and fails with a clear message |
| Agent cost grows with many runs | Budget | Use the fastest layer, cap iterations, use Sonnet for agent work (see `CLAUDE.md`) |
| A game function that saves writes into the user's REAL save folder, even with the private `LOCALAPPDATA` (it overwrote `saveGame_9` once) | Loss of user data | Never call save functions (`CLAUDE.md`). The launcher hashes the user's saves before and after a run and fails the run, but only after the write. The user's backup folder allowed a bit-exact restore |
| The game's own autosave may also write to the real folder in a long run | Changed user save | `HarnessBoot` now pushes the autosave timer one year away before READY (`SetAutosavePeriodOnPawn`). Checked: timer 600 s -> 31,535,386 s, stays after 60 game seconds, save folder unchanged. The timer ran also in the paused game (about 10 min after the load) before this fix. See `06-dev-loop-and-fixtures/implementation-notes/autosave.md` |
| A game pop-up (for example 'Hunger!') pauses the clock and cannot be closed through the bridge | A long time-advance scenario stalls | Keep scenarios short. Detect a stopped clock and fail with a clear reason |
| Cheat based actions depend on the stock `CheatManagerEnablerMod` | Actions stop working if it is removed | Keep it in `mods.txt`. The catalog notes this |

## Open decisions
- Which features will be built first? Write each feature spec with acceptance criteria as state ranges, then use the feature workflow above.
- Which test saves are needed (famine, raid, trade, many buildings)? Saves can now be used without touching the user's saves (private `LOCALAPPDATA`), but a new situation still needs a save made by hand, because `requestSaveFile` writes to the real folder and is forbidden.
- Should a nightly regression run be started by a scheduled task? This needs an unlocked desktop session.
- Is a second machine or user account for the game worth it, so the harness does not take over the user's screen?

## Acceptance criteria
- Each spec in the roadmap exists, and its status here matches its real state.
- For every feature spec, at least 90% of the criteria are marked automated, or the reason is written down.
- A new agent can follow the "Feature workflow" with no help from the user, using the harness commands and tools.

## Follow-up items (not blocking)
- PARTLY CLOSED (done on 2026-10-10 in feat/10-roadmap-followups): the `manor-harness` MCP tools in a real Claude Code session. A fresh `claude -p` session loaded `.mcp.json` and called `list_scenarios`, `game_status` and `list_runs` correctly (two defects found and fixed). DECIDED by the user on 2026-10-10: `run_scenario` is allowed without asking (moved from `ask` to `allow` in `.claude/settings.json`; `stop_game` still asks). Notes: `05-agent-tools/implementation-notes/build-notes.md`.
- CLOSED as not needed: Ctrl+R (the UE4SS hot reload key). `HarnessReload` (`RestartMod`) reloads a mod in about 2 s, and UE4SS auto reload is already on (`EnableAutoReloadingLuaMods=1`), so no key press is needed (spec 06, `hot-reload.md`).
- CLOSED (done on 2026-10-10 in feat/10-roadmap-followups): Disable the game's autosave at boot. `HarnessBoot` state `DISABLING_AUTOSAVE`, scenario `autosave-protection` (timer far away at READY and after 60 running game seconds, real save folder identical, 204 files). Not verified: a run longer than 10 minutes, a second pawn after a second load, the native `SetAutosavePeriod` (not called on purpose). Notes: `06-dev-loop-and-fixtures/implementation-notes/autosave.md`.
- CLOSED (done on 2026-10-10 in feat/10-roadmap-followups): Crash report in a real crash. Scenario `selftest-crash`: verdict `crash`, exit 2, summary written, collect and teardown ran. The report is in the user's REAL `Crashes` folder, not in the private appdata. Bug fixed: collect now searches both (matched by process id), and teardown stops the orphan `CrashReportClient.exe`. Notes: `03-run-launcher/implementation-notes/real-crash-report.md`.
- PARTLY CLOSED (done on 2026-10-10 in feat/10-roadmap-followups): `--keep-open` with the real game: the launcher exits with the game running and paused, the lock is released, the private appdata stays until `fixtures.py remove --appdata` (documented, 4 MB per run). Notes: `03-run-launcher/implementation-notes/keep-open.md`. Minimized game window: tested 2026-10-10 (a defect was found and fixed: the picker took the UE4SS debug window, see `03-run-launcher/implementation-notes/step3-6-scenarios-screenshots.md`). Direct launch with Steam closed: NOT tested on purpose (it needs Steam to be shut down, and the permission system refused that for the user's running session; `preflight` fails with a clear message when Steam is not running; notes in `03-run-launcher/implementation-notes/direct-launch-with-environment.md`). Still open: another monitor (not tested; this machine has one screen).
- PARTLY CLOSED (done on 2026-10-10 in feat/12-clock-cause-and-buildings): the clock restart after a load is explained. The intro cinematic ends about 13 s after `LoadGame` with `PawnCPP:setMainUIMode(Gameplay)`, which restores 1x and undoes a pause. `HarnessBoot` now waits while `currentUIMode ~= 0` and calls `pauseGame` once (5 of 5 smoke runs pass with one call; the 8 s hold stays as a safety net). The fallback to 1x about 1 to 2 s after `changeGameSpeed(3)` was tested further on 2026-10-10: it is intermittent (2 of 6 controlled trials), not caused by the tutorial queue, a new letter, or the probe's own reads; the caller of `decreaseGameSpeed` stays unknown. Closed as "intermittent, handled by the `set_speed` retry". Notes: `02-save-autoload/implementation-notes/clock-restart-cause.md`.
- CLOSED (done on 2026-10-10): thicker baselines. Five more `core` suites passed (14 smoke, 12 time-advance, 5 telemetry-sanity runs). Every value was inside the existing ranges. The `duration_s` ranges were tightened to about 20 percent around the observed spread, and `core` passes against them with no drift. Notes: `08-regression-suite/implementation-notes/build-notes.md`.
- CLOSED (2026-10-10, feat/14-os-mouse-placement): building placement works with a real OS mouse click. Action `place_building` (verified, 10 runs, HitchingPost). It uses the OS mouse and focus, so a person must not work on the computer. Notes: `07-feature-test-kit/implementation-notes/building-placement.md`. Older text: building placement had no verified action (probed 2026-10-10 in feat/12-clock-cause-and-buildings). `PawnCPP:activateBuildingMode(id)` enters building mode (`isInAnyConstructionMode` true) and `LMB_BP_pressed/released` can be called, but `getMouse3d` is (0, 0, -100000) (no ground under the cursor), and 8 types gave no new building. A human or OS mouse input must hover the ground. Second attempt (2026-10-10, feat/13-building-placement, 13 runs): a post hook on `getMouse3d` and `getMouse` can fake the mouse position (works, no crash), but no preview appears and no building is placed; `BuildingSpawnParams` has no reflected fields (Lua cannot fill it) and a zeroed struct spawned nothing. Still open, not verified. Raids: no verified action. Notes: `07-feature-test-kit/implementation-notes/building-placement.md`.
- CLOSED (done on 2026-10-10 in feat/10-roadmap-followups): Spec 09 first check. A Lua mod reads and writes number fields of `itemStats` rows (213 rows, `FindRow`), so a pak is not needed for numbers. The bridge cannot read rows (`RowStruct` read and `getItem` crash the game). Not verified: that game logic uses a changed value, persistence over a load, string and soft fields. Notes: `09-asset-mods/implementation-notes/datatable-check.md`.
- OPEN (user input needed): Spec 09 real pak build. `pakmod.py` and `datatable-vanilla` are built and tested without a pak tool. To verify the chain, the user supplies UnrealPak or `retoc`, an edited `DT_Items` asset and possibly the AES key, and writes `harness/pakmod.local.json` (`harness/README.md`, section "Asset mods"). Notes: `09-asset-mods/implementation-notes/tooling.md`.
