# King's Favour write (spike 1.1)

Run 20261106-000620-91e6 (slot 1, fixture `playtest-noai`, test scenario `probe-contract-costs`, variant `favour`).

- Start: `kingsFavour` 0, `getKingsFavour_daysLeft()` 249.
- `changeKingsFavour(10)` on the player pawn (harness action `add_kings_favour`): `kingsFavour` 0 to 10. No error.
- The value stayed 10 after 6 game seconds and after one game day.
- `getKingsFavour_daysLeft()` counted down: 249, 248, 247. The game may use it for a timed effect. What the value does in the game is not known and was not checked.

Verdict: the mod reward `kings_favour` calls `changeKingsFavour(amount)` and reads the value back. No fallback is needed.
