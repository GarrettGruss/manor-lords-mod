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

## Spike result and recommendation (issue #358, notes in `notes/`)

- The game has raider settings in the Game Setup screen (Raider Frequency, Raider Free Years, bandit camps, template difficulty). Lua reads them in a loaded and in a started game (`notes/game-settings.md`). A value chosen on the screen is in `MLGameInstance.gameSetup` after the game starts (`notes/new-game-menu.md`).
- The game does not save these values. The mod must copy the value into its mod state at new game start. The mod state survives save and load (`notes/save-load.md`).
- `invasion_set_difficulty` already works at any time (`notes/set-command.md`).
- Recommendation: source A. Read Raider Frequency (Medium = 1, Frequent = 2, other values not mapped yet) at new game start, map it to difficulty 1 to 3, store it in the mod state. No widget and no pak. Option B (own widget) works only as a placeholder so far and has more risk. Owner questions: is Raider Frequency the right meaning for the mod difficulty, and how are its values mapped to 1 to 3?

## Open questions (owner)

See `tasks.md`, section 2.
