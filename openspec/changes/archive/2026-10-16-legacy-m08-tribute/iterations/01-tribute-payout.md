# M08 iteration 01: tribute-payout

Branch: `feat/M08-tribute-01-tribute-payout` (stacked on PR #196, M07.02). Issue: #197.

## Goal
At each season change the mod adds goods to the player stock for each handed-over vassal (M00 decision 21: a Lua rule, no transfer between regions). The amount is a share of the vassal production, 10 to 30 percent (M00).

## Design (TBD values are marked)
- Production proxy (TBD): `families x units_per_family` (20 per season). The vassal may be stalled (M07.02), so buildings are not used.
- Share (TBD): `share_min + (share_max - share_min) x loyalty / 100`: 10 percent at loyalty 0, 20 at 50, 30 at 100.
- Amount: `round(production x share)`, split equally over the tribute goods (`fish` 30, `timber` 16; M10 swaps in iron and salt). The remainder goes to the first good.
- Payment: `addToInventory` on a store that has room, read back (the proven route of the raid loot return). The first store that takes the full amount wins.
- Tick: once per season change, using the saved last season (the pattern of M04.02). No tick on the first poll. A vassal counts only after the handover (it has a lord).
- State: ModState keys `tribute_last_season`, `tribute_ticks`, `tribute_paid_total`.

## Changes
- New feature `tribute` (requires `vassals` and `raid_behavior` for the store functions): `rules.lua`, `init.lua`.
- `vassals` exports `region_families` (light read).
- Commands `tribute_state`, `tribute_tick_now` (forced tick).
- Config `tribute`.

## Acceptance criteria
- T1: one vassal with 5 families and loyalty 50: a season change adds 20 goods (10 fish, 10 timber) to the stock (read back from the stores), and `tribute_paid_total` is 20.
- T2: a season change with no handed-over vassal pays nothing.
- T3: exactly one payment for one season change; none while the season stays.
- T4: loyalty 100 pays 30, loyalty 0 pays 10 (5 families).
- T5: the store reads back the exact amount; a failed deposit is logged and counted (`failed_deposits`), not hidden.
- T6: no crash in the run.

## Scenarios
- `scenarios/tribute/tribute_payout.py` (`tribute-payout`): the claim, settle and handover of M07.02, then season jumps with `set_season`.

## Result
PASS in the real game (2026-10-18). Notes: `../implementation-notes/iteration-01-tribute-payout.md`.
- `tribute-payout` on a new game: runs `20261018-074439-b4da` and `20261018-074632-5609` pass (T1 to T6): 20 goods (10 fish, 10 timber) at loyalty 50, 30 at 100, 10 at 0; 0 with no vassal; one payment per season change; no failed deposit.
- Fake game tests: `harness/tests/test_fakegame_tribute.py` (7 tests).
- Deviation: goods are fish and timber for now; iron and salt come with M10.
