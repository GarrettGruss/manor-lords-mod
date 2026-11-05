# Spike: what the start kit settle call adds (2026-11-04)

Question: which call adds the 5 extra families of the start kit, and what else does it add (second camp, ox, goods)?

## Cause
`scenario_settings/init.lua` `set_families` calls `refugees.world.send_settlers`, which calls ManorCore `settle_region`, which calls `PawnCPP:settleRegion(region, camp, supply=0, type, nil)`. The game runs its "new settlement" code on the already settled region. The call adds, every time:

| What | Run skx-settle1 (one extra call) | Run skx-atcamp1 (call at the first camp spot) |
|---|---|---|
| Families | 10 -> 15 (+5, 10 more people) | 10 -> 15 |
| Homeless tent camp (type 87) | 2 -> 3 (+1, 5 families) | 2 -> 3 (+1, again a new tent) |
| Region buildings | 9 -> 13 (+4) | 18 -> 22 (+4) |
| Oxen (SMUnit role Ox) | 8 -> 9 (+1) | not read |
| Stock (all goods) | 158 -> 237 (+79: goods 15 +20, 16 +8, 172 +20, 216 +20, 234 +1, 6 +10) | 237 after (same) |

The goods are the "Modest" starting supplies (argument `supply` 0, owner payment is not taken). The ox is an `SMUnit`, so `K2_DestroyActor` is forbidden for it.
Note: the runs started with the kit already applied (InvasionMod deploys without `--pak`; the menu pak was missing, so the kit ran at once). The "start" numbers contain the kit. The numbers above are the delta of one more identical call, which is the same call the kit makes.

## Ways tested
- Camp position argument: a spot at the position of the first camp still makes a new tent (skx-atcamp1). The position only moves the new camp. No argument skips the camp, the ox or the supplies. `supply` has only the values 0 to 2 (Modest, Average, Plentiful); there is no "none".
- `Region:growPopulation()` x5 (run skx-grow1): no change (families 10 -> 10, no tent, no goods). It needs free homes and the right day, so it cannot add homeless families here.
- `Region:AddNewFamily` after `removeFromFamilyIfHasOne` (harness `family_add`): splits villagers of existing families, adds no people, makes homeless families with no tent. It is on the crash list together with worker assignment, so it is not safe for a player mod.
- `Region:AddNewFamily` with new unit objects: not tried (needs spawned villager units; no safe spawner known).

## Result
No call adds only the families. Remaining options:
1. Keep `settleRegion` and clean up: demolish the new tent camp (but its 5 families then need a tent again), `just_die` + hide the new ox (find it by comparing the Ox units before and after), and `consumeGoodNoCheck` the added goods. Fragile, not tested.
2. Accept the extras and document them (spec: "a tent camp, an ox and Modest supplies come with the families").
3. Start kit families through another way, for example more families at the first camp by a pak data change (not tested).

Not verified: the exact new buildings (+4 includes the camp and probably a supply store), where the new ox stands, cleanup methods.
Runs: skx-settle1, skx-grow1, skx-atcamp1 (all slot 1). skx-kit1 failed (menu pak did not open).
