# Proposal: Spike two year soak

Issue: #286. Legacy source: `docs/harness/10-invasion-testability/README.md` (criterion Q1, upgrade U9) and `docs/harness/10-invasion-testability/implementation-notes/open-items.md`.

## Why
Criterion Q1 says the game does not crash over a simulated 2-year run. A 3.3 hour soak reached day 333 of 730 with no crash and no memory growth. The clock slows over time (2.53 game s per wall s in the first hour, 1.11 over 3.3 hours). A scenario cannot chain runs, because each run loads the fixture again. The 730 day run is not reachable in one run. The soak also has no periodic raid (U9 "not built"). Details: `docs/harness/10-invasion-testability/implementation-notes/soak-results.md` and `open-items.md`.

## What Changes
- Decide how Q1 is proven: a longer single run (about 8 hours), a stronger start village, or a result that stays at 333 days as a stability proof.
- Add a periodic raid to the soak, if the user wants Q1 for raids.
- Investigate why the clock rate falls (a growing village is the suspect).

## Non-goals
- A save and load chain between runs (the save rules forbid ad hoc saves).
- Balance checks.

## Legacy folders
`docs/harness/10-invasion-testability/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None now. A longer soak scenario is a test scenario, not a harness behavior.

## Impact
One run needs hours of the game. Only one game at a time should run it. `criteria.json` (live data) changes only if Q1 changes state; see `move-coverage-criteria-to-openspec` for where it lives.
