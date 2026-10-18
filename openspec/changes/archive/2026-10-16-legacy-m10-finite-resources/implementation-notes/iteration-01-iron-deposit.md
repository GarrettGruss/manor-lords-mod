# Iteration 01: how deposits are represented (spike)

Probe: `harness/scenarios/probe_deposits.py` (hidden). Runs `20261018-101128-0507`, `-101309-034a`, `-101547-d9ff`, `-101810-1437`, `-101944-cc4e`, `-102127-ee4f` (fixture base, no writes except the optional limit step).

## Findings
- jmap: `RTSMultiEngineCPP.deposits` (array), `ironResourceBP`, `saltResourceBP`, `clayResourceBP`, `depositMaterial*` exist; struct `Ore { Pos, oreComponent, iNo, Type, amt, Region }`; `DepositDecal { depositedGood, Limit, depositType, bRichDeposit }`; `ResourceNodeProperties { bIsLimitedResource, resourceCount, MinResourceAmount ... }`. EItemType: IronOre 14, Salt 145, Clay 146.
- Live (base fixture, Jagged_Cliffs): `deposits` is empty; `DepositDecal` count 0; `ResourceNode` count 35, clump kinds Berries 3, Fish 2, Stone 6, Mushrooms 4, Eel 1, empty 19. No iron, salt or clay. Underground deposits may appear only after prospecting or in other places: not checked.
- `getGoodsProducedOver(36500)` works on the `ProductionTrackerComponent` of a building. Through the bridge the keys show as RemoteUnrealParam. In the mod's own Lua state the table values are RemoteUnrealParam values too: use `:get()` (fixed in run `20261018-103029-1c81`).
- `Region:isProductionLimited/getProductionLimit/setProductionLimit/setProductionUnlimited` read and write the player workplace limits. A limit of 0 on a good with a running producer stopped its production (no new unit in 3 game days).

## Consequence
The deposit is a mod ledger that is fed by the production counter and enforced by the limit lever. A read of the game's own `Ore.amt` stays an option when deposits can be found.
