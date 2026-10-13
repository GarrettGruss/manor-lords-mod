---
name: harness-write-scenario
description: Write or change a harness scenario (a Python file in harness/scenarios) with assertions, metrics and coverage tags. Use when adding a test for a mod feature or a criterion.
---

# Write a scenario

A scenario is one Python file in `harness/scenarios/`. The runner finds it by its module attributes.

## Module format
```python
NAME = "my-scenario"          # lowercase words with dashes, unique
DESCRIPTION = "What it proves, what mods it needs."
LIMIT_S = 60                  # wall seconds; above 300 also needs LONG_REASON = "why"; max 4200
COVERS = ["R5"]               # criteria ids of spec 10; a literal list (it is read with ast)
HIDDEN = False                # True for probes and for tests that use the real mouse

def run(ctx) -> dict:
    ...
    return ctx.result()
```
Add the name to the scenario list in `harness/tests/test_runlib_scenario.py` (a test compares the full list).

## The context (`ctx`)
- `ctx.expect`: `equals`, `in_range`, `at_least`, `at_most`, `changed`, `eventually(name, fn, timeout_s)`. Each call records one assert. Sets are saved as sorted lists.
- `ctx.actions`: base-game actions (give goods, spawn raiders, sack, close pop-ups, and so on). The list is in `docs/specs/07-feature-test-kit/implementation-notes/actions-catalog.md`.
- `ctx.mod`: commands and metrics of a mod that defines its own state (see the skill `harness-mod-state`).
- `ctx.run_until(predicate, timeout_s, clock="wall"|"game", stall_s=..., on_poll=ctx.popups)`: wait with a stall detector.
- `ctx.time`, `ctx.read_clock()`, `ctx.read_calendar()`, `ctx.pause()`, `ctx.unpause()`: game time. A game day is 40 game seconds. Speeds are index 1/2/3 = 1x/4x/8x.
- `ctx.metric(name, value)`: a number for A/B statistics (see `harness-ab-testing`).
- `ctx.screenshot(name)`, `ctx.snapshot()`, `ctx.notes`, `ctx.fail(name, reason)`.

## Rules
- The game is not deterministic. Assert ranges, not exact values, for anything stochastic. Use `equals` for flags and names.
- Keep asserts few and named so the 4 KB summary stays readable (`R5 five captives are held`).
- A failing assert is a `fail`. A bug in your code is a `harness_error`. Do not catch errors to hide them.
- Never call a save function. Scenarios that need the real mouse (`place_building`) are `HIDDEN` and run alone.
- Long scenarios need `LONG_REASON` and the pop-up guard (`ctx.popups`). A pop-up pauses the game.
- Use `COVERS` only for a criterion whose method the scenario really proves. The coverage tool counts a passing tagged scenario.

## Test it without the game
Run it in the fake game kit (Lua mods in a Lua runtime, fake bridge). See `harness/tests/test_fakegame_standin_scenarios.py` and `harness/tests/modstate_support.py`. Include a broken-rule case that must make the scenario fail.
`uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"`

Then run it in the real game 3 of 3 (skill `harness-run-scenario`).
