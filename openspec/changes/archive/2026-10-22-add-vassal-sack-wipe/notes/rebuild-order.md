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

## Test region choice (owner correction 2026-10-22, implementation)

- The owner's model: a vassal region is a region owned by an AI lord. In the `base` fixture the region `Eichenhau` (Wilde Wand) has no AI lord of its own: the old test scenario faked one through `settle_region`, and after a wipe the map shows it vacant. The scenarios `vassals-wipe` and `vassals-sack-end` no longer use it.
- Both scenarios now adopt an existing AI-lord region, default `Goldhof` (Hochweg, 34 buildings, owner `PawnCPP_AI`; option `VASSAL_REGION`). The smallest way to register it: the new test command `InvasionMod.vassals_adopt` (region): it reads the lord name of the region owner, takes a free slot and sets lord, handed day and handed buildings. It writes nothing to the game.
- The wipe and the restore also run on Goldhof: the lord pawn exists, so the restore hands the region to it again (`lord_receive_region` of the existing lord), then adds 5 families, goods and the rebuild order.
- The sack-end scenario uses the test option `hold` of `vassals_sack` (the sack collapses but never wipes until `vassals_end_sack`). Ending a sack right after its start ordered only 4 of 28 ruins, because `collapseBuilding` results show a little later (run 20261023-004441-9d86). A real sack end must wait until the collapses are done.
- Real runs on Goldhof (slot 0, fixture `base`): sack-end 20261023-005025-a2b9 pass (28 of 28 ruins ordered, built 2 to 6 in 15 days); wipe 20261023-005438-80b8 (26 ruins ordered, built 5 to 7 in 20 days). Run 20261023-005320-e91a crashed (access violation) at the first camera picture of Goldhof, before any mod action: a camera/screenshot call, not the sack.
- After the wipe only 26 of the 28 ruins remained (the AI removes some ruins), so the wipe check uses 70 percent.
- Earlier runs on Eichenhau (20261023-003012-a0df, -003542-1cff, -003926-72d7): the rebuild order worked (4 of 4 ordered) but the sites of that tiny village (5 buildings, lord stalled) were not built in 20 days.
- The AI rebuilds a fresh ruin about as fast as the sack collapses one (27 of 28 for 6 steps, run 20261023-010105-f526, the sack gave up and ordered the rebuild). The sack now collapses `retry_margin` (3) more than needed from the second step on. Passing runs after that: wipe 20261023-011135-bce6 (28 ruins at the wipe, 5 families, 26 ruins ordered, 400 goods), sack-end 20261023-010729-519b. Crash 20261023-010958-4796: access violation right after the wipe of the 16-family Goldhof village (4 other wipes of it did not crash; same class as the earlier same-tick wipe crash).
- After the restore the sites are built slowly with 5 families (built 3 to 3 in 20 game days in run -010329-225e, 5 to 7 in -005438-80b8), so the scenario logs it as a metric, not a check.
