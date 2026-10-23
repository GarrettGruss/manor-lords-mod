# Real game runs of pit_loot

- Run 20261023-030456-4f99: killed by the shell timeout. The scenario waited with run_until while the game was paused, so no body ever reached the pit. Fixed: the scenario runs game days.
- Run 20261023-031719-9078 (fail): `unpaid` stayed 0. Bug in the mod: `rules.note_deaths` was never called in `step_raid`, so no body was ever counted. Fixed in `raid_behavior/init.lua`.
- Run 20261023-032125-a80d (pass): Hussite raid of 18, record 18 of good 15 after 3 days, 9 raiders killed, 9 deaths noted, after some game days 1 body paid and the pit gained 1 share (floor(18/18) = 1) of good 15. Only the first delivered body is waited for.
