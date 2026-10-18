# M06 iteration 02: notes

- Silver is read and written as `engine.playerRef.silver` (the bandits buy-back helpers `features/bandits/world.lua`). The game does not check the cost, so the mod refuses a payment below the amount.
- Accepting calls `raid_behavior.force_leave("terms")`. It runs the same start-leave code as the loot, loss and time reasons: peace with the lord (the lord army is removed by the game), and the leave watchers run. The sack feature treats `terms` as not lost, so no sack follows.
- The offer opens at a lord raid spawn. It is held in memory only (a load drops an open offer). The state code, the next tribute day and the silver paid are saved in ModState.
- Vassalage tribute: a scheduler job charges `tribute_base x difficulty` every 360 days, or the silver left if lower. M08 will replace this rule.
