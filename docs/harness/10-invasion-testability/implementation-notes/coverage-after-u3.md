# Coverage after U3, S8 and the soak run

Command: `.venv/Scripts/python.exe harness/tools/coverage.py` (branch `feat/23-scenario-control`, 2026-10-10).
Before this branch: 10 of 37 (stand-in scenarios verified, see the changelog). The last passing runs of raid scenarios show `none` here because their runs are in other worktrees; `criteria.json` marks T2, R2 and Q2 verified by spike notes.

```
criteria total: 38  (A 35, P 2, H 1)
automatable share (A+P) / total = 97%
A and P criteria with a verified method: 11 of 37
verified share of A and P criteria = 30% (target 90%)
blocked criteria count against the target: 7
  O1: outposts do not exist in the game data (no way found to found an AI village)
  O2: outposts do not exist in the game data (no way found to found an AI village)
  O3: outposts do not exist in the game data (no way found to found an AI village)
  O4: outposts do not exist in the game data (no way found to found an AI village)
  R5: the base game has no captive system
  S4: outposts do not exist in the game data (no way found to found an AI village)
  S5: the base game has no tribute system
human criteria with a reason: 1
  Q3: Dread, fairness and fun are felt by people. No number can judge them.
scenarios read: 28
  raid-load: covers Q2; last passing run: none
  raid-loot: covers R2; last passing run: none
  raid-spawn: covers T2; last passing run: none
  soak-days: covers Q1; last passing run: soak-f3
  standin-captives: covers R5; last passing run: 20261010-173922-84a5
  standin-outposts: covers O1, O2, O3, O4, S4; last passing run: 20261010-174325-adc0
  standin-tribute: covers S5; last passing run: 20261010-174110-b932
gap list (no scenario, not verified): 26
  T1 T3 T4 T5 R1 R3 R4 R6 R7 R8 C1 C2 C3 S1 S2 S3 P1 P2 P3 P4 P5 P6 D1 D2 D3 Q4
```

Reading: Q1 is now counted (3 of 3 passing runs of `soak-days`, newest `soak-f3`, and `method_verified` true in `criteria.json`). Verified: 11 of 37 A and P criteria (30%). Q1 is verified as a method; the 2-year run itself is extrapolated (`soak-results.md`).
