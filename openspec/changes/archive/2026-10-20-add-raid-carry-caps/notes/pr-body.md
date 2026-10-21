## Summary

Change: `add-raid-carry-caps` (#275). Gate: implementation.

- Owner decisions of 2026-10-20: the carry cap acts on Hussite raids only; native raids keep the game's own loot (about 5 per raider, see `notes/loot-cap-spike.md`); the bandit cap is dropped; the loot goal of a Hussite raid is `carry_cap` (10).
- The plundered goods of a Hussite raid never exceed `carry_cap` times its raiders at the start. `raid_behavior_state` shows `carry_cap` and `raid_type` of each raid.
- New test scenario `raid-behavior-carry-caps`. The wiki page `docs/wiki/architecture/invasion-features.md` and `CHANGELOG.md` are updated.

Closes #275

## Spec changes

- Two MODIFIED requirements in `mod/raid_behavior`. They changed after gate 1 because of the owner decisions of 2026-10-20 (Hussite-only cap, native raids untouched, no bandit cap, loot goal 10).

## Test results

| Check | Run id or test file | Verdict | Key number or range |
|---|---|---|---|
| Real game: carry caps | `raid-behavior-carry-caps`, run 20261021-030639-c378 | pass | Hussite lord raid, 32 raiders, left after 15 days, reason `loot`, plundered 320 = 10 x 32 |
| Real game: loot return | `raid-behavior-loot-return`, run 20261021-031352-eb7c | pass | - |
| Real game: native plunder | `raid-behavior-native-plunder`, runs 20261021-031021-395d, 20261021-031527-374c | fail, pre-existing (#337) | same two asserts fail on main: run 20261021-032110-3177 |
| test_runlib* | harness/tests | pass | 527 tests |
| test_suitelib* | harness/tests | pass | 116 tests |
| test_harness_tools* | harness/tests | pass | 50 tests, 1 skipped |
| test_reload_mods | harness/tests | pass | 15 tests |
| test_pakmod | harness/tests | pass | 78 tests, 1 skipped |
| test_coverage | harness/tests | pass | 26 tests |
| test_fakegame_* | harness/tests | pass | 899 tests |
| test_telemetry_mock | harness/tests | pass | 19 tests |
| test_boundary, test_save_call_sites | harness/tests | pass | 2 and 5 tests |
| lua_syntax, boot_state_machine, coverage --check-spec | harness/tests, harness/tools | pass | - |
| wiki.py check, openspec validate --strict | - | pass | - |

## Evidence

None

## Not verified

- `raid-behavior-native-plunder` fails on main too (#337); this change does not fix it.
- Whether the native reset of `ItemsLooted` (about 5 per raider) is a native cap or a drop at a store (not seen per unit).
- No A/B test of the effect on game balance.
