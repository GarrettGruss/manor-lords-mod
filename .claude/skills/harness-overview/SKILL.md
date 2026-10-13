---
name: harness-overview
description: Orientation for the Manor Lords mod harness: what exists, where it lives, which skill to use for which task. Read this first when you start work in this repo or are unsure which harness tool to use.
---

# Manor Lords mod harness: overview

The loop: edit a mod, deploy it, run the real game, observe, repeat. Details are in `CLAUDE.md` and `docs/specs/00-harness-overview/README.md` (the roadmap of specs 00 to 16).

## Parts
- `mod/`: Lua mods for RE-UE4SS (HarnessBoot, HarnessLog, HarnessTelemetry, HarnessActions, HarnessReload, and the stand-ins InvasionStandIn and RaidStandIn). Shared modules (each has a fake-game test): HarnessWalls (walls and roads), HarnessManor (manor goods and worker slots), HarnessBuild (building placement data), HarnessUi (Lua screens and banners), HarnessHousing, HarnessBandits (settle raiders), HarnessPolicies (policy edicts), plus HarnessLords, HarnessSack, HarnessRaids, HarnessUnits, HarnessBattle, HarnessLoot, HarnessDataTable. They are in `mod/shared/<Name>/<Name>.lua`. Each mod has its own Lua state.
- `harness/`: `run.py` (one run), `run_series.py`, `suite.py` (suites, baselines, A/B), `deploy.ps1`, `runlib/` (library), `scenarios/`, `suites/`, `tools/` (`coverage.py`, `pakmod.py`, `reload_mods.py`, `fixtures.py`).
- `mcp/harness_tools` (server `manor-harness`: run_scenario, wait_for_run, read_summary, read_log, ...) and the `ue4ss-bridge` MCP server (live queries into a running game).
- `docs/specs/NN-name/`: one spec per core feature, with `implementation-notes/` for findings.
- Git-ignored: `runs/`, `modtools/` (repak, UAssetGUI, work files, the AES key), `harness/pakmod.local.json`, `slots/`.

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

## Facts that save time
- UE 5.5.4 shipping game. Game folder `C:\Program Files (x86)\Steam\steamapps\common\Manor Lords`. The game runs without Steam.
- A game day is 40 game seconds. Speeds 1x/4x/8x. Intro cinematic ends about 13 s after load.
- The simulation is not deterministic: assert ranges, and use A/B runs for stochastic behavior.
- Never call a function that saves (CLAUDE.md Safety). A run installs its fixture save into the user's save folder under a free slot name, loads it, and removes it at the end; the user's saves are hashed before and after (spec 06, part D). `harness/tools/load_save.py <fixture | .sav path>` opens the game on a save.
- Building placement works only with a real OS mouse click (hidden scenario `place-building`).
- The game drops to 1x when an army is spotted (often when armies march through forest). Hold the speed with `ctx.time.run_game_*`, or set it again every second in a spike.
- Raw Lua eval through the bridge is approved for experiments only (2026-10-10).
- Python: start every command with `uv run python` (scripts, `-m unittest`, fake-game tests). Never `python`, `python3`, `py` or `python -`: they are the Windows Store stub and hang. Dependencies: `pyproject.toml` and `uv.lock` (`uv add`).
- Shells: Git Bash may have no `gh` on the PATH. Use `C:\Program Files\GitHub CLI\gh.exe`. Bash heredocs mangle quotes: use the Write tool for files.
- Spec 10 (`docs/specs/10-invasion-testability/`) is the plan for testing the Invasion Mode brief. Spec 11 (parallel game slots) is proposed. Specs 12 to 16 are spikes: 12 manor exploration, 13 mod inspection, 14 free walls, 15 bandit settlement (refugee waves), 16 policy edicts. Spec status lines: `docs/specs/00-harness-overview/README.md`.
- Writing rules: simplified technical English, short sentences, one term per thing.
