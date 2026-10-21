# Design: Add vassal sack wipe

## Context
- A vassal is a handed-over region run by an AI lord. Today a loss frees the slot and the lord keeps the land (`loss_region = forget`). `take_by_lord` crashed the game.
- The sack code for the player region is in `sack_and_terms` (`world.lua`). The mod may sack houses in an AI village only (owner, 2026-10-20, item 10).
- The refugee wave goes to the home region, in steps of 5 families.

## Decisions
- The completion rule is the share of ruins: ruins divided by the buildings of the region at the start of the sack, 80 percent (config `sack_wipe.ruin_share`, default 0.80).
- At completion the mod deletes every villager of the region, frees the slot (reason `wiped`), and starts a refugee wave of 50 percent of the population counted just before the deletion.
- The land stays a village of rubble. The mod does not change its owner.
- Restore: one named command spends gold and raises the villager count of the wiped region to 5. The AI does the rebuild. The tribute restarts when the AI has rebuilt (see question 2).
- Terms: after a sack of the player region the mod closes any open offer and opens no new one for that raid. The offer at raid spawn stays (question 4).
- `take_by_lord` and its command are removed. No spec keeps the capital move.
- The requirement "The feature offers named commands" of `mod/vassals` is also changed by `remove-vassal-loyalty` (#344). This change leaves it unchanged, and adds `vassals_restore` and drops `vassals_set_loss_region` in the implementation. Fix the spec text for the command list when the second of the two changes is archived.

## Open questions
| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 1 | What does an AI village do when all its villagers are dead (stays empty, gets new villagers, the lord dies)? | A spike | Task 1.1 |
| 2 | Does a villager count of 5 make the AI rebuild the ruins? How long does it take? | A spike | Task 1.2 |
| 3 | What does the restore cost in gold (flat, for each villager, or by difficulty)? | Owner | Task 1.3 |
| 4 | Item 4 says "no terms after a sack of the player". Does it mean (a) no offer after a sack in the same raid, or (b) the terms feature is gone? This design takes (a). | Owner | Task 1.3, on the spec pull request |
| 5 | Does a wiped vassal keep its registry slot so the player can restore it, or does restore claim a new slot? This design keeps a `wiped` record outside the slots. | Owner | Task 1.3, on the spec pull request |
| 6 | How does the mod sack houses in an AI village (the same `collapse` method as for the player region)? | A spike | Task 1.1 |
