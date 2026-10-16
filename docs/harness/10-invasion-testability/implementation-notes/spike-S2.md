# Spike S2: raid spawn functions

Date: 2026-10-10. Runs: probe-s2-a, probe-s10-a/b, series of `raid-spawn` (3 of 3).

## Question
What are the signatures of the spawn functions, can they be called, and what do they spawn?

## Signatures (jmap)
| Function | Owner | Parameters |
|---|---|---|
| `spawnRaiders` | `RTSMultiEngineCPP` | `NumSquads:Int`, `ArmyCenter:Vector` (const ref) |
| `spawnEliteRaiders` | `RTSMultiEngineCPP` | `ArmyCenter:Vector` |
| `spawnBanditCamp` | `RTSMultiEngineCPP` | none |
| `spawnArmy` | `RTSMultiEngineCPP` | `Pos:Vector`, `unitTypes:Array<Name>`, `ownerPawn:PawnCPP`, `companyID:Int`, `arrivesInDays:Int` -> Array of squads. Not called |
| `spawnCompleteUnit` | `RTSMultiEngineCPP` | `tempName:Name`, `Location`, `Rotation`, `ownerPawn`, `companyID`, `arrivesInDays`. Not called |
| `SpawnBanditSquad`, `SpawnRaidersOfType(Types:Str)`, `SettleRaiders` | `MLCheatManager` | none / string / none |
| `spawnRaiderForce` | not a function: an Int field of the quest `Reward` struct | |

## Method
Command `spawn_raiders` of HarnessActions: `engine:spawnRaiders(n, {X=, Y=, Z=})`. A plain Lua table works for the Vector parameter, so no new object passing was needed. The centre is the position of the player pawn unless x and y are given. Units are counted before and after.

## Results (bandit side, test save, 189 to 220 units at the start)
| Call | Added units | Squads | Where |
|---|---|---|---|
| `spawnRaiders(1, centre)` | +18 | 1 | Hochweg, about 11700 units from the centre |
| `spawnRaiders(6, centre)` | +108 | 6 | not recorded |
| `spawnBanditCamp()` | +18 | 1 | random region (Riesenbuckel, Krumme Leite seen) |
| `spawnEliteRaiders(centre)` | +54 | not counted | Hochweg, the same point as the 1-squad raid |
| `MLCheatManager:SpawnBanditSquad` | +18 | 1 | |
| `MLCheatManager:SpawnRaidersOfType("Raiders")` | 0 | | no effect (as before) |
The unit counts and sides match a timer raid (+18, side bandit, role Soldier). Every call took about 0.2 s through the command channel.

## Can size and type be chosen?
Size: only in whole squads of 18 (`NumSquads`), at most 20 squads per call in the helper. Type: no parameter. `unitTemp` of the units reads `None`, so the composition could not be read either. `spawnArmy` and `spawnCompleteUnit` take unit template names (rows of `DT_units`): they may allow a chosen composition, but they need a `ownerPawn` object. Not tried.

## Verdict
method verified for count and place: `ctx.actions.spawn_raid(squads, elite=False)`, `spawn_bandit_camp()`. Not possible (with these calls): choose type or an exact size. Not verified: `spawnArmy`.
