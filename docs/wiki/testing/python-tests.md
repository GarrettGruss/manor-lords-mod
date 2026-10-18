---
type: Testing
title: Python tests and coverage
description: The Python unit tests of the harness (runlib, suitelib, releaselib, tools, install scripts), the full test set and how to run it, test helpers and fakes, and the coverage tool for the Invasion Mode criteria.
tags: [testing, unittest, python, coverage, criteria]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T15:30:28Z }
sources:
  - resource: repo://harness/tests/
  - resource: repo://harness/tools/coverage.py
  - resource: repo://harness/runlib/fake_phases.py
  - resource: repo://harness/tests/stub_launcher.py
  - resource: repo://harness/tests/suitelib_fakes.py
  - resource: repo://docs/harness/10-invasion-testability/criteria.json
  - resource: repo://.claude/skills/harness-coverage/SKILL.md
  - resource: repo://.claude/skills/harness-git-workflow/SKILL.md
  - resource: repo://pyproject.toml
  - resource: repo://CLAUDE.md
---

# Python tests and coverage

All harness tests are `unittest` files in `harness/tests/`. No game is needed for them. Lua mods are tested by the [fake game kit](fake-game-kit.md). This page covers the Python side and the coverage tool.

## Run the tests

Start every Python command with `uv run python` (CLAUDE.md). Run from the repo root.

```
uv run python -m unittest discover -s harness/tests -p "test_runlib*.py"
uv run python -m unittest discover -s harness/tests -p "test_suitelib*.py"
uv run python -m unittest discover -s harness/tests -p "test_harness_tools*.py"
uv run python -m unittest discover -s harness/tests -p "test_reload_mods.py"
uv run python -m unittest discover -s harness/tests -p "test_pakmod.py"
uv run python -m unittest discover -s harness/tests -p "test_coverage.py"
uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"
uv run python -m unittest discover -s harness/tests -p "test_telemetry_mock.py"
uv run python harness/tests/lua_syntax.py
uv run python harness/tests/boot_state_machine.py
uv run python harness/tools/coverage.py --check-spec
```

The full set that must pass before a merge is the list in the [git workflow skill](../../../.claude/skills/harness-git-workflow/SKILL.md): `test_runlib*`, `test_suitelib*`, `test_harness_tools*`, `test_reload_mods`, `test_pakmod`, `test_coverage`, `test_fakegame_*`, `test_telemetry_mock`, `lua_syntax.py`, `boot_state_machine.py`, and `coverage.py --check-spec`. Run only the suites you touched while you work, then the full set. `lupa` is a dependency declared in `pyproject.toml`; `uv run` installs it.

A test file imports a path helper first, so its package is importable: `runlib_path` (adds `harness/`), `harness_tools_path` (adds `harness/` and `mcp/`), `fakegame_path` (adds `harness/tests/`).

## Test groups

| Group | Files | What they check |
|---|---|---|
| runlib | `test_runlib_*.py` (about 35 files) | The run launcher library `harness/runlib/`: phases and runner, run folder, summary, scenario loading, expectations, actions and action checks, mod state, fixtures, save slots, game reads, popups, screenshot, timers, waiting, battle, raids, sack, soak, series, variants. See [Run launcher](../workflows/scenario-run.md). |
| suitelib | `test_suitelib_*.py` | Suite files, the worker pool, the launcher, runner, report, stats, and A/B runs. They call a stub launcher instead of the game. |
| releaselib | `test_release_cli.py`, `_gate`, `_manifest`, `_zip` | `harness/release.py` and `harness/releaselib/`. See [Mod releases](../workflows/releases.md). |
| MCP and tools | `test_harness_tools_mcp.py`, `_scenarios.py`, `_tools.py` | The `manor-harness` MCP server in `mcp/harness_tools/`. See [Harness MCP tools](../integrations/harness-mcp-tools.md). |
| Pak tools | `test_pakmod.py`, `test_modpak.py`, `test_genmesh.py` | Pak extraction and patching, mod pak building, Meshy helpers. See [Pak mods](../workflows/pak-mods.md). |
| Install and slots | `test_install_scripts.py`, `test_parallel_slots.py` | `install.ps1` and `uninstall.ps1` with temp folders and real PowerShell (skipped when PowerShell is missing), and parallel game slots. |
| Lua mods | `test_fakegame_*.py`, `test_telemetry_mock.py`, `lua_syntax.py`, `boot_state_machine.py` | See [Fake game kit](fake-game-kit.md). |
| Rules | `test_boundary.py`, `test_save_call_sites.py`, `test_invasion_plan_roles.py`, `test_bandits_rules.py` | Repo rules as tests. `test_boundary.py` fails if harness code names the Invasion Mod (spec 22: the harness must not know the mod). `test_save_call_sites.py` fails if any code file other than `HarnessSave.lua` names a game save function. |
| Tools | `test_coverage.py`, `test_wiki_tool.py`, `test_reload_mods.py` | `harness/tools/coverage.py`, `harness/tools/wiki.py`, `harness/tools/reload_mods.py`. |

## Fakes and helpers

- `harness/runlib/fake_phases.py` has fake launcher phases with the real phase names. `harness/run.py --fake <outcome>` runs them with no game. `test_runlib_runner.py` and `test_runlib_phases.py` use them to test `execute_run` and the failure outcomes.
- `harness/tests/stub_launcher.py` is a small script that stands in for `run.py`. It keeps a step state file under a lock and writes a `summary.json`. The `test_suitelib_*` tests start it as the launcher.
- `harness/tests/suitelib_fakes.py` has `make_suite`, `entry`, `result`, `summary`, `FakeClock` and `FakeRunOne` to test the suite runner without a process or real time.
- `modstate_support.py`, `battle_support.py`, `saveslot_support.py` build fake worlds for the fake game kit tests.

A test must not touch the real save folder, the real game folder or the network. Use temp folders (`tempfile`). Several tests build a small git repo in a temp folder (`test_wiki_tool.py`).

## Coverage tool

`harness/tools/coverage.py` measures how much of the Invasion Mode brief is testable (spec 10, upgrade U8). It uses only the standard library.

Inputs:

- `docs/harness/10-invasion-testability/criteria.json`: the source of truth, 40 criteria. Each has `id, title, pillar, mark, method, blocked_by, spikes, upgrades, method_verified, verified_by, reason_human, spike_note`. Mark `A` is automatable, `P` partly, `H` human.
- Scenario files in `harness/scenarios/`. The tool reads the module constants `NAME` and `COVERS` with `ast` and never runs the file. `COVERS` is a list of criterion ids.
- `runs/*/summary.json`. `last_passing_runs` maps each scenario to its newest run with verdict `pass`. A broken summary is skipped. A newer failing run does not remove an older pass.

How `compute` decides:

- Automatable criteria are the `A` and `P` ones. A criterion is verified when `method_verified` is true or a scenario that covers it has a passing run.
- A gap is an automatable criterion that is not verified and that no scenario covers.
- An id in `COVERS` that is not in `criteria.json` is an error and the exit code is 2.

Commands (see the [coverage skill](../../../.claude/skills/harness-coverage/SKILL.md)):

```
uv run python harness/tools/coverage.py                     # shares, blocked list, gap list
uv run python harness/tools/coverage.py --json
uv run python harness/tools/coverage.py --min-verified 0.9  # exit 1 if the share is lower
uv run python harness/tools/coverage.py --check-spec        # criteria.json against the spec README tables
```

Exit codes: 0 ok, 1 a check failed (`--min-verified` or `--check-spec`), 2 bad input or an unknown id. The goal is at least 90% verified of the `A` and `P` criteria. Get the current number from the tool; do not quote an old one.

Set `method_verified: true` only when a scenario tagged with the criterion passed 3 of 3 real-game runs and checks the criterion itself. Keep the line endings of `criteria.json`, then run `--check-spec`. See [Scenarios](../workflows/scenario-run.md) for how runs produce `summary.json`.

## Rules for new tests

- A new feature gets a test in the same commit.
- Prefer ranges over exact values for anything the game simulates (CLAUDE.md: the simulation is not deterministic).
- A new scenario file is listed in the scenario list test of `test_runlib_scenario.py`. Merge conflicts there keep both sides (git workflow skill).
- Fail loudly: assert on a clear message, do not catch and ignore errors.

## Platform

The project runs the tests on Windows. Some `test_runlib*`, `test_parallel_slots` and many `test_fakegame_*` tests fail on Linux or WSL, because they use Windows paths, PowerShell or the Windows `mkdir` of `HarnessLog` (see [Fake game kit](fake-game-kit.md#windows-only)). The platform-neutral groups (`test_suitelib*`, `test_harness_tools*`, `test_coverage`, `test_release_*`, `test_wiki_tool`) also pass there. Run the full set on Windows before you merge.
