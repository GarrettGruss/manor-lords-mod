# Design: Spike mod state limits

## Open questions
| Question | Who decides | How it is answered |
|---|---|---|
| How many entries and how long can the Tags hold before save or load slows or fails? | A spike | Task 1.1 |
| Do Tags on AI lords or buildings survive a save and a load? | A spike | Task 1.2 |
| Do a quick save and an autosave keep the pawn Tags? | A spike, with the user playing | Task 1.3 |
| What happens to the stale slot `saveGame_48`? | The user | Task 2.1 |
| Is option C (a side file) needed? | The user, after 1.1 | Only if 1.1 shows the limit is too low for a planned feature. |
