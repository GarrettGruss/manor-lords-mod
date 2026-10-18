# Weaver by reskin of the tailor slot: recipe result (2026-10-18)

Question: can wool -> yarn and flax -> linen (1 : 1) run in a plot extension?

## Short answer
YES, in the tailor slot (Type 6), with two Lua writes: `artisanJob = 14` (weaver) and `EnableRecipe(148)` or `EnableRecipe(12)`. Not with a new Type (see `new-extension-number.md`).

## Setup
- Fixture `base`, scenario `probe-extension`, game speed 3. 40 planks, 60 wool, 60 yarn, 60 flax and 60 linen are given with the cheat manager (`GiveItemByID`). Stocks are read with `Region:getStockOfGood`.
- Steps: `addExtensionChangeRequest(6)`, 5 game days (built), `addArtisanChangeRequest(6)`, 4 game days, then the unsafe `master_artisan_set` (`job` 14, `enable_recipe`), then 8 to 10 game days.
- Pak `weaver106` (sha256 starts `a5c5ea8c`): `DT_Upgrades` row 106 edited in place (`descr` weaver, cost 3 planks, wealth 77) plus the custom mesh (see `custom-model.md`).

## Results
| Run | Pak | Writes | Stocks over the watch | Verdict |
|---|---|---|---|---|
| s31-base-3 (burgage-start, 10 days) | none | none (tailor job 10) | all stocks unchanged, clothes 0 | the vanilla tailor made nothing |
| s31-base-9 | none | recipe 149 | yarn 53 -> 53, linen 57 -> 57, clothes 0 | no production |
| s31-lv2-1 | none | `lv` 2, recipe 149 | unchanged | no production |
| s31-recipe-2 | none | recipes 149, 12, 148 (job 10) | linen 53 -> 53 | recipes alone do nothing |
| s31-job14-1 | none | job 14 only | wool 59, yarn 50, flax 50, linen 59: constant | the job alone does nothing |
| s31-weaver106-2 | weaver106 | job 14, recipes 148 and 12 | wool 50 -> 41, yarn 56 -> 65 over 10 days. Flax 52 and linen 58 constant. Plot inventory: yarn 9, wool 1. | wool -> yarn, 1 : 1 (9 in, 9 out) |
| s31-weaver106-3 | weaver106 | job 14, recipe 12 only | flax 53 -> 43, linen 50 -> 60 over 10 days. Wool 54 and yarn 53 constant. Plot inventory: linen 9, flax 1. | flax -> linen, 1 : 1 (10 in, 10 out) |

Small drifts of a few units also happen in runs without any extension (other users of the stock). Only the pairs above moved together by the same amount.

## Reading
- The worker (the plot family, `assigned_families` 1, `max_worker_families` 0) needs both the weaver job and an enabled recipe. Both are state that a Lua mod can write.
- With the tailor job 10 and any recipe, nothing is made. So the vanilla tailor extension did not produce in these runs (clothes may need other inputs or a gate that was not found). The weaver path works because job 14 and the weaver recipes fit together.
- Only one recipe ran at a time when two were enabled (yarn first).
- The data rows work: with `weaver106` the extension cost fell from 6 to 3 planks (54 -> 51), and the artisan change cost 3 planks (51 -> 48). Vanilla charges 6 and 6.
- The job write stayed for 10 game days. It is not proven to survive a save and a load (no save was made). A mod must write it again after a load.
- The rate 1 : 1 is vanilla data (`DT_Items` 148 and 12). A different rate or a new product needs a `DT_Items` row change. Not tested.

## Not proven
- Normal play: the plot panel and a real player. The user should check one weaver plot by eye.
- Several families or several plots.
- The tailor's own clothes recipe.
