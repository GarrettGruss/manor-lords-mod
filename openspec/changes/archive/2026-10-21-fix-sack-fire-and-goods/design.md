# Design: Fix sack fire and goods

## Context
- The sack runs when a role raid begins to leave (`sack.lost_reasons`). The default `sack.method` is `collapse`: rubble at once, goods stay in the stock. The `fire` method sets fires; its config comment says goods inside a burned building are lost.
- Villagers fight fires unless enemy soldiers are in the village; then they flee (owner, 2026-10-20).

## Decisions
- The sack takes buildings and families only. The stock share is removed (owner, 2026-10-20).
- The mod removes no goods in a sack. Fire may destroy part of the goods of a burned store; the owner accepted this (2026-10-21). The mod does not move or add them back.

## Open questions
| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 1 | With raiders in the village, do villagers flee and leave the fires, and do buildings turn to rubble? Is the flee state tied to nearby soldiers or to the alarm bell? | A spike | Task 1.1 |
| 2 | How long does a fire take to make rubble with no firefighting? This sets the time limit. | A spike | Task 1.1 |
| 3 | Does a burned store lose its goods? Answered: yes, 11 to 60 percent; the owner accepts it (2026-10-21). | Owner | Done |
| 5 | Should the sack run later, when raiders stand in the village? The current timing is kept. | Owner | Open |
| 4 | Are the raiders still in the village when the sack runs (the raid begins to leave)? If not, when should the sack run? | A spike | Task 1.1 |
