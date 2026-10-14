# Summary of the mod inspection

Date: 2026-10-11. 15 items inspected by four agents (groups A to D). One note per mod in this folder; rows in `inventory.md`.
Nothing was run, installed or copied into the repo. No mod gives a license, so we use ideas and facts, not code.

## Checks done by the lead
- jmap (game 0.8.111): these names exist with these signatures:
  `Region:growPopulation()`, `Region:AddNewFamily(familyMembers) -> int`, `Region:AddNewFamilyMember(familyID, newMember)`,
  `Region:accomodateHomelessFamilies(ignoreBuilding)`, `Region:getTotalNumFamilies()`, `SMBuildingMaster:addToInventory(Good)`,
  `SMUnit:GetEquippedID(Slot)`, struct `Stat` fields `maxInRegion` (int), `placedWithin` (int), `isModule` (bool),
  `moduleCategory` (EModuleCategory), `storageLimitGeneric` (int), `requiredTech` (array).
  `SquadComponent:SetBehaviourStance`, `SetPushStance`, `PawnCPP:getSquadsNearPos`, `RTSMultiEngineCPP:FindGoodSquadMoveTargetNear`
  were already seen in the S11 jmap search.
- Our UE4SS files: `dwmapi.dll` SHA-256 starts `3f11fad9`, `UE4SS.dll` starts `87b49419`, as the group D note says.
- The notes hold no AES key and no code block longer than 8 lines.

## Findings by criterion
| Criterion | Mod | Finding | Status |
|---|---|---|---|
| M2 (build inside the manor) and the one-Keep rule | StorageAndManorUnlock, ManorLimit99 | Both lift the manor limit by data: `buildingStats` field `maxInRegion` set to 99 (Lua at run time on every row with 1..98; the pak on the Keep, Tax Collector and Palace rows). So "one Keep per region" is likely a data value that C++ reads, not a fixed rule. Neither mod touches building inside the manor. New field `placedWithin` (int) in the same row is not set by either mod and may control where a building may be placed. | Claim from code and data; not tested in the game. |
| M1 (storage in the manor) | StorageAndManorUnlock | Raises `storageLimitGeneric`, `storageLimitLarge`, `storageLimitPantry` on about 55 rows by run-time row writes. The same technique as our worker-slot write (spec 12). Its values for rows 57, 68, 72, 80, 99 match ours. | Confirms our method. |
| P3 (refugees) | RefugeesExpanded | Calls `Region:growPopulation()` up to 32 times, only on day 1 of a month, and checks `getTotalNumFamilies` before and after. A small DLL only makes the call through `ProcessEvent`; plain Lua may work. Our spike called it on other days. Also `AddNewFamily` and `accomodateHomelessFamilies` exist and were not tried. | Lead for a retry spike. |
| R3 (loot) | Battlefield Loot And Bandit Loot | No ground loot either. Reads the gear of dead units (`SMUnit:GetEquippedID`, slots 0..3), maps it to goods, and puts them into the nearest storehouse with `addToInventory`. Bandit camp rewards write `Region.regionalWealth` and `silver`. | A real-game loot path that could replace our ledger stand-in. |
| Raid and enemy size (T, D, S11) | AdaptiveEnemies | Grows the baron's army during a challenge with `RTSMultiEngineCPP:spawnCompleteUnit(template, pos, rot, lord, companyID, 1)` per squad next to `Squad.WeightedCenter`; size from level, regions and militia (2..24 squads), waves and a last stand. Finer than `spawnRaiders` (steps of 18). No mod changes the raid timer or `gameSetup`. | Technique for the invasion engine. |
| Steering (S4, S11) | all of group C | No mod orders squads. `Squad` values from Lua are copies (AdaptiveRetinueManager needs a DLL that writes raw memory). Reflected calls that remain: stances (`SetBehaviourStance`, `SetPushStance`), `RequestDisbandSquad`. | Confirms baron-model.md. Stances are a new lever to test. |
| Battle place | BetterBattlefield | Moves the `battlefield_BP_C` actors before `initChallenge` and puts them back after 500 ms, so the battle happens at a chosen place. | Technique to steer where a challenge battle is. |
| Unit stats (C3) | LargerFormations | A pak with the whole `DT_UnitTemplates` (mercenary rows 72 against 60) plus a DLL that patches six code constants. | Our run-time row write does the same for data; code patches are out of scope. |
| Battle fixtures | ML Battle Scenarios | Two saves from game 0.8.065 (TwinLakes, "Village Defense with Castle on Hill"). Not loaded. | Possible fixture only after the user approves and a load test on 0.8.111. |
| Tools | MLUE4SS-zDev, MLModMenu | zDev is stock RE-UE4SS 3.0.1-1136, older than ours; keep ours. MLModMenu is an alpha that needs a missing companion mod; do not depend on it. | No change. |
| Calendar names | several | Stale names in 0.8.104 mods: class `WeatherMaster` (fields now on `TemporalComponent`), `SMUnit.closestEnemy` (now `ClosestEnemyUnit`), `RTSMultiEngineCPP.squads`, `PawnCPP.addRetinueSquad`, `addSquadCard`. | Our harness already uses the new names. |

## Proposed follow-up spikes (each needs a game test)
1. **M2 data spike:** read `maxInRegion` and `placedWithin` of every `buildingStats` row (Keep, walls, gates, burgage, industry). Write `maxInRegion = 99` on row 57 and place a second Keep. Change `placedWithin` on a burgage row and try to place it inside a bailey. Claim to test: the one-Keep rule and the inside-manor rule are data.
2. **P3 retry:** call `growPopulation` on day 1 of a month (several times, count families), then try `AddNewFamily` and `accomodateHomelessFamilies`. Claim to test: a mod can add refugee families without a DLL.
3. **R3 real loot:** read `GetEquippedID` of killed raiders and move goods with `addToInventory`. Claim to test: loot can follow the gear of dead units instead of a ledger.
4. **Stances and battle place:** `SetBehaviourStance` on an AI squad, and moving `battlefield_BP_C` before `lord_challenge`. Claim to test: a mod can make a raid aggressive or defensive and choose where the battle is.
5. **Unit growth by `spawnCompleteUnit`:** add units to a lord's army one squad at a time during a challenge.

## Round 2 (2026-10-14): MLArmyCampMod, MLHomelessTentMod, SwapShrine, MLUE4SS 229, BetterBattlefieldMod
Notes: `ml-army-camp.md`, `ml-homeless-tent.md`, `swap-shrine.md`, `mlue4ss-229.md`, `better-battlefield.md` (re-check). Nothing was run. Claims come from DLL strings and Lua source. None is tested in the game.

| Lesson | Mod | Open issue | Status |
|---|---|---|---|
| No mod makes a buildable army or siege camp. "Encamp" is a squad skill (squad fields `camp`, `campLocation`, `rallyingStatus`) made by a native DLL. The pak is an empty shell. | MLArmyCampMod | #94 | Confirms that #94 needs a pak/data path (`siege-camp-build.md`). |
| No garrison call in the army camp DLL (the only name is `SMUnit.garrisonedIn`). It does not reuse the manor garrison (type 57, `getModularGarrisonLimit`). | MLArmyCampMod | #90/#65, #68 | Negative result. A garrisoned camp must use the manor route (a row with `garrisonLimit`). |
| The homeless tent is the game's own row 87. A mod places it by setting the pawn's building id and using the normal preview. | MLHomelessTentMod | spec 15 | Explains why our one-click `place_building` did not place a tent: use the preview and a real click. |
| Lua-only visual swap of a finished building: `KismetSystemLibrary:LoadAsset_Blocking` plus `StaticMeshComponent:SetStaticMesh`. | SwapShrine | #68, #94 (look of parts) | Technique to test. Collision does not follow the new mesh. |
| Same UE4SS build as zDev (3.0.1-1136). Ours is newer. Keep ours. | MLUE4SS 229 | none | No change. |
| Battle place lever unchanged (same archive). | BetterBattlefieldMod | spec 10 | Still unverified. |

No technique found for #90/#65 (manor commit) or #52 (walls). New spike proposals: (6) `tent-preview-place`: row 87 through the preview and a real click. (7) `building-mesh-swap`: `SetStaticMesh` on one building. (8) Read `Squad.camp` and `campLocation` while a baron army waits.