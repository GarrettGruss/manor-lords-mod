## Context

The difficulty (1 to 3) lives in the invasion feature. It is picked once, by the F8 menu buttons or by `invasion_pick_difficulty`. The mod state (`openspec/specs/mod/mod_state/spec.md`) is stored in the save, so a value in it survives save and load.

## Decisions

- The spike decides between two sources of the value: (A) a game setting that the mod reads; (B) a mod option added to the new game menu.
- Prefer A when the game has a raider or bandit difficulty or frequency setting that Lua can read. Else use B.
- The mod copies the value into its mod state at the start of a new game. The save then holds it.
- The command that sets the difficulty is for tests and tuning. It has no "once" limit and works at any time. Its name is decided in the spike (keep `invasion_pick_difficulty` if it can be changed without breaking the test scenarios).

## Risks

- A mod option in the new game menu may need a widget change in a pak, or may not be possible from Lua.
- Reading struct values with soft object fields through the bridge crashes the game (CLAUDE.md, Safety). Read settings field by field.
- Saves only through the guarded `save_game` action.

## Open questions (owner)

See `tasks.md`, section 2.
