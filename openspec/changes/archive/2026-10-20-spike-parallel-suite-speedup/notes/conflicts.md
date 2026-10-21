# Conflicts in 3 parallel runs

Source: suite-20261020-070359-539d (`--slots 3`), runs 001 to 005, 1 monitor, game not in focus control.
- Focus and audio: all 5 runs passed. Runs 004 and 005 ran in parallel and both passed. No scenario here sends real input, so focus loss cannot show. Audio was not measured by ear. Not checked: a scenario with real mouse input in parallel (it is EXCLUSIVE by rule).
- Second-instance lock: no start failed. No `harness_error`. No timeout in any `scenario.log`. No crash file in any `crash/` folder.
- Bridge timeouts: 0 of 5 runs here (0 of 15 with the earlier 2 parallel suites).
- Limit: at most 2 games ran at once in this suite (5 jobs, exclusive run alone). Earlier suites ran 3 at once with no conflict.
