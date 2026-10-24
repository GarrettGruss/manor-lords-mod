# Menu widgets and data source (tasks 1.2 and 1.3)

Real game runs (hold runs, fixture `base`, then `open /Game/NotStronghold/Maps/MainMenu` and `mainMenu_widget_C:GoToGameSetup`): `menu-h-185800`, `menu-p-190638`, `menu-s-191029`, `menu-q-191928`. Assets read with `pakmod.py extract` and `tojson` (work folder only). Picture: `evidence/m1-setup-screen.jpg`.

## The screen

- Widget `mainMenu_GameSetup_C` (`/Game/UI/Game_Setup/mainMenu_GameSetup`).
- **Templates:** `ModePresets` (a `HorizontalBox`) holds one `mainMenu_GameSetupPresetButton_C` for each row of the data table `DT_GameSetupPresets`. The function `repopulateGamePresets` makes them from `GetDataTableRowNames`. The table has 5 rows: `peaceful_citybuilding`, `baron`, `survival`, `duel`, `fractured_realm`. Each button has `presetRowName` (Name), `setupPreset` (a `GameSetupPreset` struct with a soft object `Thumbnail`: never read it) and the delegate `gamePresetSelected`.
- **Row of the table (`GameSetupPreset`):** `Thumbnail` (soft object), `isMainGameMode`, `customTags` (array), `mapOverride` (Name), `gameSetupData` (a map by difficulty) and `currentGameSetup` (`GameSetupParameters`: goals, `numGenericAILords`, `adversary_baron`, `AI_aggressiveness`, `maxBanditCamps`, `initialBanditCamps`, `raidingFrequency`, `yearsUntilFirstRaid`, supplies, spoilage, weather and more).
- **Difficulty banners:** `HorizontalRadioSelect_Difficulty` (class `HorizontalRadioSelect_C`), enum `EGameDifficulty`.
- **Settings rows:** the parent of `entry_untilFirstRaid` is a **`GridPanel`** with 21 children: 18 `W_Menu_GameSetupSettingEntry_C` (`entry_goals`, `entry_ai`, `entry_baron`, `entry_aggressiveness`, `entry_raidFrequency`, `entry_untilFirstRaid`, `entry_bandit_initial`, `entry_bandit_max`, `entry_startseason`, `entry_startsupplies`, `entry_tax`, `entry_armament`, `entry_resources` (collapsed by the game), `entry_discontent`, `entry_spoilage`, `entry_approval`, `entry_water`, `entry_weather`), 2 `Spacer` and the image `SettingHoveredHiglight`. The grid is inside `SettingsScrollBox`. A row has a grid slot with `Row` and `Column` (raid frequency: row 5, column 1).
- **A row widget:** native base class `MLGameSetupSettingWidget` (property `Spinner`, `params` struct, `SetSettingValue`, `GetSettingValue`). The blueprint adds `Icon`, `Text` (class `MLTextBlock`), `HB`, `OnSettingChanged`. The `Spinner` is a `W_MenuSpinner_C` over the plugin class `/Script/AutoSettings.Spinner`: `Options` (array of `SettingOption` with `Label` Text and `Value` String), `UpdateOptions(InOptions, bPreserveValue)`, `SelectIndex`, `SelectValue`, `Next`, `Previous`, `GetCurrentIndex`, `GetCurrentOption`, `SelectionChangedEvent`.
- **Data source:** `MLGameInstance.gameSetup` (`GameSetupPreset`) with `currentGameSetup`, `gameSetupDifficulty` (enum), `scenario` (Name, reads `None`), `startingSetup` and the delegates `OnGameSetupChanged` and `OnGameSetupParamsChanged`. Read it field by field.
- **Screen functions of interest:** `repopulateGamePresets`, `UpdateAll`, `UpdateGameSetupFromSetting(Widget, OldParams)`, `SetOptionAvailable(Widget, isAvailable)`, `NotifySettingsChanged_BP`, `getCurrentGameSetup`, `Open`, `Close`.

## What a click on a template does (real mouse; the mouse was present on 2026-10-23)

Run `menu-q-191928` (pak with a 6th row, see `template-add.md`). Instance before: AI lords 3, adversary_baron false, difficulty 0. After one real left click on the 6th template button: AI lords 0, adversary_baron true, difficulty 3 (Medium), and the screen showed End Goal Domination, AI Opponents 0, Off Map Adversary Present, "Default" difficulty highlighted (picture `evidence/m6-click-sixth-template.jpg`). So **a template click writes the preset into `MLGameInstance.gameSetup` at once.** (The new row was a clone of `baron`.) Earlier work (#358) saw the instance change only at "Continue" after a click on a settings arrow. That was not re-tested.

## Not verified

What `Continue` does with `scenario`; `scenario` stayed `None` after the template click.
