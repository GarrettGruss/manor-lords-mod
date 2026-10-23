# A named command that sets the difficulty at any time (task 1.4, issue #358)

## Result
The command `InvasionMod.invasion_set_difficulty` (value 1 to 3) already exists and has no "once" limit. Run `spike358-2` (test scenario `probe-difficulty-setting`, verdict pass) proves it.

## Numbers
- Set 3, 1, 2 in a row before any pick: each read back (planned `squads` 6, 2, 4).
- After `invasion_pick_difficulty` (value 3): a second pick is refused ("the difficulty was picked already"). `invasion_set_difficulty` 1 still worked.
- After `invasion_force_next` and the raid spawned: `invasion_set_difficulty` 3 worked. `replan_size` returns at once when a raid is spawned, so the squads of that raid do not change. Waves and relief of the great raid read the difficulty live.

## Limits of `invasion_pick_difficulty` (`invasion/init.lua`, `pick_difficulty`)
- Refused when `difficulty_chosen == 1` (once).
- Refused when `raids_spawned > 0`.
- Value 1 to 3.
- Sets `difficulty_chosen = 1`. `invasion_set_difficulty` does not set it. The raid menu prompt and the three buttons (`raid_info.picks_allowed`) use that flag.

## For the change
- Keep `invasion_set_difficulty` as the "tune at any time" command. No new name is needed. Let it also set `difficulty_chosen = 1`, so the prompt stays off. A raid that already spawned keeps its squads.
- `invasion_pick_difficulty` and its test scenario `difficulty_pick.py` (checks D1 and D2, "a second pick is refused") go when the buttons go.
