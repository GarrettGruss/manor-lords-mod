# How to tell the side of a unit (spec 28)

Date: 2026-10-16. Run: `s28-tune-check` (normal save, no registry).

## Method
A unit has no owner property. The side comes from the squad:
`unit.assignedSquadID.Value` -> the `commandedSquads` list of each `PawnCPP` -> pawn flags.
This is the method of spec 10 spike S3 (`HarnessUnits.squadMap`). HarnessTune reuses it.

| Pawn flags | Side name in tune commands |
|---|---|
| `isMainPlayer` | `player` |
| `isBandit` (the bandit pawn is also `isAI`) | `bandit` |
| `isAI` only (`PawnCPP_AI` lords) | `ai_lord` |
| none of these | `other` |
| unit has no squad (villager, animal, merchant) | no side, counted as `unowned_units` |

## Result in a normal game
`tune_state` on the run `s28-tune-check` (no harness spawn before) found: player 25 units (squads 27, 31), bandit 18 (squad 30), ai_lord 91 (squads 5, 6, 7), 201 units without owner. So the side detection works without the registry. No `other` squad was seen.

## Costs and limits
- One pass over all `SMUnit` plus the pawn list. About 335 units here. A `tune_state` call returned within the 100 ms poll.
- Squads of units bought or called up later appear in `commandedSquads` at once (the squads spawned by `spawn_units` were found in the next call).
