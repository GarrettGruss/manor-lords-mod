# Design: Spike new row id persistence

## Open questions
| Question | Who decides | How it is answered |
|---|---|---|
| Does a building with id 1000 or 32767 survive a save and a load? | A spike | Task 1.1 |
| Does a new `DT_Upgrades` row work in the game? | A spike | Task 1.2 |
| Does an AI lord village with a new id in the table build, or crash? | A spike | Task 1.3 |
| Is the id rule still safe if one of these fails? | The user | Task 2.1 |
