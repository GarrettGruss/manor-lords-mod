# M08 iteration 01: notes

## Open question 1 and 2 of the README
- Production of a vassal region is not read. The mod uses a formula on the family count (5 families x 20 units). Reason: the handed-over lord may not build (M07.02: 3 of 6 stalled), so building output is no base.
- Goods do not move between regions (decision 21). The mod adds goods to a home store with `addToInventory` (the route of the raid loot return) and reads the store back. A store that refuses the amount is skipped; if all refuse, `failed_deposits` counts it and the log has a warning.

## Findings
- The season jump with `set_season` triggers the tick within one poll (2 s).
- Store listing counts only buildings that hold goods, so a village with no goods anywhere cannot receive tribute. A new game start village always has goods.
- The tribute goods (`fish` 30, `timber` 16) are ids proven in older spikes. Item names for iron and salt are not known yet (M10).

## Open
- The player sees a banner ("Tribute has arrived"). `show_banner` delivery is not checked on screen (gap of the refugee mod notes).
- Iteration 02 (M08) will use loyalty from protection; the share formula already reads loyalty.
