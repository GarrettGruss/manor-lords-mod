# Pause cause (task 1.1)

Method: HarnessBoot has a new env switch `HARNESS_BOOT_NO_PAUSE=1`. It skips the PAUSING step and writes `ready.marker` (`paused: false`) at once, so the game runs as in a player launch. Test scenario `scenario-settings-player-launch-pause` (`run.py --new-game --pak raidmenu --env HARNESS_BOOT_NO_PAUSE=1`) samples the clock, the speed and the menu state.

## Findings

- Run 20261023-224121-a094 (first probe, no key): the intro ran at speed 1 for about 4 s. When `currentUIMode` went to 0, the menu opened and paused at once (speed 0, clock 5.084). The clock stood still for 30 s. So the intro cinematic end alone does NOT un-pause the menu in this setup.
- Run 20261023-224512-647a (bug, before the fix): the scenario pressed Space and 2 while the menu was open. The game ran at speed 1 and the clock moved 3.4 s in 3 s (assert P4 failed). The mod did nothing: `paused_by_menu` stayed true. The menu does not take the keyboard, so the player's speed keys un-pause the game behind the menu. This is the proved cause of the pause loss, and the most likely cause of the owner's Steam launch.
- Not reproduced: a delayed speed restore by the game after the cinematic. If the game does it, the same guard re-pauses.

## Fix

While the menu is open the mod looks at the game clock on each tick (100 ms). If the clock moved by `pause_guard_epsilon` (0.01), it calls `pauseGame` again and logs a warning. The first look after a pause only sets the reference. The guard stops when the menu closes.

Run 20261023-232209-eb8a (after the fix): P1 to P4 pass. The mod log shows one warning "the game clock moved while the menu is open (5.101 -> 5.201); pausing again (1)". The clock moved only 0.1 s before the re-pause.
