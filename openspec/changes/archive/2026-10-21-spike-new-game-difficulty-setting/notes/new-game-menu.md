# Mod option in the new game menu (task 1.2, issue #358)

## Result
- Reusing a game setting needs no widget, and its value reaches the started game (proven).
- A new option widget can be added from Lua (a placeholder shows). A working mod-only option needs more work (not done).
- Run `spike358-3`: the fixture run with `--keep-open`, then the real main menu and a real mouse click. No scenario ran, so the run has no verdict of its own.

## How the menu was reached
- Console `open /Game/NotStronghold/Maps/MainMenu` (bridge op `console`) from the loaded game gives the main menu with `mainMenu_widget_C`.
- Bridge `call` `GoToGameSetup` on `mainMenu_widget_C` opens the Game Setup screen. Picture: `evidence/menu-setup.jpg`.
- A real click on "Continue" starts the new game on the chosen map at once (no more screens).

## A game setting reaches the started game (proven)
- A real click (`osinput`) on the right arrow of Raider Frequency changed the screen from Medium to Frequent (`evidence/menu-setup-clicked.jpg`).
- While the screen was open, the instance did not change (`raiding_frequency` stayed 1, `difficulty` was 0 = Custom).
- After "Continue" and the intro, the started game read `raiding_frequency=2` and `difficulty=0`. So the game writes the setup into `MLGameInstance.gameSetup.currentGameSetup` when the game starts.
- A mod reads the value in the started game with the same code as in a loaded game. Option A (read the game setting) needs no widget and no pak.
- A new game is told from a load by `MLGameInstance.savefileToLoad` (empty on a new game, spec 06 fresh start). Not re-tested here.

## Add a widget (partly proven)
- Command `game_setup_menu_probe` (`HarnessGameSetup`). The rows are children of a panel (the parent of `entry_untilFirstRaid`, 21 children). `WidgetBlueprintLibrary:Create(controller, W_Menu_GameSetupSettingEntry_C, controller)` and `panel:AddChild(widget)` worked (22 children). Picture `evidence/menu-clone.jpg` shows the clone as the text "label" at the top left of the list. The panel does not stack its children, so a real option needs the right box and a place.
- The entry takes its look and its target from `params` (`MLGameSetupSettingEntry`: `PropertyName`, `Label`, `Icon` soft object, `Options` array). `PropertyName` names a property of `GameSetupParameters`. So the stock entry can write only a game property, not a mod value. Reading `params` may crash (soft object). Not tried: writing `params`, or reading the `Spinner` of a clone.
- Option B (own option in the menu) is possible but needs the right parent box, own `params` or an own widget, a value hook, and a way to carry the value after the map loads (the mod state is written after the pawn exists). It has more risk than A. A game update can rename the widgets.

## Cautions
- `HarnessActions` reads only a fixed list of request fields (`parseRequest`). A new command field must be added there, or an existing field reused (`count`, `field`, `value`).
- The first `disable_autosave` right after the new map loaded was undone by the game (timer 624 s). A second call after the intro worked (31535394 s). A new game started from the menu must send it twice or wait.
- Visiting the Game Setup screen changed the game file `menu.sav` in the real save folder (the game remembers the last setup). I restored it from the backup. The fixture slot `saveGame_51` of the kept-open run was removed by hand.
