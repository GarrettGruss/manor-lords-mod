## 1. Setup

- [x] 1.1 Add the fixture `playtest-noai` to `harness/fixtures/fixtures.json` (entry in `notes/fixture.md`) and check that it loads.
- [ ] 1.2 Back up the save folder. Run the base fixture once as the control.

## 2. Question 1: bandit camps

- [ ] 2.1 Find the bandit pawn or faction actor with camps 0. Write `notes/bandit-camps.md`.
- [ ] 2.2 Try a camp spawn and a bandit squad spawn. Add the result to the note.
- [ ] 2.3 Try to create the bandit pawn if missing. Check `HarnessBattle` squad ownership.

## 3. Question 2: AI lord and construction

- [ ] 3.1 Find AI lord pawns in the world. Write `notes/ai-lord-construction.md`.
- [ ] 3.2 Assign a region to an AI pawn (`region.ownerPawn`, claim function). Record the result.
- [ ] 3.3 If no AI lord exists, try to spawn or enable one.
- [ ] 3.4 Watch for construction sites over 10 to 20 game days. Take pictures into `evidence/`.

## 4. Question 3: Hussite AI

- [ ] 4.1 Run the raid test scenarios of `invasion` and `raid_behavior` on the fixture and on base. Write `notes/hussite-raid.md` with a comparison table.
- [ ] 4.2 Force a raid with `invasion_plan_now`. Take pictures of the raid into `evidence/`, listed in `evidence/README.md`.

## 5. Close

- [ ] 5.1 Check the save folder against the backup after every run.
- [ ] 5.2 Write the recommendation. The owner decides which settings the mod needs.
- [ ] 5.3 Move lasting engine facts to `docs/wiki/`. Add the `CHANGELOG.md` line. Archive the change.
