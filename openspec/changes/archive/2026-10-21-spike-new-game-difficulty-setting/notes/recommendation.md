# Recommendation (spike-new-game-difficulty-setting)

Findings (notes in this folder):
- The Game Setup values live in `MLGameInstance.gameSetup.currentGameSetup` (`raidingFrequency`, `yearsUntilFirstRaid`, `maxBanditCamps`, `initialBanditCamps`). Lua can read them. The game does not save them.
- A cloned stock option widget showed only the text "label"; the stock entry writes only game properties.
- Visiting the Game Setup screen changed the real `menu.sav` (restored from the backup).
- The first `disable_autosave` after a menu-started new game was undone by the game; a second call after the intro worked.
- `invasion_set_difficulty` works at any time.

Owner decision (2026-10-21): do not use or change the game's setup menus and do not read Raider Frequency. The mod opens its own scenario settings menu at the start of a new game. That work is the change `add-scenario-settings-menu` (#375); this spike's delta specs were removed (`skip_specs: true`) and its build tasks are moot.
