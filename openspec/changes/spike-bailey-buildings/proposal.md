# Proposal: find out if buildings can stand inside the manor bailey

Issue: #68. Legacy source: `openspec/changes/archive/2026-10-15-legacy-17-bailey-buildings/README.md`. Legacy issue: #68 (status: blocked, awaiting user).

## Why

Criterion M2 of the harness (spec 10) asks that the player can wall in a whole town. Normal buildings inside the manor bailey are refused with "Road Access obstructed". The mouse-free plot commit makes sites inside, but builders never finish them. Two retests gave the same result (legacy note `implementation-notes/bailey-buildings.md`).

Two causes are not separated yet: a bailey rule, or no reachable path (a wall ring with one gate). The legacy README says the spec folds into spec 12 as "not possible" unless the gate-free ring test is wanted.

## What Changes

- The owner decides: run the last tests, or fold the result into the spec 12 notes and close the issue.
- If the tests run: a gate-free ring test, and a test of reflected flags that the check might read.
- If a way works: a named command and a test scenario for criterion M2.

## Non-goals

- Changing the Keep limit (`maxInRegion`) or manor storage.
- New walls (that is the change `spike-blocking-wall-route`).
- Calling a save function outside the guarded action `save_game`.

## Legacy folders

- `openspec/changes/archive/2026-10-15-legacy-17-bailey-buildings/`
- `openspec/changes/archive/2026-10-15-legacy-12-manor-exploration/implementation-notes/` (rule search, `rule-search.md`)

## Capabilities

### New Capabilities
- None. This is a spike (`skip_specs`).

### Modified Capabilities
- None.

## Impact

- Probe scenario `harness/scenarios/probe_bailey.py` and the tools `harness/tools/s17_plots.py`, `s94_drive.py`.
- Notes in this change folder.
