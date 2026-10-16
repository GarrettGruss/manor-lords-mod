# MLHomelessTentMod 1.0.1-alpha.2 (inspection note)

Date: 2026-10-14. Source: `C:\Users\garre\Downloads\MLHomelessTentMod-262-1-0-1-alpha-2-1756945974.zip` (Nexus file id 262; 1756945974 = 2025-09-03). Local copy (git-ignored): `modtools/example-mods/ml-homeless-tent/`. Nothing was run.
Archive: 1,085,080 bytes, SHA-256 `f60bdad3f1914c8157783b2948d59bb203d0dd9bd35b1ec9fe628734fa16a5c9`. Author Psiae (same framework as MLArmyCampMod and MLModMenu). No license text.

## What it does for the player
It lets the player place the "Homeless People Tent" building (the shelter that the game puts up itself for homeless families) by hand, from the UI. The log line says so: `set placeBuilding id to: "{}" (Homeless People Tent)`.

## Mechanism
- Native UE4SS C++ DLL only: `dlls/main.dll`, 4,514,816 bytes, SHA-256 `85bc19106460aeeb8ee8afccc45b229593a02126b55fc461c0b1f04c71ad76a5`. No pak, no Lua. Other files: `enabled.txt`, `modManifest.json`, `modManifests/ue4ss/modManifest.json` (target UE4SS 3.0.1-450). Companion mods named in strings: MLModPresence and MLModMenu (not in the archive).
- Console command `k.homelessTent.placeHomelessTent` (also `ping`, `isInGame`, `printModInfo`).
- From the strings: it sets the pawn's "building to place" id to the tent, so the normal placement preview starts, and it watches the floating building tooltip ("Building floater not updated"). It does not create a building. It reuses the game's tent (spec 15 `tent-placement.md`: `DisplayName` `homeless_tents`, blueprint `BM_HomelessTents`, type id 87, `buildingFunction` 7 Temporary).
- Names in the DLL: `Region` functions `accomodateHomelessFamilies`, `accomodateHomelessLivestock`, `addNewFamily`, `spawnNewFamilyMember`, `setFamilyHome`, `removeWorkerFamilyAt`, `getAllCommandedRegions`, `getRegionByPos`; properties `occupantFamilyIDs`, `assignedFamilyIds`, `workerFamilyID`, `familyHome`, `familyMembers`, `regionalWealth`; bandit camp names `spawnBanditCamp`, `spawnCamped`, `initialBanditCamps`, `maxBanditCamps` (probably only read); UI classes `regionViewOverlay`, `packTrainPlanner_InterRegion`, `buildingCardWidget`; type `EBuildingFunction`.
- An assert string: "accommodated familyID does not exist in homeless family pool". So it also moves homeless families into the tent.
- This is read from strings only. The logic itself was not disassembled.

## Game version and staleness
Built for UE4SS 3.0.1-450 (2025-08) and an old game build. No game version string found. UI names such as `regionViewOverlay` were stale in other 0.8.104 mods (spec 13 summary). Assume it does not work on 0.8.111 without a rebuild.

## Risk review
Native 4.5 MB DLL with a bundled framework. No network API names found. Unsigned. Do not install. Crash risk on a new game build.

## Lessons for us (spec 15 refugee waves)
- The tent is placed by selecting the existing building id on the pawn and using the normal preview. Our spike (`tent-placement.md`, spike P3) called `place_building` for type 87 with one click and nothing was placed. This mod suggests we need the preview mode (pawn `placeBuilding` set, preview shown) and then a real click on valid ground, as in spec 12 round 2.
- Functions to try in a Lua spike: `Region:accomodateHomelessFamilies(ignoreBuilding)`, `Region:AddNewFamily`, `Region:SetFamilyHome(familyID, building, bool)`. All exist in the jmap (spec 13 summary).
- It adds no tent class and no data row. Answer to "how does it make tents": it starts placement of the game's own tent.

## Test idea
Scenario `tent-preview-place`: set the pawn `placeBuilding` to row 87 through the bridge, check that the preview (`DummyBuilding`) exists, click a valid spot with the real-click tool from spec 12. Assert `Region:getBuildingCount(87)` rises by one. Then call `accomodateHomelessFamilies` and assert `getNumHomelessFamilies` falls.
