# AdaptiveEnemies 1.1 (inspection note)

Date: 2026-10-11. Source: `C:\Users\garre\Downloads\AdaptiveEnemies 1.1 369 1.1 2026-09-13T16-06Z IzMRLXfPa`. Nothing was run.
Files: `enabled.txt` (0 bytes), `README.txt`, `scripts/config.lua`, `scripts/main.lua`. Code comments are in Russian. Citations below use the line numbers of each file.

## What it does for the player
While the player is at war with the baron, the baron gets extra squads. The size grows with the realm: settlement level, number of regions, size of the player's field militia.
A realm with fewer than 2 regions gets no change. Waves: a first wave at once, a second smaller wave 90 s later (only for a grown realm). A "last stand" wave comes when the baron has 3 squads or fewer. (README.txt)

## How it works
- One timer: `LoopAsync(5000, ...)` then `ExecuteInGameThread(baronTick)` (main.lua:346). It runs for the whole game.
- Find the baron: loop `RTSMultiEngineCPP:getPawnBySetupIndex(i)` for i = 0..40 and match `pawn.lordsName` to the fixed name "Hildebolt von Berenreute" (main.lua:93, config.lua:35).
- "At war" means the baron has an active challenge: `#baronPawn:getRelevantChallenges() > 0` (main.lua:277). The war state resets when the count is 0. `baronAtWar` (main.lua:133) also wants 5 or more squads, but only the probe uses it.
- Anchor: the first live baron squad from `baronPawn:getAllCommandedSquads()`. It reads `squad.WeightedCenter` (config list: WeightedCenter, TargetLocation, campLocation, Center, Location) (main.lua:117). The squad `companyID` is reused for the new squads.
- Spawn: `RTS:spawnCompleteUnit(FName(template), pos, rot, baronPawn, companyID, 1)` once per squad, with the position moved by `spawnOffset` 1500 units, 4 squads per row (main.lua:199-216). The last argument (`arrivesInDays`) is 1.
- Notice to the player: `playerPawn:playEventMessage(FName("adaptiveEnemiesReinforce"), title, text)` (main.lua:219).
- Player level: `Region:getNumFamiliesOfLv(2|3|4)` per settled region, mapped by a ladder table to level 1..6, averaged over `getAllCommandedRegions()` (main.lua:20-75, config.lua:15-25).
- Player army: sum of `#squad.equippedRecruits` over the player's field militia squads (`companyID == -1`, unit type one of the 5 militia names) (main.lua:146).
- Count formula (config.lua:43-57, main.lua:167): `levelBase[L]` = {0,1,2,4,6,8}, plus `floor((regions - 1) * 1.3)`, plus `floor(militiaMen / 60)`. Clamp 2..24 squads. Wave 2 is `round(count * 0.5)`. Last stand size by level {2,3,4,5,6,6}.
- Composition: cycle through `spearMilitia, militiaFoot, militiaPole, bowMilitia, crossbowMilitia`. Level 3 and up add `retinue_tier1`. Level 5 and up add it twice. The last stand cycle ends with `retinue_tier1` (config.lua:60-91, main.lua:188).
- No DataTable edit. The author writes that `FindRow` crashes in 0.8.104 (config.lua:7).

## Game version and signs it is stale
Target: 0.8.104 (README.txt, header). Checked against the 0.8.111 jmap:
- Present: `RTSMultiEngineCPP:getPawnBySetupIndex(Index)`, `spawnCompleteUnit(tempName, Location, Rotation, ownerPawn, companyID, arrivesInDays) -> Squad`, `PawnCPP:getAllCommandedSquads`, `getAllCommandedRegions`, `getRelevantChallenges` (returns `Challenge` structs), `playEventMessage(msgType, primaryText, secondaryText)`, `Region:getNumFamiliesOfLv(familyLevel)`, `Squad.WeightedCenter, unitType, companyID, equippedRecruits`, `PawnCPP.lordsName, isMainPlayer`.
- baron-model.md names the same baron "Hildebolt von Berenreute" in 0.8.111. So the lookup should still work.
- Not stale by name. Not tested in 0.8.111.
- Side find: `Region.settlementLevel` (Int) and `Region.isSettled` (Bool) exist in the jmap. The mod rebuilds the level from family counts because "the game does not give the level". The property is not used by any of the three Adaptive mods. A later spike can read it.

## Risk review
- Pure Lua, no file or network access, no `os`/`io` calls (grep checked). Nothing outside the game objects.
- It writes game state: spawns squads for the baron. A bug can spawn without limit; the code limits waves with `waveCount` and a clamp of 24 squads.
- It loops `getAllCommandedSquads()` and calls `:get()` on the elements (main.lua:119). This is a function return value, so it follows our crash rule (S11: do not call `:get()` on property array elements).
- Do not use together with another mod that spawns baron reinforcements (README.txt).
- License: none given. README says "100% original standalone code".

## Lessons for us
- Raids and enemy scaling: the mod does not touch raids (`spawnRaiders`, `daysUntilNextRaid`, `raidingFrequency`, `AI_aggressiveness`, `RaidSettings` do not appear in any file; grep checked). It scales an AI lord's army by spawning extra squads.
- New versus baron-model.md and spike S2: `spawnCompleteUnit(template, pos, rot, lord, companyID, arrivesInDays)` spawns ONE squad of a chosen template for ANY lord, at any point. It is the single-squad form of `spawnArmy`. A "wave" is a loop of calls plus a timer. This gives the invasion mod finer control of army size and composition than `spawnRaiders` (steps of 18).
- Steering: the mod does not move squads. It drops new squads next to a living one and lets the C++ AI take them. This matches the S11 verdict (no direct order).
- The "at war" signal for an AI lord is `#lord:getRelevantChallenges() > 0`. Our invasion mod can use the same call to know that an invasion is active, and read the `Challenge` struct fields (`status`, `DaysLeft`, `Center`, `Battlefield`, `initialBattleSquadIDs`).
- The anchor position `Squad.WeightedCenter` of a returned squad copy can be read. This is a cheap way to read where an army is. We use `SMUnit.realPos` today.
- Open: does a new squad with the same `companyID` join the old squad or form its own? The mod counts one squad per call but never checks. Does `arrivesInDays = 1` delay the squad by one day? S11 used 0.

## Test idea for the harness
Scenario `lord-reinforce`: command `lord_spawn_squad` (new, in `HarnessLords`) calls `spawnCompleteUnit` for the invader lord next to its first squad. Assert, with ranges: the squad count of the lord rises by N (N from 1 to 6) within 5 s of game time; the units have the lord's side; units of the new squad are within a few thousand units of the anchor. Then run it with `arrivesInDays` 0 and 1 and record the difference. Repeat 3 times (A/B skill).
