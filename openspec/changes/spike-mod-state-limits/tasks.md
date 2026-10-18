## 1. Tests
- [ ] 1.1 Limit test: write 10, 100 and 1000 entries and one long entry, make a harness save with `save_game`, load it. Verified by a real run and `notes/tags-limits.md` (counts, sizes, times as ranges).
- [ ] 1.2 Write a marker in the Tags of an AI lord and of one building, save, load, read back. Verified by a real run. Never write Tags through the bridge `set` (it crashes the game); use Lua `FName`.
- [ ] 1.3 Ask the user to make a quick save and wait for an autosave, then load and read the pawn Tags. Verified by a real run and a note. No probe calls a save function.

## 2. Decisions
- [ ] 2.1 Ask the user about the stale slot `saveGame_48`. Verified by the answer in the note.
- [ ] 2.2 Decide with the user if option C is needed. Verified by the answer in `design.md`.

## 3. Close
- [ ] 3.1 Add a limit test scenario if the numbers are stable. Verified by `mod/InvasionMod/scenarios/` or `harness/scenarios/` and a real run.
- [ ] 3.2 Update the wiki page on ModState and `CHANGELOG.md`. Verified by `wiki.py check`.
- [ ] 3.3 Fill the test results table of the implementation pull request.
