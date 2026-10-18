# M07 iteration 01: notes

## Design
- The goal check runs in the scheduler poll (2 s). It reads `gameSetup.currentGameSetup.goals` through `HarnessGameSetup` and writes 2 when the value differs. It runs on every start and every load, because the poll has no memory of earlier writes. The counter `vassals_goal_writes` (ModState) shows how often the mod had to write.
- The registry has 3 slots in the pawn Tags (`invasion:vassal<N>_region|lord|loyalty|since_day`). TBD change from the README ("region Tags"): the pawn Tags are saved by ModState already, and the region actor save is not proven.
- A value equal to the key default writes no Tag (ModState keeps defaults implicit), so a loyalty of 50 shows no Tag until it changes.

## Findings
- Real game, new game on Jagged Cliffs (no AI lords): the start goal is 3 (Growth). The poll wrote 2 within the first poll (`goal_writes` 1 at the first read). A test write of 3 was undone by the next poll (`goal_writes` 2).
- `daysTotal` reads 0 right after a new game start. Use differences only.
- A claim with `consume` off still needs influence in the pawn for the first claim in the probe. The scenario sets 1000.
