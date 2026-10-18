# A new extension number (Type 17) (2026-10-18)

Question: can a pak add an extension that the game does not have?

## Method
- Pak `ext17` (`modtools/work31/out/ext17_P.pak`, sha256 starts `c1f355eb`): `DT_Upgrades` row 117, cloned from row 106 (tailor) with `descr` "weaver", cost 3 planks, `regionalWealth` 77, `minimumHouseLv` 0. Tool: `harness/tools/s31_make_extension_json.py`.
- Scenario `probe-extension`, `HARNESS_PROBE_EXT=17`, fixture `base`: `plot_upgrade` with `extension=true`, then with `artisan=true`.

## Result (runs s31-ext17-1 and s31-ext17-2, both pass, no crash)
| Check | Result |
|---|---|
| Row 117 loads | YES. `upgrade_stat` 117 shows `minimumHouseLv` 0 (my value). |
| The game accepts Type 17 | YES. `Extensions[1].Type` = 17. |
| Cost is charged | NO. Planks stay 54. `upgradesDone` is `[0]`, not `[117]`. The game takes 17 as "Count" (out of the enum range). |
| Parts | The old yard parts (31) are removed. The new extension has 0 parts. No model, no `workpos`. |
| Job | `addArtisanChangeRequest(17)`: `artisanJob` stays 0. |
| Production (job 14 and recipe 148 written by Lua) | NO. Wool is carried into the plot (inventory wool 3), but wool stays 50 and yarn stays 59 for 8 game days. |

## Verdict
A new extension number cannot be made with data. The enum is native with 17 values. Type 17 is accepted but gives an empty yard, no cost and no job. The part blueprint (with `workpos`) is needed for work, so even Lua writes do not give production.
Not tested: the plot panel (mouse only), and a number above 17.

## Side result for row ids
`DT_Upgrades` row key = 100 + extension number. The spec 22 range for new upgrade rows (117 to 999, feature 0: 117 to 126) overlaps these keys: rows 117 to 126 would be extensions 17 to 26. This does not matter while extensions above 16 do not work.
