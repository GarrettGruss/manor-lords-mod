# Rebuild order: findings (2026-10-22)

Live session with the owner, slot 0, fixture `base`, runs `20261022-231049-8008` (vassal wipe) and `20261022-231824-d19d` (noop, kept open). Bridge only, no mouse for the agent. Region names: internal `Eichenhau` = Wilde Wand, `Goldhof` = Hochweg, `hofstetten` = Obere Wiese, `immenreuth` = Krumme Leite, `Nusslohe` = Riesenbuckel (player).

## Why the restored vassal did not rebuild

- After the wipe, Wilde Wand shows on the map as vacant, with no AI lord, although `region.ownerPawn` still points to the old lord pawn. With no lord, nobody builds. Adding 5 families does not bring a lord back.
- `CityPlanningComponent:ResetAIBuildingOptions` on the region changed nothing in 2 game days. `IsActive` is false on every region's planner, also on healthy AI villages, so that flag means nothing.

## What an AI lord does with rubble

- One collapsed building (Hochweg, Krumme Leite): within about one game day, the same object is a construction site again (rubble count down, site count up).
- Hochweg after a second, larger collapse (21 buildings soon after the first): no rubble was rebuilt and no new site was placed for about 8 game days. The owner thinks the quick double collapse broke the AI. Not confirmed.
- Hochweg after `demolish(true)` on all 19 rubble buildings: the lord placed new sites again and built, but at its own new spots.
- Obere Wiese, one collapse of all 34 finished buildings after all logs (7) and planks (58) were removed: the lord rebuilt in the old spots, one or two buildings at a time (34 to 25 rubble in about 10 game days). The villagers made new planks at once (0 to 48 before the give-back), so removing wood only delays a rebuild briefly.
- `addToInventory({Type, amt})` on a rubble building is accepted, so goods can be given when nothing stands.

## The rebuild order

- Rubble (`Data.bType` 75) keeps the old type in `typeBeforeChange` (0 on a standing building, the old type after `collapseBuilding`). The native rebuild flips the same object back; afterwards `typeBeforeChange` reads 75.
- No reflected rebuild UFunction exists on the building, the pawn, the region or the build panel. Hooks on the pawn and panel Blueprint functions caught nothing when the owner clicked rebuild: the panel button runs native code.
- A working mod rebuild order (burgage plot, type 3, player region; the owner confirmed a full rebuild with the house model):
  1. `old = building.typeBeforeChange`.
  2. Write `building.Data` back as a whole struct with `bType = old`, `constructed = false`, `hp = 0`, the other fields unchanged (the bridge writes whole properties).
  3. Call `building:SetupBuilding()`. It rebuilds the parts (2 to 53), restores `maxHp` (100 to 200) and storage, and the status becomes a site (`not_enough_workers` until builders come).
  4. Builders then build it as a normal construction site.
- Do NOT call `convertBlueprintsToBuildings(false)` after `SetupBuilding`: it cut the parts (42 to 6, 50 to 25), and the finished house had no model.
- Writing `Data` alone (no `SetupBuilding`) gives a "finished" building with only the rubble parts: it shows as a pile of ash.
- No crash in any of these writes or calls.

## The order in AI regions

- Krumme Leite: 3 buildings collapsed and ordered while paused (types 84, 97, 13). The type 97 site was finished by the AI builders in about 2 game days; types 84 and 13 were built later. A single ruin that the mod does not order is rebuilt by the AI itself within about a game day (the stable at -21600, 14000).
- Hochweg, full test: all logs and planks removed (0 / 37), all 35 finished buildings collapsed, 50 logs and 100 planks given to a rubble building, then the order on all 35 ruins (19 types, 11 burgage plots). All 35 became sites at once (`getConstructionResourceSituation` Y summed to 113 goods over 37 sites). The AI built 13 in about 2 game days (planks 100 to 78), against 1 or 2 at a time without the order (Obere Wiese). The owner confirmed full building models. No crash.
- Goods: a site from the order can need goods (Hochweg) or none (Krumme Leite types 84 and 13 read 0). The meaning of the X and Y fields of `getConstructionResourceSituation` (delivered, needed) is assumed, not confirmed.

## Open

- Whether it survives a save and load (needs the guarded `save_game`).
- The lord handover after a wipe (give the region to an AI lord again).
