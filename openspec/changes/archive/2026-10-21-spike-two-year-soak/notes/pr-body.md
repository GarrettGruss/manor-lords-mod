## Summary
- Spike for #286: soak the village for a long run in the real game.
- Owner decisions (2026-10-20): the game clock rate is a metric only, not an assert. Criterion Q1 is verified at 401 days.
- Test scenario `soak-days` samples units, buildings, game days and memory every 120 wall s. Run 1 crashed in the Invasion Mod sack step (#327, fixed in #328).
- The clock slows to about 1.1 to 1.2 game s per wall s as the village grows. Memory stays flat. 730 days do not fit in `MAX_LIMIT_S`.

Closes #286. Refs #327.

## Spec changes
None. The change declares no spec-level behavior (`skip_specs`).

## Test results
| Check | Run id or test file | Verdict | Key number |
|---|---|---|---|
| Soak, first run | s286-soak-1 | crash (#327, fixed in #328) | about 67 days, 1399 s wall, rate about 8 early, memory 4709 to 4458 MB |
| Soak, 333 days | s286-soak-2 | no crash; rate assert failed by design (before the owner decision) | 333 days, 12054 s wall, rate 1.11, memory 4194 to 1932 MB |
| Soak, 401 days | s286-soak-3 | no crash, village alive | 401 days (day 205 to 606), 13254 s wall, rate 1.21, memory about 4400 to about 1700 MB |
| test_runlib* | harness/tests | pass | 527 tests |
| test_suitelib* | harness/tests | pass | 116 tests |
| test_harness_tools* | harness/tests | pass | 50 tests (1 skipped) |
| test_reload_mods | harness/tests | pass | 15 tests |
| test_pakmod | harness/tests | pass | 78 tests (1 skipped) |
| test_coverage | harness/tests | pass | 26 tests |
| test_fakegame_* | harness/tests | pass | 894 tests |
| test_telemetry_mock | harness/tests | pass | 19 tests |
| test_boundary, test_save_call_sites | harness/tests | pass | 2 and 5 tests |
| lua_syntax, boot_state_machine | harness/tests | pass | all ok |
| coverage.py --check-spec | harness/tools | pass | criteria agree |
| wiki.py check | repo-wiki | pass | ok |
| openspec validate --strict | spike-two-year-soak | pass | valid |

## Evidence
None

## Not verified
- 730 days in one run. It does not fit in `MAX_LIMIT_S` (13500 s) at the observed clock rate.
