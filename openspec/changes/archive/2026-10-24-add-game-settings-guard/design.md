## Context

The game setup values are not in the save (archived change `spike-new-game-difficulty-setting`, `notes/game-settings.md`). `mod/shared/HarnessGameSetup` reads `MLGameInstance.gameSetup.currentGameSetup`, for example `numGenericAILords`.

## Decisions

- Read once at new game start. Save one mod setting in ModState: `vassals` (bool, false when `numGenericAILords` is 0). Reason: the game values are lost after a save and load. The menu warning reads this setting.
- After a load, use the stored result. Old saves: live check (AI lord pawns). A live check can only prove "off" when no such pawn exists.
- No lock and no command refusal. The only output is the menu warning "vassals are not enabled".
- No start banner (owner decision 2026-10-23): the warning shows only in the mod start menu.
- No Hussite lock and no `hussites_enabled` setting (owner decision 2026-10-24). Spike #430 showed that Hussite raids work with Off Map Adversary absent. No other requirement needs the setting, so it is not kept as information.
- Bandit camps 0 locks nothing: the mod makes the bandit pawn itself (change `update-banditry-bandit-camp`).

## Risks

- A live check can be wrong early in a game (lords not spawned yet). Run it after the intro.
- The guard is very small now. See the proposal.
