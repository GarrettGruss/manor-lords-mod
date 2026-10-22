# Salt mine deposit (live spike, partial)

Run `20261022-013541-4c3a` (`--keep-open`, slot 0, bridge only, no save call, no game day used, nothing written). Mine: `SMBuildingMaster_2147455918` (type 7, function 18, region Nusslohe).

## Result: the number 1194 was NOT found in any reflected property
The UI text "Salt (Surface Deposit: 1194) / Rich Resource / Endless Underground Reserves" is in `MainUICPP_C.WidgetTree.WhiteTooltipRT` (RichTextBlock). It is only the display. Searched for a numeric value 1100 to 1300 (also nested in structs and arrays) in all properties (with super) of: the mine (234), the nearest `ResourceNode` (88), `RTSGameManager` (368), the player pawn (540), region Nusslohe (133), and the mine components `ProductionTracker`, `Maintenance`, `Proficiency`, `Expertise`. No hit.

## Facts
- `ResourceNode_2147458837` is 446 units from the mine (the next one is 15000 away): it is the salt zone. Its own props are only decals (`ResourceZoneDecal`, `PaperMapDecal`); `resourceClumps` is empty; the only own function is `onPaperMapViewChanged`. So the deposit amount is not a reflected field. Likely C++ data or a texture mask (engine props `resourceZoneMaterials`, `depositMaterial_Salt`).
- The mine `Resources` array (12 entries) holds plain visual `SMBuilding_*_res_<good>_<n>` actors (goods 14, 17, 146). They have no amount field.
- `RTSGameManager.deposits` is empty; no live object of class `Deposit`, `DepositDecal`, `Ore`, `ResourceZone*`, `Resource_Salt_C`.
- No function name with deposit, reserve, rich, endless, infinite, surface on the mine, parts, region, pawn or engine. Related functions: `engine.findResourceByPos(Vector)` (returns `<invalid>` at the mine position), `engine.getResourceBP`, `mine.getNearestResource` (2 params, types unknown, not called), `mine.IsMineBuilding` = true, `mine.CanLimitProduction` = true.
- Region Nusslohe: `isProductionLimited(145)` (salt), `(14)`, `(27)` all false. `getProductionLimit` takes 2 parameters (good and a second one, unknown).
- The mine has no workers (`numActiveWorkerFamilies` 0, `assignedFamilyIDs` empty), so no production happened and the value could not be watched over a game day. No harness command to assign workers was used.

## Not done
Tasks 1.2 to 1.4 for salt (read after production, set a high value, flag toggle): there is no field to read or write. Left unchecked.

## Open points
- Find the rich and endless flags: they are not reflected on the mine, the node or the region. Candidates: unreflected C++ in the ResourceNode, or a texture mask.
- Next steps: call `getNearestResource` with a guessed signature (position and good id); hook `updateTooltip` / `getSmallTooltip` on the pawn and read args; or use a mine with workers and compare `ProductionTracker` over days.

## Follow-up: 3 families assigned (same run, game days 251 to 254, 3 game days used)
- Mine: `assignedFamilyIDs` [10, 11, 7], `numActiveWorkerFamilies` 3. `ProductionTrackerComponent.timeEntries[labor].numberOfTasksComplete`: 0 after day 1, 3 after day 2, 20 after day 3. So the mine produces. The mine `Inventory`, `numStoredGeneric`, `yield` stay 0/empty (salt does not stay in the mine).
- Tooltip: `WhiteTooltipRT.Text` is empty when nothing is hovered. The "Surface Deposit" number exists only while the owner hovers the salt node, so it was not readable per day without the mouse. Not recorded. A hook on pawn `updateTooltip` / `getSmallTooltip` was not tried (the MCP bridge tools point at the wrong bridge folder).
- `mine.getNearestResource(good:int, pos:Vector)` (order: good first): good 14 returns `SMBuilding_2147455902_res_14_0`, good 17 returns `SMBuilding_2147455897_res_17_1` (the visual res parts of the mine); goods 145 (salt), 27, 15, 0, 1 return `<invalid>`. Vector first fails with a struct conversion error.
- `engine.findResourceByPos(Vector)` returns `<invalid>` at the mine position.
- `region.getProductionLimit(good, 0)` returns 0 and `(good, 1)` returns 1 for salt (second parameter looks like a flag or index; meaning unknown); `isProductionLimited` false.
- No writable source of the amount found, so no set test and nothing to restore. Nothing was changed.
- Next: have the owner hover the salt node while a day runs and read the tooltip text, or hook `updateTooltip` through the run's bridge folder.

## Follow-up 2: hover test (same run, game day 255; 4 game days used in total)
- Reading `WhiteTooltipRT.Text` for 30 s before the day: empty (hover not seen). After 1 more game day it read "Mining Pit" (a building hover, not the salt node), so the mouse was not on the deposit.
- `ProductionTracker.timeEntries[*].numberOfTasksComplete` (5 entries): before the day [20, 0, 2, 0, 106], after the day [36, 2, 3, 0, 160]. The mine keeps producing.
- No "Surface Deposit" number was read, so whether the deposit goes down is still unknown. Stopped after 1 day to save game days.

## Follow-up 3: hover on the salt node (game days 255 to 258; 7 game days used in total)
| Moment | Surface Deposit | tasks complete (5 entries) |
|---|---|---|
| Before follow-up 1 (owner UI) | 1194 | - |
| Day 255 (start of this test) | 1193 | [36, 2, 3, 0, 160] |
| Day 256 | 1192 | [56, 3, 3, 0, 197] |
| Day 257 | 1191 | [77, 4, 4, 0, 217] |
| Day 258 | 1190 | [96, 5, 4, 0, 227] |
- The surface deposit falls by 1 per game day with 3 families on the mine. The amount is still not a reflected field (still not found); it is only readable from `WhiteTooltipRT.Text` while the node is hovered. Nothing was written, nothing to restore.
