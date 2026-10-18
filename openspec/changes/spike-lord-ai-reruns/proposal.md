# Proposal: Spike lord AI reruns

Issue: #281. Legacy source: `docs/harness/10-invasion-testability/README.md` (spikes S11, S13, battlefield anchor, upgrade U3) and `docs/harness/10-invasion-testability/implementation-notes/open-items.md`.

## Why
Several spike results ran once and were never repeated:
- S11 (baron model): the probe `probe-lord-diplomacy` (`lord_claim`, `lord_declare_peace`, the "challenge lost" path) is written but not run.
- S13 (dynamic lords): the suite `lord-village-ab` was stopped after 2 runs. The second result differs from the first (the lord village stayed at 5 buildings, earlier it grew 4 to 14). "The lord builds" is not confirmed on the `base` fixture with other lords present.
- Battlefield anchor: the raid challenge check and the formal 3 against 3 A/B are open (`docs/harness/10-invasion-testability/implementation-notes/battlefield-anchor.md`).
- U3: a game-time `run_until` against the real game is not verified.

## What Changes
- Run these four checks again in the real game, with the memory care the notes ask for (one game at a time).
- Write each result to `notes/` and update the state in the mod features that depend on it.

## Non-goals
- New lord AI features.
- Save and load of a spawned lord (needs a save call; forbidden outside `save_game`).

## Legacy folders
`docs/harness/10-invasion-testability/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None now. A result that changes a command adds a requirement to `harness/raid-commands` or `harness/game-actions` in the implementation pull request.

## Impact
Needs the real game. The S13 suite stopped because the machine ran low on memory, so run it with one game and fewer background tasks.
