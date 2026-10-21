## Summary

Change: `spike-parallel-suite-speedup` (#151). Gate: implementation.

- Measured suite `core` (5 runs): 296.7 s with `--slots 1`, 186.8 s with `--slots 3`. Speedup 1.6x, not 3x, because each run is slower with 3 games.
- An `EXCLUSIVE` scenario ran alone in a 3-slot suite: no run overlapped it.
- No bridge timeout and no `harness_error` in 15 parallel runs. The owner kept the 15 s timeout.
- `gameslots.SLOTS_DIR` is the main checkout `slots` folder, so `--slots N` works from a worktree.
- Updated `CHANGELOG.md`, skill `harness-run-scenario` and wiki page `workflows/suites-and-ab.md`.
- Closes #151. Issue #160 may be closable too.

## Spec changes

None. The change has no delta spec (`skip_specs`).

## Test results

| Check | Run id or test file | Verdict | Key number or range |
|---|---|---|---|
| Suite core, 1 slot | suite-20261020-064557-dd4d, suite-20261020-065742-66da | pass (drift from old baselines) | 296.7 s, 5/5 runs passed |
| Suite core, 3 slots | suite-20261020-065120-d970, suite-20261020-065435-e514 | pass (drift from old baselines) | 187.3 s and 186.2 s, 5/5 |
| Exclusive scenario | suite-20261020-070359-539d | pass | no overlap; 184.3 s, 5/5 |
| Bridge timeouts | the 3 parallel suites | pass | 0 of 15 runs |
| test_runlib* | harness/tests | pass | 527 tests |
| test_suitelib* | harness/tests | pass | 116 tests |
| test_harness_tools* | harness/tests | pass | 50 tests (1 skipped) |
| test_reload_mods, test_pakmod, test_coverage | harness/tests | pass | 15, 78 (1 skipped), 26 tests |
| test_fakegame_* | harness/tests | pass | 894 tests |
| test_telemetry_mock, test_boundary, test_save_call_sites | harness/tests | pass | 19, 2, 5 tests |
| lua_syntax, boot_state_machine, coverage --check-spec | harness/tests, harness/tools | pass | all ok |
| wiki.py check, openspec validate --strict | repo | pass | ok |

## Evidence

None

## Not verified

- A parallel run of a test scenario with real mouse input (it is EXCLUSIVE by rule).
- Audio and focus were not measured directly.
- `report.json` has no per-run start time; the overlap check used the run summaries.

Closes #151
