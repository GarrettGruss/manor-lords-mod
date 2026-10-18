# Coverage baseline (U8)

Start value of the coverage tool, before any spike or scenario. Command:
`.venv\Scripts\python.exe harness\tools\coverage.py` (worktree of branch feat/16-invasion-testability, 2026-10-10).

```
criteria total: 38  (A 35, P 2, H 1)
automatable share (A+P) / total = 97%
A and P criteria with a verified method: 0 of 37
verified share of A and P criteria = 0% (target 90%)
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
scenarios read: 19
gap list (no scenario, not verified): 37
  T1 T2 T3 T4 T5 O1 O2 O3 O4 R1 R2 R3 R4 R5 R6 R7 R8 C1 C2 C3 S1 S2 S3 S4 S5 P1 P2 P3 P4 P5 P6 D1 D2 D3 Q1 Q2 Q4
```

Reading: the criteria are 97% automatable on paper, but none has a verified method yet. 7 of the 37 A and P criteria are blocked by missing game systems and count against the target until their system exists or the brief drops them.
