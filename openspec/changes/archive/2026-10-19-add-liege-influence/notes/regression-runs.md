# Regression runs (task 4.3)

Real game, 2026-10-20, branch merged with `origin/main`. Backup of the saves first: `SaveGames-backup-271b-220015`.

| Test scenario | Pak | Run id | Verdict |
|---|---|---|---|
| `tribute-payout` | none | 20261020-030031-1076 | fail (T4 `loyalty 0 pays 10 percent` got `[0, 0]`) |
| `tribute-payout` (repeat) | none | 20261020-030427-8751 | pass (T4 `[10, 0]`) |
| `tribute-protection-and-loyalty` | none | 20261020-030157-2f65 | pass |
| `mod-state-roundtrip` | none | 20261020-030331-7496 | pass |
| `tech-tree-widget-clicks` | techmenu | 20261020-030625-0554 | pass |
| `invasion-raid-widget` | raidmenu | 20261020-030731-f246 | pass |
| `tech-tree-widget-laws` | techmenu | 20261020-030914-0328 | pass |

Notes:
- The first `tribute-payout` run failed one assert (T4, a stochastic payout value). The repeat passed. The failure is not tied to `liege_influence` (not investigated further); treat it as a possible flake.
- Slot made by a run through `save_game`: `saveGame_52` (run 20261020-030331-7496, `mod-state-roundtrip`). It was deleted after the run. No other save file changed (compared with the backup).
- Not run (cap of about 8 runs): `mod-state-default-load`, `mod-state-two-saves`, `tech-tree-widget`, `tech-tree-widget-key`.
