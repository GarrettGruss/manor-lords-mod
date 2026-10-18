# Start and victory settings: static findings (spec 26, step 1)

Date: 2026-10-15. Method: search of the game jmap (build 40574608), strings of `DT_GameSetupPresets.uasset`
(in `modtools/work/ua-scan/`), the fixture manifest, and the notes of specs 06, 10, 12 and 15.
No game was run. The jmap shows names, types and default values. It does not show native code.
So the code that checks victory is not known yet.

## 1. Settings objects and fields

### 1.1 `MLGameInstance` (`/Script/ManorLords.MLGameInstance`)

| Field | Type | Default (jmap) | Meaning |
|---|---|---|---|
| `scenario` | Name | `None` | Name of the start preset (for example `survival`, `duel`). |
| `gameSetup` | `GameSetupPreset` | Conquest, day 61 (see 1.3) | Full setup of the current game. |
| `gameSetupDifficulty` | EGameDifficulty | `Custom` | Difficulty. |
| `currentGameVictoryStatus` | EVictoryStatus | `Ongoing` | Victory state. |
| `startingSetup` | Array of `PlayerStartingSetup` | empty | Start positions (`startingLocation`, `attachedPlayer`, `isAI`). |
| `startWithCart` | Bool | `False` | Start with a cart. |
| `aggressive_AI`, `AI_behaviour` | Bool, Byte | `False`, `0` | AI settings. |
| `triggerQuests` | Bool | `False` | Story quests on or off. |
| `savefileToLoad` | String | empty | Save slot to load. Empty means a new game. |
| `DT_GameSetupPresets` | DataTable | (asset) | The preset table (see section 2). |

Functions (names only): `ApplyPreset`, `GetPreset`, `setCurrentGameSetup(setupPreset, chosenDifficulty)`,
`isCurrentGameSetup(setupPreset, outDifficultyThatMatches)`, `UpdateGameSetupParameters(OldParams, bForce)`,
`getStartingSupplies(Level, outCost)`, `getSpoilageRateFromGameSetting`, `setStartLocation`, `setRandomStartLocations`,
`unassignedStartLocation`, `SetNumAILords`, `getMaxAILords`, `isRegionEmpty(InRegionData, OutVillagesInRegion)`.
Delegates: `OnGameSetupChanged`, `OnGameSetupParamsChanged`, `onStartLocationChanged`.

### 1.2 `MLSaveGame` (`/Script/ManorLords.MLSaveGame`)

The save keeps copies of the same values:
`gameSetup` (GameSetupPreset), `scenario` (Name), `AI_behaviour`, `triggerQuests`, `currentGameVictoryStatus`,
`scenario_nextActionDay` (Int), `kingsFavour_daysLeft`, `lastBanditCampSpawnedDay`, `enableFertilityGrid`.

A loaded game may read these values from the save. A run-time write to `MLGameInstance` may not change the save copy.
This is not tested yet.

### 1.3 Structs

`GameSetupPreset`: `Thumbnail`, `isMainGameMode` (Bool), `customTags` (array), `mapOverride` (Name),
`gameSetupData` (map), `currentGameSetup` (`GameSetupParameters`).

`GameSetupParameters` (name [type]):
- `startingLocation` [array of Transform], `startingLocation_AI` [map]
- `goals` [EGameGoals]: the victory goal (see section 3)
- `numGenericAILords` [Int], `adversary_baron` [Bool], `AI_aggressiveness` [Byte]
- `maxBanditCamps`, `initialBanditCamps`, `raidingFrequency`, `yearsUntilFirstRaid` [Byte]
- `generateWaterVeins` [Bool], `resourcesRandomization` [Byte]
- `startingSuppliesMultiplier` [Int], default 1
- `armamentDelivery` [Bool], `loyaltyLossRate`, `consumptionRate`, `treeGrowthRate` [Float]
- `requirementDiscontentBias`, `royalTaxMultiplier` [Int], `spoilage`, `weatherDamage` [Byte]
- `startingDay` [Int], default 61 (March 2, year 1)

Default preset values (default object of `mainMenu_GameSetupPresetButton`): `goals` = Conquest,
`numGenericAILords` = 0, `maxBanditCamps` = 3, `initialBanditCamps` = 3, `yearsUntilFirstRaid` = 2,
`startingSuppliesMultiplier` = 1, `startingDay` = 61, `spoilage` = 2, `weatherDamage` = 1.

Not in the structs: ruins, starting families, starting population, starting buildings. No field sets them.

### 1.4 Enums

- `EGameGoals`: `Conquest`, `Dominance`, `Endless`, `Growth`.
- `EVictoryStatus`: `Ongoing`, `Victorious`, `Lost`.
- `EGameDifficulty`: `VeryLow`, `Low`, `Medium`, `High`, `VeryHigh`, `Custom`.

### 1.5 Menu side (UI)

- `/Game/UI/Game_Setup/mainMenu_GameSetup`: `Open`, `Close`, `UpdateAll`, `UpdateGameSetupFromSetting`,
  `getCurrentGameSetup`, `repopulateGamePresets`, `SetOptionAvailable`, `UpdateAILordCountSetting`,
  `changeVictoryConditionsOptionsBasedOnAIPresence`. The victory option set depends on AI presence.
- `mainMenu_GameSetupPresetButton`: property `setupPreset` (GameSetupPreset).
- `W_Menu_DifficultyRadioButton`: `UpdateSelected`, `HandleInput`.
- New game flow: `mainMenu_widget:startNewGame`, `mainMenu_widget:newGameSettingsIsCreatedAndVisible`,
  `W_MainMenu_GameStartScreenV2:open_newGameScreen`, `mainMenu_widget:getScenarioName`.
- `/Game/UI/New_Settlement/settlementInitializerWidget` (`chooseScenario`, `scenarioPicked`) is the settler camp
  type menu (spec 15), not the start menu.

## 2. Preset data table

`/Game/ManorLords/Database/DT_GameSetupPresets` (`pakchunk0_s4`, row struct `GameSetupPreset`).
Row names found in the asset strings: `baron`, `duel`, `fractured_realm`, `peaceful_citybuilding`, `survival`.
The strings `mode_burned`, `mode_citybuilding`, `mode_baron2` are icon paths under `/Game/ManorLords/UI/ScenariosAndModes/`.
Their row names are not confirmed.
The row values are not read yet. The asset is binary, so a parser is needed to read each row's `goals`.

## 3. Victory: candidates

| Candidate | Where | Evidence | Use |
|---|---|---|---|
| `goals` (EGameGoals) | `GameSetupParameters` in `gameSetup.currentGameSetup` | Enum in jmap. Default Conquest. | The goal of the game. Possibly read by the claim check (not proven). |
| `currentGameVictoryStatus` | `MLGameInstance`, `MLSaveGame` | Enum: Ongoing, Victorious, Lost | Victory state. A claim may set it to Victorious (not proven). |
| `PawnCPP:createAndPlayVictoryCinematic` | `PawnCPP` (player pawn) | Function, no parameters in jmap | The cinematic. Inferred from spec 15 to run on a victory. |
| `PawnCPP:triggerDefeat` | `PawnCPP` | Function | Defeat path. Comparison only. |
| `MLCheatManager:triggerVictory` | cheat manager | Function | Starts the victory path with no claim. Control for the cinematic. |
| `UI/Events/Victory_Domination/dominance_wip_*` | UI assets | spec 12 `unused-assets.md`: WIP, not used in the game | Not used. |

Evidence from notes: spec 15 `settler-camp.md` (line 10) says the claim of Eichenhau "met the victory condition of this start"
and the victory cinematic played. The goal of that start was not recorded. It was probably the default (Conquest).

## 4. Claim path (region claim and influence)

- `PawnCPP:layClaim(Region, useFavour, consumeInfluence)`: the claim call. `consumeInfluence` = true spends influence
  (spec 15: one claim used all 1000 influence).
- `PawnCPP:finalizeClaim(Region, Remove)`: finishes the claim, or removes it when `Remove` is true.
- `PawnCPP:refuteClaim`, `withdrawAllClaimsAndChallengesTowards`, `updateClaims`, `updateClaimsUI`, `canClaimSomething`,
  `updateClaimBlocked`, `getRelevantClaimedRegions`: claim checks and UI.
- `PawnCPP:changeInfluence(change: Float)`: changes influence. Spec 15 wrote the `influence` field with the bridge.
- `PawnCPP:settleRegion(regionToSettle, SettlersCampLocation, supplyLevel, settlementType, outpostToRegion)`: the settler camp call (spec 15).
- `PawnCPP:declarePeace(targetPawn)`: peace with another lord. Not checked as a victory path.

The victory check is probably in `finalizeClaim` or in a function it calls. This is not proven.

## 5. Start state fields (for A3, plundered start)

- `startingSuppliesMultiplier` (default 1) scales the starting supplies. `getStartingSupplies(Level, outCost)` gives the supply list.
- `startingDay` (default 61) sets the start date.
- `startingLocation`, `startingLocation_AI`, `startingSetup`: start positions. No ruins, families or population field.
- `numGenericAILords`, `initialBanditCamps`, `maxBanditCamps`: AI and bandit start.
- Ruins: building types `EBuildingType::Scenario_DestroyedGranary` and `Scenario_DestroyedWindmill` and
  `EBuildingFunction::Scenario` exist. Their use in a start is not known.
- `BP_VillageSpawner` has `farmingVillage`, `woodcutterVillage`, `scenarios`. `BP_UnitSpawner` has `scenario` and `spawnCamped`.
  These are per-village and per-unit data, not start settings.
- Run-time family code: `Region:AddNewFamily`, `Region:accomodateHomelessFamilies`, `MLGameInstance:isRegionEmpty`.
- Fixture facts: a new game on Jagged Cliffs starts on day 61 with 5 homeless families and population 10 (spec 06 `fresh-start.md`).
  The start region is random.

Result for A3: no start setting gives ruins, a small population, or low supplies. `startingSuppliesMultiplier` changes only the amount of supplies.
The plundered start needs Lua after the start: sack and fire (spec 10 S6 works at run time), and family changes with the `Region` functions.
A pak change of `DT_GameSetupPresets` is the other option. It is not proven that it sets ruins.

## 6. Hooks to observe (observe only, no writes)

Bridge `hook_function` on:
- `/Script/ManorLords.PawnCPP:createAndPlayVictoryCinematic`: count calls. The main signal.
- `/Script/ManorLords.PawnCPP:layClaim`: log the region and `consumeInfluence`.
- `/Script/ManorLords.PawnCPP:finalizeClaim`: log the region and `Remove`.
- `/Script/ManorLords.PawnCPP:triggerDefeat`: count calls.

Bridge `get_property` (read only):
- `MLGameInstance` (game instance object): `currentGameVictoryStatus`, `gameSetupDifficulty`, `scenario`, `gameSetup.currentGameSetup.goals`.
- Player `PawnCPP`: `influence`, `silver`.

Do not call any save function (CLAUDE.md Safety). Do not use `eval_lua` for this step.

## 7. Plan for the real-game test (A2)

Goal: one run where a region claim gives no victory cinematic after a Lua change.

Fixture and start:
- Use a new game on Jagged Cliffs, as spec 15 did (`live-camp2`): `run.py --new-game --scenario <name> --keep-open`
  or `load_save.py --new-game`. No fixture file is written, and no save is written.
- A fixture is optional. If one is needed, use `base` (a copy of the user's save, read through the harness).
  Do not load a user slot directly.

Steps:
1. Boot. Read the state (section 6). Expect `currentGameVictoryStatus` = Ongoing and `goals` = Conquest. Save the values in the run folder. This is the control.
2. Set influence to 1000 on the player pawn with the bridge `set_property` (as spec 15). Read it back.
3. Control run (no change): claim Eichenhau or a neighbour with `layClaim(Region, useFavour=false, consumeInfluence=true)`.
   Expect 1 call of `createAndPlayVictoryCinematic`. If there is no cinematic, the claim gives no victory in this start, and the test is not valid. Stop and report.
4. Change run (new game, same steps): before the claim, set `gameSetup.currentGameSetup.goals` to `EGameGoals::Endless` on `MLGameInstance`.
   Write the nested field, then read it back. Keep `currentGameVictoryStatus` at Ongoing.
5. Claim the same region. Expect 0 cinematic calls and status still Ongoing.
   If the cinematic still plays, the check does not use `goals`. Then try `Growth` and `Dominance` and record each result.
   Also record whether a change to the save copy (`MLSaveGame`) matters. Do not write to save files.
6. Record hook counts, property values before and after, a screenshot, and the game day. Repeat 3 times per case (the game is not deterministic).

Pass criteria for A2: the change run has 0 cinematic calls and the control run has 1.
If no value stops it, record the next option in the spec: a Lua hook that cancels `createAndPlayVictoryCinematic`
(if it can run before the function), or a pak change of the goal (if the check reads data).

Checks that must stay true: no file in the user's save folder changed (the launcher hash guard). No `Request Autosave`.

## 8. Open questions

- Which code reads `goals`? Not known from the jmap. Step 4 of the test answers it.
- Does `createAndPlayVictoryCinematic` run from `finalizeClaim` or from another function? Hook both.
- Does the running game use a runtime write to `MLGameInstance.gameSetup`, or only the save copy? Not known.
- Preset rows: which rows exist, and their `goals`. A parser for the `.uasset` is needed.
- Ruins and start families: no field found. The menu flow may show a setting that is not in the struct. Not checked.
- The fixture saves were not scanned for setting names (the save data is compressed; strings did not show them).

## 9. Sources used

- Game jmap: 38233 objects. Searched by object name and by property name.
- `modtools/work/ua-scan/ManorLords/Content/ManorLords/Database/DT_GameSetupPresets.uasset`: 1327 bytes, strings only.
- Notes: `openspec/changes/archive/2026-10-15-legacy-15-bandit-settlement/implementation-notes/settler-camp.md`,
  `openspec/changes/archive/2026-10-15-legacy-12-manor-exploration/implementation-notes/unused-assets.md`,
  `openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/implementation-notes/fresh-start.md`, `fixtures.md`, `fixture-load-bug.md`,
  and `harness/fixtures/fixtures.json`.
