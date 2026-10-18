# Coverage after the raid spikes

Command: `.venv\Scripts\python.exe harness	ools\coverage.py` (worktree mlm-wt16, 2026-10-10). Baseline: 0 of 37 (coverage-baseline.md).

```
criteria total: 38  (A 35, P 2, H 1)
automatable share (A+P) / total = 97%
A and P criteria with a verified method: 3 of 37
verified share of A and P criteria = 8% (target 90%)
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
scenarios read: 24
  raid-load: covers Q2; last passing run: 20261010-162303-0c5c
  raid-loot: covers R2; last passing run: 20261010-162015-3b4f
  raid-spawn: covers T2; last passing run: chk-telemetry
gap list (no scenario, not verified): 34
  T1 T3 T4 T5 O1 O2 O3 O4 R1 R3 R4 R5 R6 R7 R8 C1 C2 C3 S1 S2 S3 S4 S5 P1 P2 P3 P4 P5 P6 D1 D2 D3 Q1 Q4
```

Reading: 3 criteria have a verified method (T2, R2, Q2). T1, T3, R3 and T5 are partial; their `spike_note` in criteria.json says what is missing. Scenarios of partial criteria are not tagged with COVERS, so the tool does not count them.
