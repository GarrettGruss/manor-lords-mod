## 1. Probes
- [x] 1.1 R3 real loot: read the equipped ids of killed raiders and move goods. Verified by a real run and a note with before and after counts.
- [x] 1.2 Stances: call `SetBehaviourStance` on an AI squad and watch the squad. Verified by a real run and a screenshot in `evidence/` if the result is visual. Result: the call works, its effect is not shown; see the note.
- [x] 1.3 Unit growth with `spawnCompleteUnit` during a challenge. Verified by a real run: army size range before and after.
- [x] 1.4 Read `Squad.camp` and `campLocation` of a waiting baron army. Verified by a real run and a note. Result: the fields cannot be read (a Squad struct read ends the game); see the note.
- [x] 1.5 Swap the mesh of one finished building with `LoadAsset_Blocking` and `SetStaticMesh`. Verified by a screenshot in `evidence/` and a collision check.

## 2. Close
- [x] 2.1 Write one note for each lead in `notes/`. Verified by review.
- [x] 2.2 Move engine facts that stay true into the wiki. Verified by `wiki.py check`.
- [ ] 2.3 Fill the test results table of the implementation pull request.
