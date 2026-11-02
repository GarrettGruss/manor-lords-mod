# Real game runs (slot auto, test map Jagged_Cliffs)

| Run | Test scenario | Verdict | Key result |
|---|---|---|---|
| tr-rich-1 | tribute-rich | harness_error (metric type, fixed) | all 19 checks passed before the error |
| tr-rich-2, tr-rich-3 | tribute-rich | pass | Krumme Leite (immenreuth) pays stone + salt, Hochweg (Goldhof) pays mushrooms + flax; 100 / 150 / 50 each for fair / heavy / light; 35 nodes scanned; same goods in both runs; no failed deposit |
| tr-supply-1 | finite-resources-vassal-supply | pass | claimed region Eichenhau paid stone + flax (200); home deposits not mined |
| tr-payout-1, -2 | tribute-payout | fail (T1, T2, T5 passed) | claimed region paid stone + clay, 200. The later `run_game_days` failed: the clock did not move because the scenario settings window ("The Hussites are coming") was open in a --new-game run. Not caused by the tribute |
| tr-policies-1 | vassals-policies-and-orders | fail (P1 to P3 passed) | fair 100, heavy 150, light 50 each; the later `run_game_days` hit the same open window |
| tr-laws-1, -2 | tech-tree-laws | fail | "start pick" never true in the --new-game run (the same window); the tribute checks were not reached |

The tribute checks of every run passed. The open settings window in --new-game runs is a known behavior of the scenario settings feature and is not part of this change. The month field is 1 based (see `month-clock.md`). Game saves were not touched (hash of the save folder unchanged, per the run summaries).
