# Coverage after the sack spike (S6, R3)

Date: 2026-10-10. Tool: `harness/tools/coverage.py` (`--check-spec` agrees with the spec tables).

| | Before | After |
|---|---|---|
| A and P criteria with a verified test method | 26 of 37 (70%) | 29 of 37 (78%) |
| Target | 90% | 90% |

New verified methods (3 of 3 real-game runs each, 2026-10-10):
- S1 by `sack-village`.
- R7 by `sack-store-trip` (the observation method; guard and lock are rules of the mod).
- R3 by `loot-drop-recovery` (on a stand-in ledger; the base game has no ground loot).

Still not verified, with the reason:
- R8: the ruin state is verified (the scenario has no COVERS tag, so the tool does not count it) (`sack-ruins`, 3 of 3 runs), the rebuild cost cannot be read (`spike-S6.md`).
- T4, C1, C2, C3, P3, P5, Q4: no scenario yet (see the gap list of the tool).
Run IDs and the numbers: `spike-S6.md`, `spike-R3.md`.
