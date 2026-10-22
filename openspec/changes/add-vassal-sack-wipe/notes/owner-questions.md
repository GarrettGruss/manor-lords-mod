# Owner questions (task 1.3) as data

Answers of the owner are from chat (2026-10-21). Questions 4 and 5 have no explicit answer: the implementation uses the design defaults, and the pull request lists them for the owner.

| # | Question | Evidence from the spike | Answer |
|---|---|---|---|
| 3 | What does the restore cost in gold: flat, for each villager, or by difficulty? | None (the spike measures no cost). | Flat, 100 silver (owner, 2026-10-21). Config `vassals.restore.silver`. |
| 4 | Item 4 says "no terms after a sack of the player". Is it (a) no offer after a sack in the same raid, or (b) the terms feature is gone? | None. | No answer. Design default (a). Listed for the owner in the pull request. |
| 5 | Does a wiped vassal keep its registry slot so the player can restore it, or does restore claim a new slot? | The registry did not change when the villagers died (slot kept, region owner unchanged, 10 game days). The mod must free the slot itself. | No answer. Design default: a `wiped` record outside the slots (`wiped<N>_*` tags, at most `sack_wipe.max_wiped` = 6). A restore takes a free slot again. Listed for the owner in the pull request. |
| 7 (new) | A villager count of 5 alone did not make the AI rebuild a village of rubble in 30 game days (run 20261021-052018-be14). Should the restore also clear the ruins, add a starter set of buildings, or is a village of rubble with 5 families acceptable? | `settleRegion` gives 5 families and 3 to 4 buildings; the ruins stay; the AI logs `AI_build failed to find place`. | The restore also spawns 100 logs, 200 planks and 100 rubble stone in the village, so that the AI starts to rebuild (owner, 2026-10-21). Config `vassals.restore.goods` (item ids 16, 17 and 15). |
| 8 (new) | The helper `remove_families` crashed the game on an AI village (runs 20261021-050845-d295, 20261021-051155-a6a4). The wipe will use "collect the members, then kill each". Is it fine to change the shared helper for the player sack too? | See `empty-ai-village.md`. | Already fixed on `main` by change #357 (pull request #363). The wipe uses the fixed shared helper `ManorCore.remove_families`. |
