# Real runs of tech-tree-menu-stay-open

Command: `uv run python harness\run.py --scenario tech-tree-menu-stay-open --pak techmenu`. Save backup made first (`SaveGames-backup-272-20261019-2216`).

| Run id | Verdict | State reads | Clicks sent/counted | Note |
|---|---|---|---|---|
| 20261020-031619-b992 | harness_error | not recorded | not reached | The game window lost the foreground during the 300 s wait. No input sent. Environment, not the scenario. |
| 20261020-032210-98e1 | crash | 82 healthy, then the game ended (573 total, 491 bad) | not reached | Game crash after about 41 s: EXCEPTION_ACCESS_VIOLATION in `UE4SS!getgeneric() ltable.c:302` (Lua table). Last log line: hook registered on `WBP_ClickButton`. A real mod or UE4SS fault, not a scenario bug. |
| 20261020-032814-176d | pass | 481 / 0 bad | 10 / 10 | |
| 20261020-033430-a300 | pass | 481 / 0 bad | 10 / 10 | |
| 20261020-034044-d828 | pass | 481 / 0 bad | 10 / 10 | |
| 20261020-034657-2e06 | pass | 483 / 0 bad | not read | |

Result: 4 of 6 runs pass (4 in a row after the crash). The crash is a flaky game fault that this test scenario is meant to catch.
