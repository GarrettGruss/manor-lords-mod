# Design: Add vassal sack wipe

## Context
- A vassal is a handed-over region run by an AI lord. Today a loss frees the slot and the lord keeps the land (`loss_region = forget`). `take_by_lord` crashed the game.
- The sack code for the player region is in `sack_and_terms` (`world.lua`). The mod may sack houses in an AI village only (owner, 2026-10-20, item 10).
- The refugee wave goes to the home region, in steps of 5 families.

## Decisions
- The completion rule is the share of ruins: ruins divided by the buildings of the region at the start of the sack (or the buildings that are still there, when the AI demolished ruins during the sack: real run 20261023-005824-8bac), 80 percent (config `sack_wipe.ruin_share`, default 0.80).
- At completion the mod deletes every villager of the region, frees the slot (reason `wiped`), and starts a refugee wave of 50 percent of the population counted just before the deletion.
- The land stays a village of rubble. The mod does not change its owner while the sack runs.
- Wood (owner, 2026-10-22): when a sack starts, the mod removes all logs (good 16) and planks (good 17) from the buildings of the region (`HarnessSack.remove_goods`, `consumeGoodNoCheck`; config `sack_wipe.wood`). When a sack ends and the village is not wiped, the mod gives 50 logs and 100 planks (`sack_wipe.give`; `addToInventory` works on a ruin) and orders the rebuild of every ruin at once. Ruins stay visible while they are rebuilt. A sack ends without a wipe when the raid that sacks the region ends (owner, 2026-10-22: the raiders left or all died; the tribute feature listens with `raid_behavior.watch_end`, the same hook that other features use), when it gives up (`max_steps`), or when the command `vassals_end_sack` runs (for tests).
- Rebuild order (owner, 2026-10-22; `notes/rebuild-order.md`, proven in the real game): for each rubble building, `old = building.typeBeforeChange`; write `building.Data` as a whole struct with `bType = old`, `constructed = false`, `hp = 0`; then `building:SetupBuilding()`. The mod never calls `convertBlueprintsToBuildings` (it removes the model). A building with `typeBeforeChange` 0 or 75 is skipped. Each order is logged. The function is `world.rebuild_ruins(region)`; the test command is `InvasionMod.vassals_rebuild_ruins`.
- Restore also hands the region to the AI lord (owner, 2026-10-22): the lord of the wiped record (spawned again when gone) receives the region (`lord_receive_region`, as a new vassal), then the families and goods are added and the rebuild order goes to every ruin. Without a lord the AI does not build (`notes/rebuild-order.md`).
- Restore (owner, 2026-10-21 and 2026-10-22): one named command `vassals_restore` spends a flat 100 silver, gives the region to an AI lord, raises the villager count of the wiped region to 5 (`settleRegion` with the lord pawn as the settling pawn), spawns 100 logs, 200 planks and 100 rubble stone in a building of the village and orders the rebuild of every ruin. A refusal (no wiped region, too little silver, no free slot, or a failed villager call) takes nothing.
- The restored vassal gets a slot again, with the flag `rebuilding`. The tribute skips a `rebuilding` vassal. The flag ends when `restore.rebuilt_share` (0.50) of the ruins that the restore ordered are built, counted above the buildings that are built right after the order (the restore adds 3 to 4 buildings itself; real run 20261023-003012-a0df ended the flag at once with a count of old buildings). A construction site made by the rebuild order is not built yet (`Data.constructed` false), so the census counts it as standing but not as built. The rule `min_new_buildings` is removed: the order makes all ruins sites at once, so a count above the restore start has no meaning (kept simple). This is the mod reading of "the tribute restarts after the rebuild".
- The sack runs in steps: collapse the missing standing buildings, look again, wipe when 80 percent are ruins. A sack that makes no progress gives up after `sack_wipe.max_steps` (6) polls and logs an error. A running sack ends with a game load (not saved).
- The wipe uses the fixed shared helper `ManorCore.remove_families` (change #357, pull request #363), which collects the members first.
- Terms: after a sack of the player region the mod closes any open offer and opens no new one for that raid. The offer at raid spawn stays (question 4).
- `take_by_lord` and its command are removed. No spec keeps the capital move.
- The requirement "The feature offers named commands" of `mod/vassals` is also changed by `remove-vassal-loyalty` (#344). This change leaves it unchanged, and adds `vassals_restore` and drops `vassals_set_loss_region` in the implementation. Fix the spec text for the command list when the second of the two changes is archived.

## Open questions
| # | Question | Who decides | Answer |
|---|---|---|---|
| 1 | What does an AI village do when all its villagers are dead? | A spike | Task 1.1, `notes/empty-ai-village.md`: it stays, no decay, no new villagers, the lord keeps its build loop. |
| 2 | Does a villager count of 5 make the AI rebuild the ruins? | A spike | Task 1.2, `notes/restore-to-five.md`: not alone. Question 7 adds goods. |
| 3 | What does the restore cost in gold? | Owner | Answered 2026-10-21: flat, 100 silver. |
| 4 | Does "no terms after a sack of the player" mean (a) no offer after a sack in the same raid, or (b) the terms feature is gone? | Owner | No answer. The implementation takes (a). Listed for the owner in the implementation pull request. |
| 5 | Does a wiped vassal keep its registry slot, or does restore claim a new slot? | Owner | No answer. The implementation keeps a `wiped` record outside the slots; restore takes a free slot. Listed for the owner in the implementation pull request. |
| 6 | How does the mod sack houses in an AI village? | A spike | Task 1.1: `collapseBuilding()` on each building, by region name. |
| 7 | What else does the restore give so that the AI rebuilds? | Owner | Answered 2026-10-21: 100 logs, 200 planks, 100 rubble stone in the village. |
| 9 | What ends a sack without a wipe? | Owner | Answered 2026-10-22: the end of the raid (raiders left or dead). `raid_behavior.watch_end` calls `vassals.end_sack`. |
| 10 | Why did the wipe crash once? | Spike | `notes/wipe-crash.md`. The wipe now takes three polls (families down to one, the last family after a stable count, the slot after a stable count). |
| 8 | Is the shared helper `remove_families` fixed? | Owner | Fixed on `main` by #357 (pull request #363). |
