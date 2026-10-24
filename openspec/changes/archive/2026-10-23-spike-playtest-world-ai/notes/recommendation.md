# Recommendation (spike-playtest-world-ai, #430)

## What each setting of the playtest world switches off

| Setting in the playtest world | Needed by the mod? | What the mod can do itself |
|---|---|---|
| Initial bandit camps 0, spawn limit 0 | Only for the bandit pawn: `ManorCore.spawn_squads` and `HarnessBattle` (side `bandit`) fail with "no pawn for side bandit" when no camp ever existed. | Call `RTSMultiEngineCPP:spawnBanditCamp()` once, then `addPawnRelations(pawn)`. Side effect: one camp and 18 Brigands. Not tested: a pawn without a camp. |
| AI opponents 0 | No. | `spawnNewAILord` + relations + `startAI(build)` + a full claim makes a lord that builds (16 buildings in 20 game days in a free region). `ownerPawn` alone does not build. |
| Off map adversary Absent | No. | Nothing to do. The Hussite raid uses its own mod lord. |
| Raider frequency None | No for Hussite raids (they are planned by the mod). The game's own raids stay off. | Nothing to do. |

## For the owner (decisions)

1. **Bandit pawn:** let the mod create it with `spawnBanditCamp()` when it is missing (side effect: a camp and 18 Brigands), or tell players to set Initial bandit camps to 1 or more. A follow-up spike can look for a way to get the pawn without a camp.
2. **Raid army region (mod bug, low impact):** the army and the battle marker go to the region under the camera when the raid starts. The plunder tick does not depend on it (a control run with the army 60 000 units away still plundered). Change `lord_raid` so that the anchor uses the player's village region, not the camera region. This needs a follow-up change (for example `fix-raid-target-region`) and is independent of the game settings.
3. **Playtest fixture:** the village has 21 goods in tier 1 stores, so a raid has nothing to take. For a plunder test use a fixture with stocks (the `base` village has 156+) or give goods first (`manor_put`).

## Not verified

Save and load of a bandit pawn or AI lord made by the mod; a pawn without a camp; plunder with stocks in the playtest world.
