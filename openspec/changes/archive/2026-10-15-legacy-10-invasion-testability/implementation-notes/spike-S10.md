# Spike S10: performance with many raiders

Date: 2026-10-10. Runs: probe-s10-a, probe-s10-b, series of `raid-load` (3 of 3).

## Question
How does the game clock rate change with the unit count, at 1x and 8x? Does the game stay responsive?

## Method
Raider squads were spawned in steps (`spawn_raiders`, 6 squads of 18 per step, at the player position). After each step the speed was set (`set_speed`), then the clock was read over 6 wall seconds (`measure_clock`). Rate = game seconds per wall second. The game was paused during the census and the bridge cost test (30 clock reads).

## Results
| Units (all) | Rate at 1x | Rate at 8x (speed 3) | Census ms |
|---|---|---|---|
| 202 / 220 | 1.02 / 1.03 | 8.23 / 8.15 | 8 to 13 |
| 312 / 329 | 1.02 / 1.02 | 6.71 / **refused** (game reports speed 1 after 3 tries) | 12 to 17 |
| 420 / 441 | not measured / 1.02 | not measured / 2.99 | 17 |
| 550 | 1.03 | 1.55 | |
| 661 | 1.02 | 6.87 | |
- 1x stays at 1.02 to 1.03 for all counts up to 661 units. The game was responsive (bridge and census answered) at all counts; no stall, no crash.
- 8x falls from 8.2 to 1.5 (550 units) but is not monotonic (661 units: 6.87). The simulation is not deterministic and the raiders act differently in each run (fights, walking), so this is a trend, not a law. At 329 and 420 units the game refused 8x once (it drops back to 1x): this may be the game slowing the speed when an enemy is near. Not analysed.
- Cost of one bridge call (a clock read: engine lookup plus call) was 128 to 139 ms, with 200 to 661 units. It did not grow with the unit count.

## What this means for Q2
A 300-unit battle keeps 1x at the real rate. A test at 8x must expect a lower rate and must allow the speed to be refused. Scenario `raid-load` checks the 1x rate (0.8 to 1.3) with at least 300 units and the census cost.

## Verdict
method verified for the clock rate at 1x (`raid-load`) and for recording 8x rates (probe). The 8x rate is not asserted in a scenario because it is too variable.
