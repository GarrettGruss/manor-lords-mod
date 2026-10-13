---
name: harness-coverage
description: Measure and update how much of the Invasion Mode brief is testable (the 90% goal of spec 10). Use when marking a criterion verified, running the coverage tool, or planning which spike to do next.
---

# Coverage of the Invasion Mode criteria

Source of truth: `docs/specs/10-invasion-testability/criteria.json` (40 criteria). The spec README has the same table. The tool: `harness/tools/coverage.py`.

## Commands
```
uv run python harness\tools\coverage.py              # shares, blocked list, gap list
uv run python harness\tools\coverage.py --check-spec # criteria.json and the spec tables must agree
uv run python harness\tools\coverage.py --json
uv run python harness\tools\coverage.py --min-verified 0.9   # exit code for a gate
```
The goal is: at least 90% of the A and P criteria have a verified method (36 of 39 on 2026-10-12, 92 %; Q3, a human judgment, is not counted).

## Entry fields
`id, title, pillar, mark (A automatable, P partly, H human), method, blocked_by, spikes, upgrades, method_verified, verified_by, reason_human, spike_note`.

## When to set `method_verified: true`
Only when ALL of these hold:
1. A scenario tagged with the criterion in `COVERS` passed 3 of 3 real-game runs (`harness-run-scenario`).
2. The scenario checks the criterion itself, not a neighbour of it.
3. `verified_by` lists the scenario name(s) and the spike note. `spike_note` says what is toy or mod-defined ("method verified on the stand-in mod; the real mod still has to pass").
If a primitive does not work, leave it false and write the reason in `spike_note`. Do not fake it, and do not count a planned scenario (`verified_by` may say `planned: scenario <name>`).

## What "verified" means for mod-defined rules
The base game lacks outposts, captives, tribute, raid objectives and more. The mod will build them. A stand-in mod (skill `harness-mod-state`) proves the test method. The criterion is then method-verified, and it passes only when the real mod passes the same scenarios.

## Steps after any verification
1. Edit `criteria.json` (keep the file's line endings) and run `--check-spec`.
2. Write the new numbers in a `coverage-after-<topic>.md` note in `implementation-notes/` and update the spec README status.
3. Add a CHANGELOG line.

## Planning the next step
The gap list in the tool output is the work list. Prefer the primitive that unlocks several criteria (for example sack primitives unlock S1, R7, R8). Engine-dependent criteria need a real-game spike (skill `harness-game-spike`).
