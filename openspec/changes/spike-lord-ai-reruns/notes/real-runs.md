# Real runs

## 1.1 Suite `lord-village-ab` (2026-10-18)

Run: `suite-20261018-232048-f23d`. 9 runs, 9 pass, 0 flaky. 1885 s of the 3600 s budget.

| Variant | Runs | buildings start / end | families end | build_lines |
|---|---|---|---|---|
| supply-0 (reference) | 3 | 5 / 5 | 5 | 0 |
| supply-2 | 3 | 5 / 5 | 5 | 0 |
| type-2-supply-2 | 3 | 5 / 5 | 5 | 0 |

Result: the AI lord village does not grow in 30 game days in any variant. More supply and a different lord type change nothing (all metrics "same"). No build line is logged.

## 1.2 Probe `probe-lord-diplomacy` (2026-10-19)

Run: `20261019-223202-8611`, pass. Details in `baron-diplomacy.md`.

## 1.3 Suite `battlefield-anchor-ab` (2026-10-19)

Run: `suite-20261019-223458-b96c`. 6 runs (3 per side), 6 pass, 0 flaky. 552 s of the 3600 s budget.

| Metric | control (median) | anchor (median) | Verdict |
|---|---|---|---|
| center_dist (battlefield center to the manor) | 46853 | 760 | different, expectation "lower by at least 0.5" MET |
| anchor_arm | 0 | 1 | different |
| army_dist_1 | 15721 | 7406 | inconclusive (n=1 each) |
| fields_restored | 1 | 1 | same |

Result: with the anchor on, the battlefield center of a raid challenge is about 760 units from the manor, against about 46850 without it. Fields are restored in both variants.

## 1.4 Game-time `ctx.run_until` (2026-10-20)

Scenario `sack-ruins` (uses `clock="game"`). Run: `20261020-064143-b5d6`, verdict fail, but not because of `run_until`.
- `run_until(..., clock="game")` worked in the real game: the fires burned out after 39.5 game seconds in 4.9 wall seconds (3 polls, 0 stalls) at speed 3.
- No new rule is needed. `harness/tests/test_runlib_waiting.py` passes (19 tests).
- The scenario failed on game state, not on waiting: the action `sack_buildings` read-back was `0 -> 0` (FAILED), and no building became rubble (0 instead of 2), although 2 buildings burned and the fires ended. This is a separate finding for the `sack-ruins` scenario or the `sack_buildings` action (not part of this change).

## 2.2 Wiki and changelog

No wiki page describes lord AI behavior, and no command changed, so no wiki or `CHANGELOG.md` change is needed. Fact for the mod features: an AI lord village did not grow in 30 game days in 3 variants (1.1).
