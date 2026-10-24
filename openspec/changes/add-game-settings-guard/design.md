## Context

The game setup values are not in the save (archived change `spike-new-game-difficulty-setting`, `notes/game-settings.md`). `mod/shared/HarnessGameSetup` reads `MLGameInstance.gameSetup.currentGameSetup`: `initialBanditCamps`, `maxBanditCamps`, `numGenericAILords`, `adversary_baron` and others.

## Decisions

- Read at new game start, before the menu opens. Store a table `{bandit_camps_off, ai_lords_off, off_map_off}` in ModState. Reason: the values are lost after a save and load.
- After a load, use the stored result. Old saves: live check (bandit pawn from `HarnessBattle`, `isBandit = true`; AI lord pawns). A live check can only prove "off" when no such pawn exists.
- One table maps a game part to the mod settings it locks and to its warning text. The menu and the commands read this table.
- Lock in two places: the menu (row disabled, value 0, warning text) and the command (refuses a value above 0).
- Only locks that the spike confirms are active. The off-map adversary starts as warn only.

## Risks

- The field name for the off-map adversary may differ from `adversary_baron`. The spike decides.
- A live check can be wrong early in a game (lords not spawned yet). Run it after the intro.
