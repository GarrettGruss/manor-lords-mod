# Q3: do the registered villagers stock the weapons in their homes?

The squads were registered and never rallied. Game speed 3, one snapshot every 6 real seconds (about 50 to 60 game seconds; a game day is 40 s). Homes are the 6 buildings with `bType` 3 (burgage plots). Clock is `getGameTimeAdjusted`.

## Result: TRUE, one spear and one shield for each militia member
Squad 19 (10 men) was registered at clock 4676. Goods moved from the storehouse into the homes over about 6 game days:

| Clock | Storehouse spears / shields | Spears / shields in the 6 homes | `getNumAssignedMilitaryStockOfType` |
|---|---|---|---|
| 4687 | 30 / 30 | 0 / 0 | 0 |
| 4985 | 27 / 30 | 1 / 0 | 11 |
| 5105 | 20 / 23 | 7 / 7 | 12 |
| 5225 | 18 / 18 | 12 / 12 | 12 |
| 5823 | 18 / 18 | 12 / 12 | 12 |

Then squad 20 (6 men) was added at about clock 5830. The homes went to 16 / 16 by clock 6900 (storehouse 14 / 14) and stayed there. The third squad (4 men, about clock 7800) added no more weapons in the next 900 game seconds (still 16 / 16, assigned 16).
So the homes hold one spear and one shield for each man of the first two squads, 2 to 4 sets for each home. The goods stay in the home inventory (`building.Inventory`). The region stock (`getStockOfGood`) still counts them (30 / 30).
Population grew during the watch (5 to 8 families) because immigrants arrived.

## Not verified
Why the third squad got no weapons (a delay, or a limit of two squads, or the new men had no home slot).
