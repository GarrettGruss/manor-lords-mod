## Context

The game setup values are not in the save (archived change `spike-new-game-difficulty-setting`, `notes/game-settings.md`). `mod/shared/HarnessGameSetup` reads `MLGameInstance.gameSetup.currentGameSetup`: `initialBanditCamps`, `maxBanditCamps`, `numGenericAILords`, `adversary_baron` and others.

## Decisions

- Read once at new game start. Save three mod settings in ModState: `vassals` (bool, false when `numGenericAILords` is 0), `villager_banditry` (bool), `hussites_enabled` (bool, from the off-map adversary field; mapping to confirm in the real game). Reason: the game values are lost after a save and load. Menu rows and warnings read these settings.
- After a load, use the stored result. Old saves: live check (bandit pawn from `HarnessBattle`, `isBandit = true`; AI lord pawns). A live check can only prove "off" when no such pawn exists.
- One table maps a game part to the mod settings it locks and to its warning text. The menu and the commands read this table.
- Lock in two places: the menu (row disabled, value 0, warning text) and the command (refuses a value above 0).
- No start banner (owner decision 2026-10-23): warnings show only in the mod start menu.
- Off-map adversary absent locks all three levels (vassal raids are Hussite raids in the code). Bandit camps off disables the banditry timer and leave. AI opponents 0 warns only.

## Risks

- The field name for the off-map adversary may differ from `adversary_baron`. The spike decides.
- A live check can be wrong early in a game (lords not spawned yet). Run it after the intro.
