# Spike 1.2: does a game raid reach the manor store?

Question: when the game steers raiders (native `spawnRaiders` AI), does it take goods from the manor store?

## Method
Hidden test scenario `harness/scenarios/spike_raid_game_manor.py` on the base fixture (it has a built region manor, type 98). It puts 100 rough stone (good 27, not used by the village) in the manor with `manor_put`, starts a native raid (`spawn_raid`, 2 squads, no steering), and samples every game day for 30 days: manor stock, goods of every store, raider loot, buildings. The mod did no plunder in these runs (`RAID_BEHAVIOR plunder` is in the log 0 times; the plunder tick is for lord raids only).

## Results
| Run | Verdict | Manor stone at start | At day 30 | Lost | Raider loot at day 30 |
|---|---|---|---|---|---|
| `spike276-e` | pass | 100 | 69 | 31 | 137 |
| `spike276-f` | pass | 100 | 61 | 39 | 140 |

- The manor lost goods in 2 of 2 runs, in steps while raiders were in the village (run `-e`: -5 on day 2 to 3, then -26 on days 10 to 12; run `-f`: -10 on day 2, -17 on day 9, -11 on day 10, -1 on day 11). The manor building stayed standing and built.
- Tier 1 stores (storehouse type 6, granary type 72, others) lost goods and burned buildings at the same days. The manor is robbed in step with them: the game treats it as a store.

## Verdict
Yes. A game raid reaches the manor store and takes about a third of its goods (31 and 39 of 100). The mod does not steer game raiders. So the requirement "raiders never steal from tier 2" cannot hold for a game raid without a change by the mod. Options for the owner: accept it (and change the requirement), or restore the goods that were taken from the manor (not designed or spiked).

## Not verified
- Which raider took the goods from the manor (only the total loot and the stock were read).
- A larger raid (RAID_SQUADS option), other goods, and a Hussite role raid.
- Whether goods in a manor that came from the Manor tech (stretch) behave the same.
