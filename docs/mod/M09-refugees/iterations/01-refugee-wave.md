# M09 iteration 01: refugee-wave

Branch: `feat/M09-refugees-01-refugee-wave` (stacked on PR #199, M08.01). Issue: #200.

## Goal
A lost vassal sends 30 to 60 percent of its population as refugees to the home region (M00). They wait in the game homeless tent (building type 87). They lower approval and eat food natively (spec 15 notes). This iteration sends the wave. Iteration 02 ends it (housed or turned into bandits).

## Design (TBD values are marked)
- Trigger: the function `send_wave(families)` of the feature, and the command `refugees_vassal_lost{slot}` (test and for M07.04, which calls the function when a vassal is lost). The vassal population is the family count of its region.
- Share: random between 30 and 60 percent per wave (config `share_min`, `share_max`), or a fixed value from the command.
- Wave families = `ceil(families x share)`, at least 1.
- Arrival: `settleRegion` on the home region adds 5 families per call (spec 15: `immigration-surge.md`). TBD deviation: calls = round(wave families / 5), at least 1, at most 3, so the real wave comes in steps of 5 families. Free home slots take the first families; the rest are homeless in the tent.
- Camp: the woods first, then near the village (the old RefugeeWaves mod route).
- State (ModState): `refugee_active`, `refugee_start_day` (day + 1), `refugee_base_homeless`, `refugee_wave_families`, `refugee_waves`.
- Banner: "Refugees have arrived".

## Changes
- New feature `refugees` (requires `vassals`): `rules.lua`, `world.lua`, `init.lua`.
- Commands `refugees_state`, `refugees_vassal_lost` (slot, optional share in percent), `refugees_send_wave` (families, optional share in percent).
- Config `refugees`.

## Acceptance criteria
- R1: a wave from a vassal of 5 families at 30 percent (2 families wanted): one settle call, families of home +5, no error.
- R2: the wave is active (`refugee_active`) with `refugee_base_homeless` set to the homeless count before the wave.
- R3: if free home slots are fewer than 5, homeless rises by at least 1 (a tent camp).
- R4: approval of the home region falls by at least 3 within 4 game days while the homeless stay (spec 15: 71 to 59 in 5 days).
- R5: a second wave is refused while one is active.
- R6: the share is within 30 to 60 percent for the random case (fake game, 200 draws).
- R7: no crash in 4 game days at speed 2.

## Scenarios
- `scenarios/refugees/refugee_wave.py` (`refugees-wave`).

## Result
Not started.
