# Design: Fix sack fire and goods

## Context
- The sack runs when a role raid begins to leave (`sack.lost_reasons`). The default `sack.method` is `collapse`: rubble at once, goods stay in the stock. The `fire` method sets fires; its config comment says goods inside a burned building are lost.
- Villagers fight fires unless enemy soldiers are in the village; then they flee (owner, 2026-10-20).

## Decisions
- The sack takes buildings and families only. The stock share is removed (owner, 2026-10-20).
- No goods are destroyed by a sack. If fire destroys the goods of a burned store, the mod must keep them (move them to another store first, or add them back), or the sack uses `collapse` for stores.

## Open questions
| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 1 | With raiders in the village, do villagers flee and leave the fires, and do buildings turn to rubble? Is the flee state tied to nearby soldiers or to the alarm bell? | A spike | Task 1.1 |
| 2 | How long does a fire take to make rubble with no firefighting? This sets the time limit. | A spike | Task 1.1 |
| 3 | Does a burned store lose its goods? If yes: keep the goods (move or add back) or use `collapse` for stores? | Spike, then the owner | Task 1.2 |
| 4 | Are the raiders still in the village when the sack runs (the raid begins to leave)? If not, when should the sack run? | A spike | Task 1.1 |
