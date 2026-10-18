# M09 iteration 02: housing-and-timeout

Branch: `feat/M09-refugees-02-housing-and-timeout` (stacked on PR #201, M09.01). Issue: #202.

## Goal
A refugee wave ends in one of two ways. The player houses the refugees and the wave ends `housed` (they are villagers now). Or the refugees stay without a home for the timeout (1 to 2 game months, M00) and the unhoused families turn into bandits (the M04 `homeless_rebel` route).

## Design (TBD values are marked)
- Poll every 4 s while a wave is active. Unhoused = homeless families now minus the homeless base saved at the wave start.
- Unhoused 0 or less: outcome `housed`.
- Wave age (game days) at or above `timeout_days` (45, TBD): the unhoused families (at most 6) leave through `bandits.world.rebel` (2 families a squad). Outcome `rebelled`. If the rebellion call fails, the wave stays active and the error is logged (retry at the next poll).
- State (ModState): `refugee_last_outcome`, `refugee_housed`, `refugee_rebelled`, `refugee_bandit_families`.
- Approval and food are native effects (spec 15 notes).

## Changes
- `refugees/init.lua`: poll, `check_wave`, `finish`, `rebel`. `rules.timed_out`. Config `timeout_days`, `poll_ms`, `max_rebel_families`, `families_per_squad`.
- Command `refugees_set_timeout{days}` (test).

## Acceptance criteria
- H1: a wave starts with homeless families above the base.
- H2: the wave stays active while the refugees are homeless.
- H3: after 5 burgage plots are built (no mouse), the wave ends `housed` within 24 game days, no homeless wave families are left, no family turned to bandits.
- H4, H5: a second wave with a 3 day timeout ends `rebelled`; the converted families are between 1 and the unhoused count; bandit units appear; the home region lost those families.
- H6: no crash.

## Scenarios
- `scenarios/refugees/housing_and_timeout.py` (`refugees-housing-and-timeout`), fixture base, speed 2.

## Result
PASS in the real game (2026-10-18). Notes: `../implementation-notes/iteration-02-housing-and-timeout.md`.
- `refugees-housing-and-timeout`: runs `20261018-082015-6e7a` and `20261018-082648-e446` pass. Phase 1 housed in 16 game days (approval 71 -> 66 after housing), phase 2: 5 unhoused families became bandits after the 3 day timeout, bandit units appeared, home families 20 -> 15.
- Fake game tests: 7 new tests in `harness/tests/test_fakegame_refugees.py`.
- Two crashes before the pass: runs `20261018-081339-1665` (speed 3, access violation in the Lua tick) and `20261018-081831-22dd` (speed 2, null read in an `AActor` call right after the wave). The poll then read the regions with `:get()` unwrap every 2 s; it now indexes directly and polls every 4 s. Cause not proved.
