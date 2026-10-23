# Restore to 5 villagers (task 1.2, design question 2)

## Question
If the villager count of an emptied AI region is raised to 5, does the AI rebuild the village, and how long does it take?

## Method
Same test scenario and runs as `empty-ai-village.md`. After 10 game days with 0 villagers, the probe calls `settle_region` (the harness action over `PawnCPP:settleRegion`) with the region owner (the lord pawn) as the settling pawn, supply 0. The refugee feature adds families the same way (`refugees/world.lua`). Then it reads the region every 2 game days: 15 days in aec2, 30 days in be14. `family_add` cannot be used: it needs a living spare member, and the region has none.

## Results
| Run id | Ruins before | Standing before | Right after the call | End |
|---|---|---|---|---|
| 20261021-051425-aec2 | 2 | 13 | families 0 to 5, buildings 15 to 18 (standing 16) | day 14: families 5, population 14, homeless 5 to 0, buildings 16 (standing 14), approval 50 to 43 |
| 20261021-052018-be14 | 5 (all) | 0 | families 0 to 5, buildings 5 to 9 (standing 4, rubble 5) | day 30: unchanged: standing 4, rubble 5, families 5, homeless 5, approval 50 to 20 |

- `settleRegion` on a region that the AI owns works at once. It gives 5 families (10 people) and 3 to 4 new buildings. The call does not refuse an already settled region.
- The call adds its own buildings, so "5 villagers" and "a starter village" are one step here. A test of "villagers only" needs another way to add villagers (not found).
- The AI did not rebuild the ruins in 30 game days (be14): rubble stayed 5, standing stayed 4, no new construction. The 5 families stayed homeless and approval fell from 50 to 20.
- In aec2 (a village with many standing houses) the families moved into houses (homeless 5 to 0 by day 14) and the population grew (10 to 14). Buildings went 18 to 16 by day 14 (cause not found). The 2 ruins stayed.
- Verdict for the design: a villager count of 5 does not by itself make the AI rebuild a village of rubble. In be14 the AI logged `AI_build failed to find place` before and after the restore. Not verified: whether the ruins block the places (clearing them with `HarnessBuild.demolish_ruins` was not tried).
- Time to rebuild: not measured, because no rebuild happened in 30 game days.

## Not verified
- Supply values other than 0 (the supply argument of `settleRegion`).
- A restore with the ruins cleared first.
- More than 30 game days, and the effect on tribute (not read in this spike).
- Picture evidence (not taken).
