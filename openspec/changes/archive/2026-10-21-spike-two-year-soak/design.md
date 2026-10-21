# Design: Spike two year soak

## Open questions
| Question | Who decides | How it is answered |
|---|---|---|
| Is a 333 day run enough proof for Q1, or is the full 730 days needed? | The user | The user reads the numbers in `notes/` and decides. |
| Why does the clock rate fall from 2.53 to 1.11? | A spike | Task 1.2: sample unit count, building count and tick time during a long run. |
| Does the soak need a periodic raid? | The user | If yes, use the raid stand-in or the base game raid timer (spec 10 spike S1). |
| Can the village survive winter without writing Approval each poll? The game overwrites the value. | A spike | Task 1.3 |

## Owner decisions (chat, 2026-10-20)
1. The clock rate check of `soak-days` is removed. The rate is a performance number, not a stability result. The scenario records `running_rate` and `overall_rate` as metrics. They do not fail the run.
2. Criterion Q1 is verified at 401 game days. Run `s286-soak-3` reached 401 game days (day 205 to 606) in 13254 s, with no crash and flat memory (1738 MB at the end). Run `s286-soak-2` reached 333 days clean. Run `s286-soak-1` crashed at day 272 in the raid sack step (#327, fixed in #328). A full 730 days does not fit in one run (`MAX_LIMIT_S` 13500 s, clock rate about 1.1 to 1.2), so the 2-year run is still extrapolated.
