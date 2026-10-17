# M04 iteration 02: notes

## How the game exposes the season
- `RTSMultiEngineCPP.TemporalComponent.Season`: 0 winter, 1 spring, 2 summer, 3 autumn. Winter covers day 1 to about 90 and the end of the year (see `docs/harness/04-telemetry-and-assertions/implementation-notes/time-measurements.md`).
- The mod does not use the year. Winter is one season that spans the year change, so a rule on `(Year, Season)` would roll twice in winter. The mod compares `Season` with the saved last season instead.

## Design
- ModState key `bandits_last_season` (default -1). The poll (1 s real time) reads `Season`.
  - Saved value -1: store the current season. No roll (a new game or a first run starts with no tick).
  - Season differs: save the new season first, then run the tick. An error in the tick cannot make a second tick.
  - Same season: nothing. A load restores the saved season, so the same season does not roll again.
- One roll per tick (decision 12). Chances from the bands are unchanged. `tick_days` is removed from the config.
- A jump back to an earlier season (test only, `set_season`) also rolls. In a normal game the season only moves forward.
- A save made before this iteration has no `bandits_last_season`. The first poll after the load stores the season and does not roll.

## Findings
- The fixture `base` starts in autumn (season 3, day 205). The first scenario run showed that a `set_season` before the first poll counts as a change. The scenario now waits until `last_season` is stored.
- Approval cannot be held at 0 for several game days (the game moves it back to about 71). A real run has order 71 at the tick.
- Crash rate: see the iteration file. Multi-day runs at speed 3 crashed in 4 of 5 runs, at speed 2 in 0 of 2.
