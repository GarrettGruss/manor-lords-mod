# Q4: turn the armed villagers into bandits

State before: 3 squads registered (16 militia men in homes with 16 spears and 16 shields), families 8, residents 24.

## Weapons: removed 16, not 18
`building:consumeGoodNoCheck(good)` once per item on the homes (as `world.plunder` does). The homes held only 16 of each, so 16 spears and 16 shields were removed (18 could not be removed). Region stock went from 30 / 30 to 14 / 14 (the rest is in the storehouse). The homes then held 0.

## Route 1: SMUnit:turnToBandit on family members (`bandit_turn source=family count=3`)
| | Before | After |
|---|---|---|
| 3 units turned | family true, roles 0, 1, 2, squads 19, 0, 19 | family false, role 5 (Soldier), squads unchanged |
| `by_side` | bandit 18, civil 188, player 16 | bandit 18, civil 188, player 16 (no change) |
| Families / people | 8 / 24 | 7 / 21 |

The units leave their family and become role Soldier, but they do not become bandit units. This repeats the finding of spec 15 (`homeless-rebellion.md`). The game did not crash in the 18 minutes of game time after the call (the older note suspected a crash).

## Route 2: homeless_rebel mode home (remove 3 families, spawn a bandit squad at their home)
Before: a bandit camp made by `spawn_bandit_camp` (Outlaws pawn, 18 units, squads 22 and 23), families 7, residents 21, player side 16.
After the call: families 4, residents 12, 9 people removed (killed). A bandit squad (id 24, 18 units) appeared at the first home. Bandit units 18 to 36. Player side 16 to 10 (dead men left the militia).
The actual villagers do not become bandits. The squad is made of new units.

## What the bandits do (about 1180 game seconds watched, clock 9770 to 10950)
- No building burned (standing 17, burning 0, rubble 0 all the time). One family came back by immigration (4 to 5).
- Squad 24 walked away from the village (y -49600 to y -88700; the player is at y -53100). The AI log says "Army - enough looted. Leaving map." and "Can raid = 0".
- So the home-spawned bandits leave and do not raid in this fixture (no AI lords, raider frequency None).

## Not verified
Rallying the militia (the optional step) was not done. `mode raid` was not tried here (spec 15 did it).
