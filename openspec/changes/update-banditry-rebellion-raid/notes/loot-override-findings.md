# Loot override in the real game (tasks 2.5, 2.8, 2.9)

## Pit pay-out (task 2.5)
Test scenario `bandits-rebellion-loot`, fixture `base-corpse-pit` (10 armed families, one corpse pit). Steps: assign a pit worker, start a rebellion (6 families), kill 4 brigands that have an entry (`raid_behavior_test_kill_override_units`), run game days until a body is paid.
Results with the final scenario (worker assigned before the rebellion): pass `rb-loot-11`, `rb-loot-13`, `rb-loot-14`, fail `rb-loot-12`. Run `rb-loot-9` (no assignment) passed and `rb-loot-10` (assignment after the rebellion) failed:
- The override goods were 24 to 32 items (the goods of the 6 homes). The 4 killed entries were marked dead within a poll.
- A body reached the pit after 7 to 13 game days. Each time the pit corpse count rose by 1, one dead entry was paid (2 goods) and the pit gained exactly those goods (`pit_gain_weapon_goods` 2 = `paid_goods` 2).
- **The delivery is random.** In `rb-loot-12` and `rb-loot-10` no body reached the pit in 14 game days. The pit worker may be among the 6 families that left (60 percent), so the test can fail without a bug. 3 of 4 runs with the final scenario passed.
- **Crash:** adding families with `family_add` and then `building_assign_worker` crashed the game in three runs (`rb-loot-6`, `-7`, `-8`: EXCEPTION_ACCESS_VIOLATION reading 0x3c1, 3 game days after the assignment), also with visible bodies (`hide_bodies` false). The same scenario without these two actions did not crash. Not studied further: it is a harness action, not the mod. The test does not use `family_add`.
- The pit cannot tell whose body arrives (only the corpse count rises). The mod pays the oldest dead entry for each new body. In the runs the bodies were probably bodies of the removed families (hidden), so the entry of a killed brigand was paid by another body. This is listed as a spec change.
- A kill with the harness action `kill_units side=bandit` hit native bandit units, not the rebels (run `rb-loot-1`), so the test uses the mod command that kills the units of the entries.

## Stable unit key (task 2.8) and the round trip (task 2.9)
Test scenario `bandits-rebellion-loot-roundtrip` (fixture `playtest-noai`). Write run `rb-rt-w1`: rebellion with 4 families, 15 entries (squad 20, unit index 1 to 15, goods 133 and 271), save with `save_game(keep=True)` as `saveGame_57`. Read runs `rb-rt-r1`, `rb-rt-r2`, `rb-rt-r3`: after the load 15 of 15 entries are linked to 15 living units (relink done in 1 poll, 0 lost); the squad id is the same as before (20); a killed linked unit gets its entry marked dead. The key squad id plus unit index with the relink by position works. A body keeps its entry over a load was not tested ("A unit with an entry dies" scenario stays "Not checked yet").
The saved slot is removed by hand at the end (`saveGame_57*`).

## Not verified
- Plunder next to an override (`ItemsLooted` of a brigand with an entry): the code does not change it, no real check.
- A body with an entry over a save and a load.
