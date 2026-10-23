## Context

The owner chose a mod-owned menu over the game's Game Setup screen (2026-10-21). The spike `spike-new-game-difficulty-setting` (#358, branch `origin/feat/spike-new-game-difficulty-setting`, `notes/`) gave these facts:
- The Game Setup screen has Raider Frequency and Raider Free Years. The game does not save them. The mod does not use them.
- A cloned stock entry widget showed only the text "label". The stock entry writes only game properties.
- Visiting the Game Setup screen changed the real `menu.sav`. The mod menu avoids this.
- The first `disable_autosave` right after a menu-started new game was undone by the game. A second call after the intro worked.
- `invasion_set_difficulty` works at any time. `difficulty` is already a mod state key.
- A new game is told from a load by `MLGameInstance.savefileToLoad` (empty on a new game). Not re-tested.

## Decisions

### The menu
- A new feature `scenario_settings` in `mod/InvasionMod/Scripts/features/scenario_settings/`. It uses the menu framework of #308 (`core/menu.lua`), and the click hooks and PNG loading of the raid menu of #340 and decision #333.
- Rows: a background text block, four choice rows (left and right arrows or one button per choice), two buttons. The look follows the mockup. Images are PNG files loaded at run time.
- The background text and the labels are in the feature `config.lua` (`background_text`). The owner writes the text. Until then a short placeholder text stays in config.
- "Begin the game" closes the menu, writes the settings to the mod state, and un-pauses the game. The game is paused while the menu is open (the pause method is a task-1 check).

### New game or loaded save
- After the player pawn exists, the feature reads `MLGameInstance.savefileToLoad` and the mod state key `settings_applied` (integer, default 0).
- New game: `savefileToLoad` is empty and `settings_applied` is 0. Open the menu.
- Otherwise: do not open the menu. Apply the stored settings (they are read live from the mod state) and, for an old save without entries, use defaults and set `settings_applied` to 1.
- The decision runs once per game session. A second map load in one session does not re-open the menu.
- Open question (task 1.1): is `savefileToLoad` reliable after a "Continue" from the main menu? If not, use only `settings_applied` plus the intro state.

### Settings and existing config
| Setting | Mod state key | Existing mod option |
|---|---|---|
| Difficulty | `difficulty`, `difficulty_chosen` | exists (`invasion.difficulty`) |
| First Hussite raid | `first_raid_years` (new, 1 to 3, default 2) | NEW: the first year of the season roll (`update-raid-clock-yearly`) |
| Raid size | `size_class_fixed` (new, 0 random, 1 to 3) | the size class exists (`size_class`, `size_multipliers`); a fixed class is new |
| Great raids | `great_raids` (new, 0 or 1, default 1) | NEW: the clock always runs today |

- First raid year: the season roll of `update-raid-clock-yearly` starts in year `first_raid_years + 1` instead of year 2. The roll, its chances and the raid day inside the season are unchanged. No spread of its own.
- Great raids Off: the daily step does not start the clock when `great_raids` is 0. If the value changes to Off later by command, a running clock stops and the phase stays `none`.
- All new keys are registered in the mod state with a type (`mod/mod_state`).
- Defaults live in `config.lua`: difficulty 2, 2 years, Medium (class 2), On.

### Commands for tests
- `scenario_settings_skip`: close the menu, apply defaults, un-pause.
- `scenario_settings_set`: set one or more settings by name (reuses the request fields `field` and `value`, as `HarnessActions` reads a fixed field list), then apply and close.
- `scenario_settings_open`: open the menu (for the menu test scenario).
- `scenario_settings_state`: return the four values and `settings_applied`.
- Test scenarios that do not test the menu call `scenario_settings_skip` or `_set` first. The fixture loads (loaded saves) never open the menu, so most existing test scenarios are unchanged.

### Autosave
The feature re-sends `disable_autosave` after the intro and after "Begin the game" (spike finding). It never calls a save function.

### Picture evidence
`mod/InvasionMod/scenarios/scenario_settings/new_game_menu.py` takes `ctx.screenshot` of: the menu at the defaults, the menu after changes, and the game after Begin (menu gone). Pictures go to `evidence/` (at most 1280x720) with `evidence/README.md`. They are compared with the mockup by the owner.

### Not in this change
- The F8 raid menu loses its difficulty buttons (owner, 2026-10-21). `invasion_pick_difficulty` stays as a command for tests.

## Risks
- A new game started from the main menu needs a real run through the main menu. The harness fixture normally loads a save. Task 1.1 finds a way to run a real new game once.
- Pausing and un-pausing may differ from the game's own pause (input, time). Checked in task 1.1.

## Open questions
- Owner: the background text.
- Spike (task 1.1): how a new game is detected after the main menu, and the pause method.
- Task 1.2: the length of a game year in game days.

## Findings from the implementation (2026-10-22)

Details in `notes/new-game-detection.md`, `notes/season-roll.md` and `notes/art.md`. These change or add to the decisions above:
- New game or loaded save: `savefileToLoad` is empty on a harness new game and the slot name after a harness load, so the rule works. The game day (`new_game_max_day`, 10) is an extra guard for a lost file name.
- Hold gate: the invasion feature asks `scenario_settings` before each daily step. While a new game waits for the menu, the invasion feature shows no "Pick the difficulty" banner and starts no clock.
- Un-pause: `unPauseGame` alone does not run a new game (game speed stays 0). "Begin the game" calls `unPauseGame` and then `changeGameSpeed(begin_speed, false)` (`begin_speed` 1).
- Registered mod state defaults keep the old behaviour (`first_raid_years` 1 = year 2, `size_class_fixed` 0 = random, `great_raids` 1). The config defaults (Normal, 2 years, Medium, On) are written by the menu, by `scenario_settings_skip` and for an old save. An old save does not count as a difficulty pick, so `invasion_pick_difficulty` still works once on it (test scenario `invasion-difficulty-pick` passes).
- The base menu has a new optional field `bar = false`: the settings menu has no bottom bar button.
- The Close button of the base menu closes the settings menu like "Begin the game" (the choices apply, the game runs).
- Extra test command `scenario_settings_click` (action `choose`, `defaults`, `begin`): the same code as a click button. A real mouse click is not tested in this change.
- The three difficulty buttons are removed in Lua only (no click button is attached). The pak widget `WBP_RaidMenu` keeps three empty, transparent Borders, so `raidmenu_P.pak` needs no rebuild for this part.
- Pak: `WBP_ScenarioSettings` is in `raidmenu_P.pak` (editor script `ue/make_scenario_settings_widget.py`). The PNG art of the mockup is not in it yet (`notes/art.md`).
