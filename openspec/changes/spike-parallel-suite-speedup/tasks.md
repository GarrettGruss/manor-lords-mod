## 1. Speedup
- [x] 1.1 Pick a suite with long runs and N runs per variant. Verified by the suite file in `harness/suites/`.
- [x] 1.2 Run it with `--slots 1` and with `--slots 3`. Verified by two `report.json` files.
- [x] 1.3 Compare wall time and the result ranges. Write `notes/speedup.md`. Verified by review of the note.

## 2. Exclusive scenario and conflicts
- [x] 2.1 Run a parallel suite with one `EXCLUSIVE` scenario. Verified by the run start and end times in `report.json`: no other run overlaps it.
- [x] 2.2 Check focus, audio and a second-instance lock during 3 parallel runs. Verified by the run summaries and `notes/conflicts.md`.
- [x] 2.3 Check that no slot folder, game file or key is in git. Verified by `git status` and a grep of the diff for the key.

## 3. Bridge timeout
- [x] 3.1 Count bridge timeouts in the parallel runs. Ask the user for the decision. Verified by the decision in `design.md`.
- [x] 3.2 If the user chooses a change, write a delta spec and a fake game test. Not needed: the owner kept the 15 s timeout.

## 4. Close
- [ ] 4.1 Update `CHANGELOG.md` and the skill `harness-run-scenario` if the advice on slots changes. Verified by review.
- [ ] 4.2 Close issue #151 with a comment. Verified by the issue state.
- [ ] 4.3 Fill the test results table of the implementation pull request.
