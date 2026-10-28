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
A hook sees only Blueprint (ProcessEvent) calls. Native UI actions (build mode, placement clicks) fire no hook: read the effect with a count instead.
A mod may keep scenarios beside its files: `mod/<Name>/scenarios/**/*.py` (same module format; a file name that starts with `_` is a helper). Names must be unique across harness and mods; a duplicate fails at import.
Add the name to the scenario list in `harness/tests/test_runlib_scenario.py` (a test compares the full list).

## The context (`ctx`)
- `ctx.expect`: `equals`, `in_range`, `at_least`, `at_most`, `changed`, `eventually(name, fn, timeout_s)`. Each call records one assert. Sets are saved as sorted lists.
- `ctx.actions`: base-game actions (give goods, spawn raiders, sack, close pop-ups, and so on). The list is in `openspec/changes/archive/2026-10-15-legacy-07-feature-test-kit/implementation-notes/actions-catalog.md`.
- `ctx.mod`: commands and metrics of a mod that defines its own state (see the skill `harness-mod-state`).
- `ctx.run_until(predicate, timeout_s, clock="wall"|"game", stall_s=..., on_poll=ctx.popups)`: wait with a stall detector.
- `ctx.time`, `ctx.read_clock()`, `ctx.read_calendar()`, `ctx.pause()`, `ctx.unpause()`: game time. A game day is 40 game seconds. Speeds are index 1/2/3 = 1x/4x/8x. The game drops to 1x when an army is spotted: use `ctx.time.run_game_*` to hold the speed.
- `ctx.metric(name, value)`: a number for A/B statistics (see `harness-ab-testing`).
- `ctx.order_with_mouse(...)`: a real right click that sends a player squad to a point (HarnessSteer, spec 10). Lua-only orders do nothing. Scenarios with it are `HIDDEN`.
- `ctx.click_with_mouse(fx, fy)` (real left click on a UI button), `ctx.hover_with_mouse(fx, fy)` and `ctx.press_key(osinput.VK_F9)`: used by the scenarios `tech-tree-widget` and `tech-tree-widget-key`. Find a button by hover (poll `IsHovered` from a mod command). Repeated `bring_to_front` opened the Windows task switcher, so `focus_game` skips it when the game is in front. The tech window scenarios try the expected point of a button first (the state command gives the canvas position of each Border) and scan the window only when that fails. A picture scenario for evidence (`tech-tree-widget-layout`) minimizes the debug windows of other slots that lie over its game before `ctx.screenshot` (the harness minimizes only the debug windows of its own game). A real-mouse scenario can fail with `InputError: not in the foreground` when another slot takes the focus: run it again.
- `ctx.screenshot(name)` (a capture of the game window, `runlib.phases.capture_game_window`, saved as `runs/<id>/screenshots/<name>.png`), `ctx.snapshot()`, `ctx.notes`, `ctx.fail(name, reason)`.
- Picture evidence: a test scenario for a visual result (UI and text on screen, models, materials, placement and geometry, units in the world, world results the player sees) takes a `ctx.screenshot` at the moment that proves the criterion, with a clear name. Copy the picture, compressed and at most 1280x720, to `openspec/changes/<change-name>/evidence/` and list it in `evidence/README.md` with the test scenario and run id (CONTRIBUTING.md, Picture evidence).

## Rules
- The game is not deterministic. Assert ranges, not exact values, for anything stochastic. Use `equals` for flags and names.
- Keep asserts few and named so the 4 KB summary stays readable (`R5 five captives are held`).
- A failing assert is a `fail`. A bug in your code is a `harness_error`. Do not catch errors to hide them.
- Never call a save function. To save, use `ctx.actions.save_game(label, keep=False)` (spec 24): it backs up the save folder, uses a new free slot, deletes the files at the run end unless `keep=True`, and raises if an existing file changes. Scenarios that need the real mouse (`place_building`) are `HIDDEN` and run alone.
- Long scenarios need `LONG_REASON` and the pop-up guard (`ctx.popups`). A pop-up pauses the game. `ctx.time.run_*` closes pop-ups itself every 2 s.
- A test scenario of the Invasion Mod that starts a new game (`--new-game`) must call `scenario_settings_skip` or `scenario_settings_set` first (the settings menu pauses the game until "Begin the game"). A scenario on a fixture needs no call; it may set a value with `scenario_settings_set` (see `harness-mod-state`).
- Use `COVERS` only for a criterion whose method the scenario really proves. The coverage tool counts a passing tagged scenario.

## Test it without the game
Run it in the fake game kit (Lua mods in a Lua runtime, fake bridge). See `harness/tests/test_fakegame_standin_scenarios.py` and `harness/tests/modstate_support.py`. Include a broken-rule case that must make the scenario fail.
`uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"`
A scenario for a releasable mod can be a release gate: list it in `gate_scenarios` of `mod/<Name>/mod.json` (skill `harness-release`).

Then run it in the real game 3 of 3 (skill `harness-run-scenario`).
