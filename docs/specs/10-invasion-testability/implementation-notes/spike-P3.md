# Spike P3: refugees add workers and mouths (criterion P3)

Date: 2026-10-10. Game: real game, base fixture and 9 other saves of the user (as private copies). Tools: bridge eval (experiments only).
Verdict: **not verified.** No way was found, from Lua or with one mouse click, to add a family to the village. The criterion stays unverified. What was found is written down below.

## Question
How do people arrive in the base game, and can a mod or the harness add a family so that population, workers and food use can be measured?

## What was tried
- Names: the type list of the game has no refugee, immigrant, settler or newcomer class. Only `WorkerFamily`, `SavedWorkerFamily` and `FamilyConsumptionData`.
- The quest reward struct `Reward` has `devPoints, loyalty, prosperity, Items, regionalWealth, treasury, policies, Tech, startQuests, spawnRaiderForce, spawnFreeSquads, triggerVictory`. It has no family or population field.
- `Region` has `growPopulation()` (no parameters, no result), `GetMonthlyPopChange()`, `getAvailableLivingSpace()` (struct `constructed`, `unconstructed`), `getNumHomelessFamilies()`, `getTotalNumFamilies()`, `getNumTotalPopulation()` and `SetFamilyHome(familyID, building, bool)`.
  The reads work. Start village (player region): 5 families, 10 people, 5 homeless, living space `constructed` -5, `GetMonthlyPopChange` 0.
- `growPopulation()` was called on the player region (4 argument shapes) and on all 7 regions: no error, and **no change** in families or people. The reason is probably the missing housing (living space -5): the game grows the village only when there is free housing. This was not proven.
- Housing needs burgage plots. A single click with `place_building` did not place type 3 (BurgagePlot_Lv1), 87 (HomelessTents), 107 (SettlerCampTool) or 111 (WorkerCamp): `getBuildingCount` did not change. The living space showed `unconstructed 3` only while the preview was open.
  Burgage plots are drawn with a tool (type 73, `BurgagePlotTool`) along a road. That needs several mouse actions and was not tried.
- Spawning a person: `RTSMultiEngineCPP:spawnCompleteUnit(tempName, Location, Rotation, ownerPawn, companyID, arrivesInDays)` and `spawnArmy` make soldiers. No call that makes a civil family with a home and a job was found.
  Adding a struct to `workerFamilies` from Lua was not tried, because it would be a fake family (shared unit objects) and not a real refugee.
- Other saves: the saves 11, 12, 15, 16, 19, 21, 23, 25 and 26 of the user were loaded as private fixtures (one run each). All were new starts (5 families, 10 people, no houses, silver 0). None had a village with housing.
  Save 16 failed the boot check "autosave timer was not pushed"; its numbers were read from the live game after the failed boot. The fixture entries were not kept.

## What a future attempt needs
- A way to place burgage plots (the plot tool with the mouse), or a save with a built village that has free housing. Then call `growPopulation()` and compare families, people, workers and food use per day with a control run.
  The reads are ready: `getTotalNumFamilies`, `getNumTotalPopulation`, `getNumHomelessFamilies`, `getAvailableLivingSpace`, `getNumUnassignedFamilies`, `GetFamilyConsumptionData`, `supplies_food`.
- A fixture made by hand (spec 06, `fixtures.py record`) from a save with a developed village. The user has no such save today.
- For the mod: refugees must be a mod rule, because the base game has none. The mod could use the growth path or spawn civil units. That has to be found first.

## Not verified
Everything about adding people. No scenario was written, and `criteria.json` keeps P3 as not verified.
