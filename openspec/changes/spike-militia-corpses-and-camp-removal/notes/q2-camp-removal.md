# Q2: remove the bandit camp and its bandits

Same run `mc-1`, same game as Q1. The fixture `playtest-noai` has no bandit camp at the start.

| Step | Result |
|---|---|
| `RTSMultiEngineCPP:spawnBanditCamp()` | 1 new `SMBuildingMaster` (`bType` 100) at (-74133, -31897), 17 parts, owned by a new pawn (`isBandit`). Pawns 1 to 2, units 207 to 225 (18 Brigands, one new squad). |
| Picture before | `evidence/camp-before.jpg` |
| `just_die` on the 18 Brigands, then `SetActorHiddenInGame(true)` on the bodies | Units near the camp 18 to 0. The bandit pawn stays (1). No crash. The bodies left the unit count about 1 400 game s later (225 to 207). |
| `canBeDemolished()` on the camp | false |
| `demolish()` with no argument | refused by the bridge (it needs 1 argument) |
| `demolish(true)` on the camp master | Works. Within about 10 game s the parts went 17 to 0, then the master was gone (sites of `bType` 100: 1 to 0). No crash. |
| Outlaws pawn | Survives (bandit pawns 1, pawns 2) |
| Respawn watch | About 1 140 game s (28 game days) at speed 3: no camp, no brigands at the camp. The game did not respawn them. |
| Picture after | `evidence/camp-after.jpg` (same camera, camp and units gone) |

`K2_DestroyActor` on the camp building was not tried, because `demolish(true)` worked.

A game event popup ("Cold!") paused the game once during the watch. It was closed with the `popupMessageWidget_C` Accept event, the way `HarnessActions close_popups` does.

## Not verified
A second `spawnBanditCamp` after the removal, a save and load after the removal, and the later behavior of bandit raids with an Outlaws pawn that has no camp.
