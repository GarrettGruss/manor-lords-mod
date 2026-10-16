# Settler camp (live test with the user, 2026-10-13)

Run: `live-camp2` (fresh start, Jagged Cliffs, `run.py --new-game --scenario noop --keep-open`).
The user claimed a second region and placed a settler camp through the game UI. The agent watched with bridge hooks.

## Steps

1. Influence and silver were set on the player pawn (`MyPawnCPP_BP3_C`) with bridge `set`: `influence` 0 -> 1000, `silver` 0 -> 250.
   The cheat functions `inf` and `gold` take no amount, so a direct write was used. The UI showed the new values only after the next action.
2. The user claimed region Eichenhau. The claim used all 1000 influence (influence read 0 after it). The game then showed a victory cinematic (the claim met the victory condition of this start).
3. The user selected the settler camp and placed the ghost. Selecting and placing fired no hooked call: the build mode and placement are native.
4. A "Settlement Options" menu appeared (screenshot `runs/live-camp2/screenshots/settle-menu.png`, git-ignored):
   - Type: Town, Farming Village, Forest Village, Mining Village.
   - Starting supplies (food, wood, stone, tools; cost in silver): Modest 20/20/20/10 for 250, Average 40/40/40/20 for 500, Plentiful 60/60/60/30 for 750.
5. The user chose Town and Modest and pressed Confirm.

## Result

Confirm made one call, seen by the hook:

`PawnCPP:settleRegion(region = Eichenhau, camp = Transform(X -28729, Y 57706, Z 6079, no rotation), supply = 0, type = 1, outpost = nil)`

- `supply` is the menu index: 0 Modest (1 Average, 2 Plentiful by order; not tested).
- `type` 1 is Town. The other types are likely 2 to 4 in menu order (not tested).
- The camp transform is the placed ghost position.

Four new `SMBuildingMaster` objects appeared:

| Building | buildingFunction | occupantFamilyIDs | Likely role |
|---|---|---|---|
| 2147467294 | 7 (tent) | 0, 1, 2, 3, 4 | tent with the 5 new families |
| 2147467298 | 7 (tent) | none | empty tent |
| 2147467299 | 7 (tent) | none | empty tent |
| 2147467304 | 11 | none | probably the store of the starting supplies |

The start camp of the first region also has a tent with families 0 to 4: family ids count from 0 in each region.

## What this means

- The UI settler camp and our `settle_region` command use the same game call. The menu only sets `type` and `supply`.
- On an empty claimed region, one call gives 3 tents, a supply store and 5 families. On the player's own settled region (immigration surge) one call gives 5 families and 1 tent. The camp size depends on the region state.
- A refugee wave could use `settleRegion` on an empty region to make a full refugee camp with supplies.

## Not checked

- The building type ids of the 4 new masters (the field is not named `buildingType`; read it by the right name next time).
- `supply` 1 and 2, and `type` 2 to 4.
- Where the settlers go after some days.
