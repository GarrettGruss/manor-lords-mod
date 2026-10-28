# Rebellion raid in the real game (tasks 2.3, 2.6, 2.7)

Test scenario `bandits-rebellion-raid` on fixture `playtest-noai` (5 families, AI opponents 0, no Outlaws pawn at the start, unarmed homes). Slot 1, game speed 3.
Runs: `rb-raid-8`, `rb-raid-9`, `rb-raid-10` (all pass). Failed setup runs `rb-raid-1` to `rb-raid-7` found the problems listed below.

## What the test does
1. Waits for the Outlaws init and its camp cleanup.
2. Unarmed village: the timer is expired at once (`bandits_set_timer_days_left days=0`): the rebellion is blocked, 0 valid families found, 4 needed (5 families, the village keeps 1). Nothing is removed, the order stays 20, the timer stays expired.
3. 2 armed homes: after a new tick the rebellion is blocked again (2 of 4).
4. All homes armed: after a new tick the rebellion starts: 4 families leave (the village keeps 1), the goods of those homes are taken (14 to 16 items), 18 Brigands spawn 268 to 269 units from a removed home, and all taken goods are loot overrides.
5. The AI raids: first building burning after 20 to 30 game s, "enough looted" after 40 to 50 game s, the order rose by 25.
6. 10 more game days pass without a crash.

| Run | Burn (game s) | "enough looted" (game s) | Spawn distance | Stock change | Bandit units 180 s later / end | Override entries after the leave |
|---|---|---|---|---|---|---|
| `rb-raid-8` | 30 | 50 | 269 | -109 | 18 / 18 | 18 |
| `rb-raid-9` | 20 | 40 | 269 | -118 | 18 / 18 | 16 |
| `rb-raid-10` | 30 | 50 | 269 | -103 | 18 / 18 | 14 |

## Findings
- **The raid is fast here** (burn after 20 to 30 game s, leave line after 40 to 50 game s, against 37 to 108 and 108 to 202 in the older spike). The squad spawns at the home, 270 units from it, and the AI has no other target (AI opponents 0).
- **Plunder** (spec "Plunder by Outlaws squads"): the region stock fell by about 100 to 120 goods. Burning also destroys goods, so the stock change records the loss but cannot split looting from burning. The units' `ItemsLooted` was not read.
- **Removal at the map edge** (spec "Removal at the map edge"): the 18 bandit units are still counted 180 s and about 770 s after the spawn. They stay on the map (they do not vanish at the edge). The override entries of units that the game no longer lists are dropped (18 entries became 14 to 16); the cause (units that died while raiding, or left the list) was not read.
- **Repeat rebellion** is not checked in the real game.
- **A spawn in a paused game** works only after a warm-up with retries at the start of the scenario (the intro holds the clock). Without the warm-up, `TimeControlError` after the spawn (runs `rb-raid-4` to `rb-raid-7`).
- **Goods leave homes** about 1 game day after a test put them in (see `homes-inventory.md`). The timer expires at once with the game paused (`days=0`) so the mod looks at the homes before that.
- **Shared homes**: two families can live in one home; the mod takes the goods of a home once.
- **`bandits-banditry-timer`** (task 2.7) was updated: 55 to 65 days at the start, up to 6 families, one squad of 18, no camp, the pawn not made by the leave event. It passes on `base` (`rb-timer-1`) and on `playtest-noai` (`rb-timer-3`). `bandits-banditry-banners` passes (`rb-bandits-banditry-banners-1`), `bandits-buy-back` passed on the second run (`rb-buy-2`; the first run `rb-bandits-buy-back-1` crashed after the buy-back letter, access violation 0x60, not reproduced) and `bandits-order-tick` passes.
