# Spike A: the arrival days of spawnArmy

Question: does `spawnArmy(position, templates, owner, company, days)` with days 1 to 3 bring the army in from off the map after N days?

Method: probe `probe-border-arrival` (`mod/InvasionMod/scenarios/invasion/probe_border_arrival.py`). One AI lord at war with the player. One squad each for days 0, 1, 2 and 3, all at the same position (player pawn, dy -50000). Squad positions read every 10 game seconds with `lords_state`.

Runs:

- `20261028-015007-a040`: INVALID. The command parser of HarnessActions did not read the field `days`, so every call used 0. Fixed in `mod/HarnessActions/Scripts/main.lua` (a pattern for `days`). `lord_spawn_army` now takes `days`.
- `20261028-023053-69cf`: valid run. The parser sends `days`.

Result (run `20261028-023053-69cf`):

- All four squads (days 0, 1, 2, 3) had 32 living units 10 game seconds after the call, at the same place (about y -93500, near the given position y -103320).
- All four started to walk at once. No squad was delayed. The squad ids come back at once for every value.
- Verdict: the arrival days argument is ignored for a lord army. Spike A fails. The mod does not use it.
- The game call does honor the position argument: an army starts where it is told, also outside the playable square (spike B).

Not verified: the days argument with another owner (the player pawn, a bandit pawn) or with a company id other than 0. The native raiders use the game's own code path, not this call.

Harness change from this spike: `HarnessLords.lord_spawn_army` takes `days` (0 to 10) and an optional absolute point `x`, `y` (within 250000).

Note on the run result: the teardown of run `20261028-023053-69cf` reported `harness_error` because the fixture slot `saveGame_59` of another agent was removed during the run. It is not a change of the real saves of the user.
