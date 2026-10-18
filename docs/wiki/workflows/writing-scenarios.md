---
type: Workflow
title: Writing scenarios
description: How to write a harness scenario module, the ScenarioContext API (time, expect, run_until, actions, metrics, mouse), limits, coverage tags, hidden scenarios, mod-owned scenarios and tests.
tags: [scenario, harness, assertions, testing]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T15:30:28Z }
sources:
  - resource: repo://harness/runlib/scenario.py
  - resource: repo://harness/runlib/scenario_context.py
  - resource: repo://harness/runlib/timectl.py
  - resource: repo://harness/runlib/expectations.py
  - resource: repo://harness/runlib/waiting.py
  - resource: repo://harness/runlib/telemetry.py
  - resource: repo://harness/scenarios/smoke.py
  - resource: repo://harness/tools/coverage.py
  - resource: repo://harness/tests/test_runlib_scenario.py
  - resource: repo://.claude/skills/harness-write-scenario/SKILL.md
---

# Writing scenarios

A scenario is a Python module with a `run(ctx)` function. `harness/run.py` imports it, starts the game, and calls `run(ctx)` in the scenario phase. See [Scenario run](scenario-run.md) for the phases around it. The scenario returns `ctx.result()`. The runner stores the asserts in `scenario.json` and `summary.json`.

## Module contract

The registry is `harness/runlib/scenario.py`. It imports every module of `harness/scenarios/` and `mod/*/scenarios/**/*.py` at import time (`load_scenario_modules`, `load_mod_scenarios`).

| Attribute | Meaning |
|---|---|
| `NAME` | Scenario name. Default: the file name with `_` changed to `-`. Must be unique. |
| `LIMIT_S` | Required. Hard wall time limit for the whole scenario. |
| `LONG_REASON` | Required when `LIMIT_S` is above 300 s. |
| `HIDDEN` | `True` hides the scenario from the default list (probes, tests with the real mouse). |
| `EXCLUSIVE` | `True` if the scenario needs the screen, mouse or keyboard for long. A parallel suite runs it with no other game. |
| `run(ctx)` | The function. Returns `ctx.result()`. |
| `COVERS` | A literal list of criteria ids of spec 10. `harness/tools/coverage.py` reads it with `ast`, so it must be a literal. |
| module docstring | The first line becomes the summary in the scenario list. |

Rules enforced by `check_limit`:
- `LIMIT_S` must be above 0 and at most `MAX_LIMIT_S` (13500 s, enough for a 2-game-year soak).
- Above `LONG_LIMIT_S` (300 s) a non-empty `LONG_REASON` is required. Without it the import fails.
- A name defined twice in two different files fails at import. The same file twice is ignored.
- A mod keeps its scenarios in `mod/<Name>/scenarios/**/*.py`. A file name that starts with `_` is a helper and is not loaded.

`run_timeout_s(name)` gives the launcher kill timer: `LIMIT_S` plus 1200 s, at least 900 s. [Suites](suites-and-ab.md) and `run_series.py` use it.

Smallest example: `harness/scenarios/smoke.py`.

```python
NAME = "smoke"
LIMIT_S = 60
def run(ctx) -> dict:
    clock = ctx.read_clock()
    ctx.check("clock is stopped after boot", clock["paused"], clock["change"], [0, 0.001])
    return ctx.result()
```

## The context

`ScenarioContext` (`harness/runlib/scenario_context.py`) is built per run. It holds the bridge, the run folder, a flushed log (`scenario.log`) and these helpers.

| Member | Job |
|---|---|
| `ctx.expect` | Assertions: `equals`, `in_range`, `at_least`, `at_most`, `changed`, `eventually(name, fn, timeout_s)`. Each call adds one record `{name, ok, value, rule}`. |
| `ctx.check`, `ctx.check_range` | Plain forms. Prefer `ctx.expect`. |
| `ctx.fail(name, reason)` | Record a failed assert and return the result. Use it for an impossible action. |
| `ctx.actions` | Named base-game actions (give goods, spawn raiders, `save_game`, and others). The list is in the [actions catalog](../../../openspec/changes/archive/2026-10-15-legacy-07-feature-test-kit/implementation-notes/actions-catalog.md). |
| `ctx.mod` | Commands and metrics served by a mod itself. See [Mod commands and state](../concepts/mod-commands-and-state.md). |
| `ctx.commands`, `ctx.mod_commands` | File channels to the harness mods (`commands/`, `modcmd/` in the run folder). |
| `ctx.time` | `TimeControl`: `set_speed`, `pause`, `run_game_seconds`, `run_game_days`. |
| `ctx.read_clock()`, `ctx.read_calendar()`, `ctx.pause()`, `ctx.unpause()` | Direct clock helpers through the bridge. |
| `ctx.run_until(predicate, timeout_s, clock=, stall_s=, on_poll=, on_stall=)` | Poll a condition. See below. |
| `ctx.telemetry` | `TelemetryReader`: `read()` and `window(start_clock, end_clock)` over `telemetry.jsonl`. |
| `ctx.snapshot()` | A state snapshot through the bridge. |
| `ctx.metric(name, value)` | One number for A/B statistics, written to `metrics.json`. |
| `ctx.variant_option(name, default)` | The `--env NAME=VALUE` value of this run. |
| `ctx.screenshot(name)` | Capture the game window. |
| `ctx.notes` | Free text lines added to the result. |
| `ctx.popups` | Pop-up guard. Presses Accept on open pop-ups. |

### Assertions

`Expectations` (`harness/runlib/expectations.py`) records and logs each assert. A rule text is cut to 60 characters so `summary.json` stays under 4 KB. Sets are stored as sorted lists. `eventually` polls every 0.5 s and records the wait time as the value. The result is `passed` only if every record is ok. A failing assert gives verdict `fail`. An exception in your code gives `harness_error`. Do not catch errors to hide them.

### Waiting

`ctx.run_until` wraps `runlib/waiting.py:run_until`.
- `clock="wall"` counts wall seconds. `clock="game"` counts game seconds and follows the speed. A paused game never times out on the game clock, so add a wall limit or `stall_s`.
- The stall detector watches the game clock. If it stands still for `stall_s`, `on_stall` may repair (for example `ctx.popups`). A second stall raises `GameStalled`.
- Failures raise `WaitTimeout` or `GameStalled`. Both are `ScenarioFailure`, so the runner reports `fail`, not `harness_error`.
- The game does not run by itself after boot. Start it first, for example with `ctx.time.set_speed(1)`.

### Game time

Facts in [time measurements](../../../openspec/changes/archive/2026-10-15-legacy-04-telemetry-and-assertions/implementation-notes/time-measurements.md): speed index 1, 2, 3 gives 1, 4, 8 game seconds per wall second. One game day is 40 game seconds. The game drops to 1x when an army is spotted. `TimeControl` checks the speed about once a second and sets it again. It calls the guard (`ctx.popups`) every 2 s, so pop-ups do not stall a run. `run_game_*` methods derive their wall limit as 3 times the expected time plus 10 s, and pause after a timeout. Errors raise `TimeControlError`.

### Real mouse and keyboard

`ctx.order_with_mouse`, `click_with_mouse`, `hover_with_mouse` and `press_key` use the real OS input. Each takes the shared lock `runs/.input.lock` (`os_input_lock`, 300 s wait), so two game slots never move the one cursor at once. Mark such a scenario `HIDDEN` (and `EXCLUSIVE` when it holds the screen long). A hook only sees Blueprint calls, so native UI actions fire no hook. Read their effect with a count.

## Rules that must hold

- Assert ranges for anything stochastic. Use `equals` for flags and names.
- Keep asserts few and named, so the summary stays readable.
- Never call a save function. Use `ctx.actions.save_game(label, keep=False)`. It backs up the save folder, uses a free slot, removes its files at the run end unless `keep=True`, and raises if an existing file changes. See [Safety rules](../concepts/safety-rules.md).
- Never use `eval_lua` in a scenario. Use named commands.
- A long scenario needs `LONG_REASON` and the pop-up guard.
- Use `COVERS` only when the scenario really proves the criterion. The coverage tool counts a passing tagged scenario.
- A Python scenario cannot read `--env` values from `os.environ`, because they go to the game process. Use `ctx.variant_option`.

## Extend

1. Create `harness/scenarios/<name>.py` (or `mod/<Name>/scenarios/<feature>/<name>.py`).
2. Add the name to the scenario list in `harness/tests/test_runlib_scenario.py`. A test compares the full list.
3. Test it without the game in the fake game kit. See `harness/tests/test_fakegame_standin_scenarios.py` and `harness/tests/modstate_support.py`. Include a broken-rule case that must make the scenario fail.
4. Run it in the real game 3 of 3 (skill `harness-run-scenario`).
5. For a releasable mod, list the scenario in `gate_scenarios` of `mod/<Name>/mod.json`. See [Mod releases](releases.md).

## Tests

```
uv run python -m unittest discover -s harness/tests -p "test_runlib_*.py"
uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"
```

Covering tests: `test_runlib_scenario.py` (registry, limits, list), `test_runlib_expectations.py`, `test_runlib_waiting.py`, `test_runlib_timectl.py`, `test_runlib_modscenarios.py`, and the `test_fakegame_*` scenario tests.
