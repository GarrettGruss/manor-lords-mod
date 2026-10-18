# M06 iteration 03: notes

## Findings
- Returning a lord region to the player by clearing the owner and letting the player claim it (the reverse of the M07 handover) crashes the game a few seconds later (0x50 read in native code, 3 of 3). Same address as the `ResetAIBuildingOptions` crashes of spike S13. Probable cause (not proved): the lord AI still holds the old planning component.
- Writing `Region.ownerPawn = player` only works (2 of 2 runs, 5 game days). The region keeps its planning component; `settleRegion` as the player worked on it (+5 families), the grain deposit worked (`addToInventory` into the first building), and the region kept growing (14 -> 20 buildings in 5 days; who builds is not checked: the former lord AI or the player workers).
- The lord of the slot stays in the game with no region. Its war and peace state is unchanged. The slot is flagged `capital`; the vassal scan skips it.
- Item ids from the vanilla item table (`modtools/work/DT_Items.vanilla.json`): Grain 1, Bread 172, Fish 30, Meat 147, Ale 28, Iron Ore 14, Iron ingot 35, Salt 145. M08 and M10 can use iron and salt.

## Open
- "Fortified" is a building count for now (8). A real rule can use the manor and walls (spec 12).
- The best units cannot move (no squad move order). A later iteration may spawn new units at the capital for a price.
- How the invader treats the capital (it is not the home region): the M06 sack logic still uses `core.player_region`, the first region of the player in the list. That may now be the capital. Not tested.
- Home families stay home. TBD: remove some families from home in a way that does not kill them.
