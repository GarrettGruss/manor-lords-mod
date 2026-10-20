## 1. Spike

- [x] 1.1 Find the hook that fires once per player pawn after a load, after its autosave timer exists. Verified by a real `--keep-open` run, a load by the owner and `notes/load-hook.md`. No save function is called.

## 2. Build

- [x] 2.1 Push the timer away after each load after `READY`, with retries and a log line. Verified by a new fake game test in `harness/tests/test_fakegame_harnessautosave.py`.
- [x] 2.2 Log an error when the push fails after a load. Verified by a fake game test.
- [x] 2.3 Update the "Checked by" lines in the delta spec.

## 3. Close

- [ ] 3.1 Real check: `--keep-open` run, owner loads a save, `autosave_status` shows the timer far away. Verified by the run id in the pull request.
- [ ] 3.2 Update the wiki page on autosave, the skill `harness-run-scenario` (keep-open note) and `CHANGELOG.md`. Verified by `wiki.py check`.
