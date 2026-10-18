# M14: plundered-start

Status: **out of scope for the first release** (M00 decision 25, 2026-10-16).

Feature folder: `plundered_start`. Batch 7.

## Goal
The game starts in a damaged village: ruins, a small and scared population, low supplies.

## Player rules (from M00)
- Preferred start: a village that was recently plundered.
- Fallback: the normal settler start, with a raid story event in the first days.
- The home region has plentiful but finite resources (M10).

## Current state
Not started.

## Proven building blocks
- There is no start setting for a plundered village. Use `sack_village` (`buildings_pct`, `stock_pct`, `people_pct`, method `fire`) and `sack_people` in the first game days, then family commands for the family count: `openspec/changes/archive/2026-10-15-legacy-26-game-start-settings/implementation-notes/claim-victory-test.md` (lines 49 and 50), `start-settings.md`.
- Sack by share: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-S6.md`.
- Depopulation ends the game: `spike-S8.md`. Keep people alive.
- Fixtures and the start flow: `openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/README.md`.
- Goals = Endless: `openspec/changes/archive/2026-10-15-legacy-26-game-start-settings/README.md`.

## Tunables (M00)
- Share of buildings, stock and people lost in the start sack. M00 gives no numbers.

## Dependencies
- M01 (a start-done flag). Goals = Endless from spec 26.
- M02 and M03 are not needed.

## Open questions
1. Which shares make a "recently plundered" village that is still playable?
2. When does the start sack run: on the first load, or at the first game day? How does the mod avoid a repeat after a load (a flag in mod state)?
3. Should the first raid story event be a raid of M02?
4. Do ruins from a sack rebuild at partial cost (M03)?

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | start-sack | Run the start sack once, in a new game. | not started |
