# Value survives save and load (task 1.3, issue #358)

## Result
Yes, through the mod state. No new save was made in this spike. The existing proof is enough.

## Evidence
- `openspec/specs/mod/mod_state/spec.md`: values live in the `Tags` of the player pawn (`invasion:<key>=<value>`), which the game saves and loads.
  - Round trip: `mod/InvasionMod/scenarios/mod_state/roundtrip.py` (write phase with the guarded `save_game`, read phase in a new run).
  - Two saves keep separate values: `two_saves.py`. A save with no entries gives defaults: `default_load.py`.
- The game setup values are not in the save (`game-settings.md`). So the mod must copy the setup value into its mod state when a new game starts, and read only the mod state after that.
- The mod state needs the player pawn. At the start of a new game, copy after the pawn exists (the intro cinematic runs first).
- `difficulty` is already a registered mod state key (`state:register("difficulty", config.difficulty, "integer")` in the invasion feature), so it already survives a save.

## Not verified
- A new round trip with the new flow (copy at new game start). It needs a `save_game` run in the implementation change.
