# Great raid performance (M02 iteration 06)

Scenario `invasion-great-raid-waves`, difficulty 1, speed 3, 3 game days for each measure.

| Stretch | Run 20261018-055536-6790 | Run 20261018-055939-5195 |
|---|---|---|
| Baseline | 0.097 days/s | 0.097 days/s |
| Wave 1 (15 squads) | 0.099 | 0.061 |
| Wave, relief 15, final 25 squads | 0.099 | 0.067 |

Findings:
- No crash with 15 + 15 + 25 squads. No frame or Lua errors in the second run.
- The measure is coarse. The time control steps in whole days, so a speed change below about 30 percent is not visible. The second run shows a 30 to 40 percent slow-down, the first shows none. Treat it as noise until a frame time probe exists.
- A boot crash happened once (run 20261018-055825-d24f, during the load, before the mod ran). It is not linked to the squads.
- The first run logged `world.lua:37: attempt to compare number with AActor` once, right after the force start. The loot read is now type checked.
- The real final battle was not fought. G4 (the win) is tested in the fake game only.
