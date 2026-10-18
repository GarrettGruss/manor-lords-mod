# Open items of spec 10 (2026-10-12)

These items need the real game. They were not done in the housekeeping of issue #53. Each one stays open.

| Item | State | Reason it is open |
|---|---|---|
| Spike S11 (baron model, `baron-model.md`) | ran once | Not run again. `lord_claim`, `lord_declare_peace` and the "challenge lost" path were not run. Needs the game. |
| Spike S13 (dynamic lords, `dynamic-lords.md`) | ran once (4 runs, 6 lords) | Three runs per variant not done. Save and load of a spawned lord, what the player sees, growth beyond 20 days and other settlement types are not verified. Needs the game. |
| Soak run (Q1, `soak-results.md`) | stopped at about day 350 of 730 (village defeated) | A full 730-day run needs a safer fixture and the game. No raids ran during the soak. |
| Real A/B suite (`ab-statistics.md`, spec 09) | one run per side only | N runs per side need the game. |
| P3 refugees | not verified | Retry `growPopulation` on day 1 of a month (lead from spec 13). Needs the game. |
| M2 normal buildings in the manor area | not verified | Test `maxInRegion` and `placedWithin` (spec 12 and 13). Needs the game. |
| "Not verified" sections of spikes C1, C2, P5, R8, S6, S7, S9 | open | Collected here. Each one needs the game. |

## Update 2026-10-13 (issue #53, game items)

| Item | State |
|---|---|
| P3 refugees | Moved. Done in spec 15 (#51, mod `RefugeeWaves`). |
| M2 normal buildings in the manor area | Moved to issue #68 (spec 17). |
| Real A/B suite (spec 09) | Done. Suite `pak-ab`, 5 runs per side, different (0.5 -> 0.75, p 0.008). Spec 09 box ticked. See spec 09 `ab-n-runs.md`. |
| Spike S13 rerun | Partly run. Suite `lord-village-ab` (3 variants x 3 runs) was stopped after 2 runs: Claude Code killed the background shell because the machine ran low on memory. Run 1 (`supply-0`): pass; the lord village stayed at 5 buildings for 30 game days and the lord logged no `AI_build` line (`build_lines` 0). Run 2 (`supply-2`) has no summary. This differs from the first S13 result (4 -> 14 buildings), so "the lord builds" is NOT confirmed on the `base` fixture with other lords present (an earlier try with supply 2 logged `AI_build failed to find place: LoggingCamp`). Needs a rerun when memory allows. Save and load of a spawned lord is not tested on purpose: it needs a save call (forbidden). |
| Spike S11 rerun | Not run. Probe `probe-lord-diplomacy` (lord_claim, lord_declare_peace, challenge lost) is written, not run. |
| 730 day soak | Not run. `soak-days` now has `HARNESS_SOAK_KEEP_APPROVAL=1` (writes Approval 100 each poll) so that the village may survive winter; not tried. At 7.9 game s per wall s one run needs about 61 min (`HARNESS_SOAK_WALL_S=3650`). |

Bug found and fixed: `Actions._command(name, **fields)` failed for `spawn_ai_lord` (field `name` clashed with the argument). The first parameter is now positional only.

## Update 2026-10-15 (issue #53, 730 day soak)

Run `s53-soak730-full3`: `soak-days` with `HARNESS_SOAK_WALL_S=12000` and `HARNESS_SOAK_KEEP_APPROVAL=1`. Verdict: fail (the asserts on days and clock rate). The game did not crash.

| Number | Value |
|---|---|
| Wall time | 12010 s (3.3 h) |
| Game days reached | 333 of 730 (13334 game s) |
| Clock rate | 1.11 game s per wall s on average (the earlier 61 min run had 2.53) |
| Crash | none; game alive at the end, 1 pop-up closed ("cold"), no stalled polls |
| Memory | start 4612 MB (read at once after the load), end 1603 MB, growth -3009 MB. A mid-run sample showed 4.7 GB falling to 1.6 GB in the first hour, then 1.6 to 1.8 GB with no growth trend |
| Approval | the keep-approval write read back 36 to 59 (not 100) at five polls: the game overwrites it between polls |

Findings:
- 730 days is not reachable in one run. The clock slows over time (2.53 in the first hour, 1.11 over 3.3 h), so the scenario needs about 8 h at this rate. The scenario cannot chain runs: each run loads the fixture again.
- No crash and no memory growth over 333 game days (about 23 times the game time of a normal run). This supports Q1 as a stability result. Q1 for the full 730 days stays open.
- The assert ranges were widened in the same change: clock rate 1.5 to 9 and days share 0.2 to 1.1. The 1.11 rate is still below 1.5, so the rate assert fails by design on this slow run. Do not lower it further: a rate that low means the sim slows down and needs a look (a likely cause is the growing village).
- `--env KEY=VALUE` of `run.py` goes to the game, not to the scenario. `HARNESS_SOAK_*` must be exported in the shell. The first try with `--env` ran the 600 s default.
- Limits raised: `MAX_SOAK_WALL_S` 13000 s and `MAX_LIMIT_S` 13500 s.
