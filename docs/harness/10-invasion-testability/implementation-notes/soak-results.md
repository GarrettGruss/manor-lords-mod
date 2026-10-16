# Soak results (spec 10, U9 and criterion Q1)

Date: 2026-10-10. Scenario `soak-days` (COVERS Q1), base fixture, speed 3 (8x), real game. Run folders are in `runs/` (not in git).

## The scenario
8x speed for `HARNESS_SOAK_WALL_S` wall seconds (default 600, about 120 game days). A poll every 2 s: close pop-ups (`ctx.popups`), take a sample (clock, `daysTotal`, process memory),
check `currentGameVictoryStatus`, and give 100 Fish every 10 game days. The stall detector (`stall_s` 20) is the second line. Asserts: game process alive at the end, days run (60% to 110% of nominal),
clock rate while running (6.0 to 9.0), process memory at the end (at most 8192 MB) and its growth (at most 2048 MB). A crash gives the verdict `crash`. Numbers go to `metrics.json`.

## Q1 method: 3 of 3 passed (600 s runs)
| Run | days | game s | wall s | rate (game s per wall s) | feedings | pop-ups | stalled polls | memory start / end MB |
|---|---|---|---|---|---|---|---|---|
| soak-f1 | 121 | 4854.6 | 613.8 | 7.91 | 12 | 0 | 0 | 3597 / 3528 |
| soak-f2 | 121 | 4858.6 | 613.5 | 7.92 | 12 | 0 | 0 | 3504 / 3365 |
| soak-f3 | 121 | 4852.8 | 613.0 | 7.92 | 12 | 0 | 0 | 3562 / 3551 |

Earlier version of the scenario without feeding, also 3 of 3 (`soak-1` to `soak-3`): 120 to 121 days, rate 7.89 to 7.91, one `hunger` pop-up each (closed at the next poll, no stalled poll), memory change -200 to +14 MB.
Longer run with feeding (`soak-feed`, 1000 s): 201 days, rate 7.95, no pop-up, memory 3487 to 3571 MB. All runs: no crash, the user's saves did not change.

## The long soak: decision with numbers
- A 2-game-year run is 730 days: 3650 wall seconds at 7.9x, about 62 minutes with the boot. The clock rate was steady (7.9 in every run) and memory was flat (about +/-100 MB in 10 to 17 minutes), so time was not the problem.
- The run `soak-long3` (`HARNESS_SOAK_WALL_S=3650`, with feeding) ran **350 game days (29 minutes) without a crash**, and then ended with `GameOver`: `currentGameVictoryStatus` 1, the defeat of the settlement.
  The player village (10 people, start camp) is not defended against winter: its Approval fell to 0 and its population fell from day 345 (10, 8, 6, 4, 2). A `cold` pop-up came at about day 320 and was closed.
  Feeding cures the hunger (without it the village is defeated at day 137, run `soak-long2`), but not the cold.
- So a 2-year soak of the **unmanaged start village is not possible**. It would need a managed settlement (houses, firewood), which is a later scenario (a fixture or a situation builder, U5).
- What is verified: the method (pop-ups, stall and game-over detection, memory and rate checks, crash verdict) over 120 to 350 game days. What is **extrapolated**: the second year. Crash-free for 730 days is not shown.
- Other fact: the run `soak-long` ended with the game process terminated from outside (exit code 15, see `spike-S8.md`), not by a game error. The run was repeated.

## Not verified
- 730 game days without a crash (the village is defeated at about day 350).
- Pop-up types other than `hunger` and `cold`.
- Raids during the soak: the raid timer of the fixture is far away (about 730 days). A periodic raid is a later addition (U5).
