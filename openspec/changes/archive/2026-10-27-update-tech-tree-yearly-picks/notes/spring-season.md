# Spring value of the calendar season (task 1.3)

Question: which value of `TemporalComponent.Season` is spring? The tech tree needs it for `config.tech_tree.spring_season`.

## Method (real game, read plus the proven `set_season` action)
Scenario `tech-tree-picks-roundtrip` (run 20261028-004303-31fa, fixture `base-corpse-pit`). The test action `set_season` jumps the calendar with `RTSMultiEngineCPP:setDay(n)` and checks the `Season` property it reads back. No save function is involved in this step. The new-game fixture started at day 270.

| Action | Day | `Season` read back | Meaning |
|---|---|---|---|
| fixture start | 270 | 3 | autumn |
| `set_season("summer")` | 200 | 2 | summer |
| `set_season("spring")` | 100 | 1 | spring |

Older measurements agree (`openspec/changes/archive/2026-10-15-legacy-04-telemetry-and-assertions/implementation-notes/time-measurements.md` and the actions catalog): winter 0, spring 1, summer 2, autumn 3. The year starts in winter (day 1 is `Season` 0).

## Result
`spring_season = 1`. The scenario reads `invasion_yearly_state.season` after the jump and checks it equals 1 (assert P3, metric `spring_value`).

## Notes
- A new year starts in winter (0), so spring is the second season of the counter. The season counter of `invasion` (`yearly_season_no`) counts every change, so a pick is given when `Season == 1` and the counter is above `tech_spring_no`.
- A jump with `setDay` counts as a season change for the counter (the daily step of `invasion` sees the new `Season`). The picks therefore also follow a jump in test scenarios.
