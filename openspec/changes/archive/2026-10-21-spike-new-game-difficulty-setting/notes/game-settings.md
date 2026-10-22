# Game new game settings (task 1.1, issue #358)

## Result
The game has raider settings in its Game Setup screen. Lua can read them in a loaded game and in a started new game. Proven in the real game.

## What exists
- Screen: `mainMenu_GameSetup_C` (`/Game/UI/Game_Setup/`), a child of the main menu widget. Its rows are `W_Menu_GameSetupSettingEntry_C` widgets: `entry_raidFrequency`, `entry_untilFirstRaid`, `entry_bandit_initial`, `entry_bandit_max`, `entry_aggressiveness`, `entry_ai`, `entry_baron`, `entry_goals` and more. Picture: `evidence/menu-setup.jpg`.
- In the UI: "Template Difficulty" (Relaxing, Default, Challenging), "Raider Frequency" (Medium, Frequent, ...), "Raider Free Years" (2), "Initial Bandit Camps" (1), "Random Bandit Camp spawn limit" (3).
- Data: `MLGameInstance.gameSetup` (`GameSetupPreset`) holds `currentGameSetup` (`GameSetupParameters`). `MLGameInstance.gameSetupDifficulty` is an `EGameDifficulty` (0 Custom, 1 VeryLow, 2 Low, 3 Medium, 4 High, 5 VeryHigh). Fields of `GameSetupParameters` (jmap): `raidingFrequency`, `yearsUntilFirstRaid`, `maxBanditCamps`, `initialBanditCamps`, `AI_aggressiveness` (all Byte), `adversary_baron`, `goals`, `numGenericAILords` and economy fields.
- Presets: `DT_GameSetupPresets` (rows such as `baron`, `peaceful_citybuilding`, `survival`, `fractured_realm`, `duel`, `burned`), each with a difficulty.

## Read in a loaded game
Run `spike358-2` (fixture `base`, test scenario `probe-difficulty-setting`; the command `game_setup_state` of `HarnessGameSetup` was extended): `raiding_frequency=1` (Medium), `years_until_first_raid=2`, `initial_bandit_camps=1`, `max_bandit_camps=3`, `ai_aggressiveness=1`, `adversary_baron=false`, `difficulty=3` (Medium). The values equal the Game Setup defaults on screen. A write of `yearsUntilFirstRaid` from 2 to 3 read back as 3 (new command `game_setup_set_byte`).
Read field by field in Lua (`instance.gameSetup.currentGameSetup.<field>`). Never read `gameSetup` as a whole through the bridge: `GameSetupPreset` holds a soft object (`Thumbnail`).

## Does the game save them?
- The values are NOT in the save. The `base` fixture (`MLSaveGame`, readable GVAS) has no name with raid, bandit, difficult, aggress, goal or setup (only `SetupIndex`). So a loaded game shows the setup that the game process holds (the default or the last menu choice), not the setup of the save.
- Whether the native raid code uses `raidingFrequency` after a write in a running game is not tested.

## Not verified
- The meaning of each Byte value except Medium = 1 and Frequent = 2 for `raidingFrequency`.
- Whether Raider Frequency is the right meaning for "raid difficulty" of the mod. It is a game setting for native bandit raids. The owner decides.
