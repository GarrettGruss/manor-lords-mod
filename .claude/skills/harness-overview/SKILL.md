---
name: harness-overview
description: Orientation for the Manor Lords mod harness: what exists, where it lives, which skill to use for which task. Read this first when you start work in this repo or are unsure which harness tool to use.
---

# Manor Lords mod harness: overview

The loop: edit a mod, deploy it, run the real game, observe, repeat. Details are in `CLAUDE.md` and `docs/harness/00-harness-overview/README.md` (the roadmap of specs 00 to 19).

## Parts
- `mod/`: Lua mods for RE-UE4SS (HarnessBoot, HarnessLog, HarnessTelemetry, HarnessActions, HarnessReload, the real feature mod RefugeeWaves (releasable, has `mod.json`), and the stand-ins InvasionStandIn and RaidStandIn). Shared modules (each has a fake-game test): ManorCore (player-safe game calls; the Harness modules call it; a released mod may need it), HarnessSteer (real right click, unit steering), HarnessParts (parts of composite buildings), HarnessWalls (walls and roads), HarnessManor (manor goods and worker slots), HarnessBuild (building placement data), HarnessUi (Lua screens and banners), HarnessHousing, HarnessBandits (settle raiders), HarnessPolicies (policy edicts), plus HarnessLords, HarnessSack, HarnessRaids, HarnessUnits, HarnessBattle, HarnessLoot, HarnessDataTable. They are in `mod/shared/<Name>/<Name>.lua`. Each mod has its own Lua state.
- `harness/`: `run.py` (one run), `run_series.py`, `suite.py` (suites, baselines, A/B), `deploy.ps1`, `runlib/` (library), `scenarios/`, `suites/`, `release.py` and `releaselib/` (mod releases), `tools/` (`coverage.py`, `pakmod.py`, `reload_mods.py`, `fixtures.py`).
- `mcp/harness_tools` (server `manor-harness`: run_scenario, wait_for_run, read_summary, read_log, ...) and the `ue4ss-bridge` MCP server (live queries into a running game).
- `docs/harness/NN-name/`: one spec per core feature, with `implementation-notes/` for findings.
- `docs/mod/`: the Invasion Mod docs (overview design `M00`, feature specs `M<NN>-<feature>/` with iterations). Layout and build rules of the mod: spec 22. Row id range spike: spec 23.
- Git-ignored: `runs/`, `modtools/` (repak, UAssetGUI, work files, the AES key), `harness/pakmod.local.json`, the fixture saves, `slots/`, `dist/`. A worktree has none of them: copy the fixture saves and `pakmod.local.json` from the main checkout. Compiled mod paks (`mod/<Name>/paks/*_P.pak`) may be committed. The AES key never.

## Which skill for which job
| Job | Skill |
|---|---|
| Run a scenario, read a verdict, repeat | `harness-run-scenario` |
| Write a new test | `harness-write-scenario` |
| Test logic that a mod defines (raids, outposts, captives) | `harness-mod-state` |
| Find out what the engine allows | `harness-game-spike` |
| Compare variants over many runs | `harness-ab-testing` |
| Change game data with a pak | `harness-pak-mod` |
| Find out why a run failed | `harness-debug-run` |
| Track the 90% goal for Invasion Mode | `harness-coverage` |
| Split work between agents | `harness-dispatch-agents` |
| Commit, PR, merge | `harness-git-workflow` |
| Release a mod to play testers | `harness-release` |

## Facts that save time
- UE 5.5.4 shipping game. Game folder `C:\Program Files (x86)\Steam\steamapps\common\Manor Lords`. The game runs without Steam.
- A game day is 40 game seconds. Speeds 1x/4x/8x. Intro cinematic ends about 13 s after load.
- The simulation is not deterministic: assert ranges, and use A/B runs for stochastic behavior.
- Never call a function that saves (CLAUDE.md Safety). A run installs its fixture save into the user's save folder under a free slot name, loads it, and removes it at the end; the user's saves are hashed before and after (spec 06, part D). `harness/tools/load_save.py <fixture | .sav path>` opens the game on a save.
- Building placement works only with a real OS mouse click (hidden scenario `place-building`). Hooks see only ProcessEvent (Blueprint) calls. Native UI actions (build mode, placement clicks) fire no hook.
- AES key: file `modtools/work/aes_key.txt` (git-ignored). Load it into `MANORLORDS_AES_KEY` inside each command. Never print it. In a worktree use the main checkout path `C:\Users\garre\development\manor-lords-mod\modtools\work\aes_key.txt`.
- Player silver and influence are the properties `silver` and `influence` of the player pawn (`MyPawnCPP_BP3_C`). The UI shows a change after the next action.
- Screenshot of the live game: `runlib.phases.capture_game_window(path, pids)`, or `ctx.screenshot(name)` in a scenario.
- Background shells can be killed by Claude Code when memory is low. Do not restart them on your own. Report it.
- The game drops to 1x when an army is spotted (often when armies march through forest). Hold the speed with `ctx.time.run_game_*`, or set it again every second in a spike.
- Raw Lua eval through the bridge is approved for experiments only (2026-10-10).
- Python: start every command with `uv run python` (scripts, `-m unittest`, fake-game tests). Never `python`, `python3`, `py`, `python -`, `python -c` or code through stdin: they are the Windows Store stub and hang. Dependencies: `pyproject.toml` and `uv.lock` (`uv add`).
- Shells: Git Bash may have no `gh` on the PATH. Use `C:\Program Files\GitHub CLI\gh.exe`. Bash heredocs mangle quotes: use the Write tool for files.
- Spec 10 (`docs/harness/10-invasion-testability/`) is the plan for testing the Invasion Mode brief. Spec 11 (parallel game slots) is proposed. Specs 12 to 18 are spikes and mods: 12 manor exploration, 13 mod inspection, 14 free walls, 15 bandit settlement (refugee waves, mod RefugeeWaves, `implementation-notes/settler-camp.md`), 16 policy edicts, 17 bailey buildings, 18 composite buildings (parts). Spec 19 is mod releases (skill `harness-release`). Spec status lines: `docs/harness/00-harness-overview/README.md`.
- Writing rules: simplified technical English, short sentences, one term per thing.
