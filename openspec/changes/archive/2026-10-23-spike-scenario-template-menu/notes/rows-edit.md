# Question 2: remove and add rows (tasks 3.1 and 3.2)

## Verdict

**Both work from Lua at run time.** Hiding a row: `SetVisibility(1)` (Collapsed). Adding a row: clone `W_Menu_GameSetupSettingEntry_C`, `AddChildToGrid`, set the label with the `Text` widget and the choices with `Spinner:UpdateOptions`. The value is read in Lua with `GetCurrentIndex` or `GetCurrentOption().Value`. No pak is needed. Nothing was saved. Run `menu-h-185800`.

## Hide rows (works)

- `entry_aggressiveness`, `entry_baron`, `entry_bandit_initial` and `entry_bandit_max` were set to Collapsed (`GetVisibility` reads 1 after). The grid closes the gap. Picture `evidence/m2-rows-hidden.jpg`: AI Aggressiveness, Off Map Adversary and both bandit camp rows are gone. End Goal, AI Opponents, Raider Frequency and Raider Free Years remain.
- Hidden rows keep their values in the instance. They are only not shown. Whether `UpdateAll` or `SetOptionAvailable` shows a collapsed row again (the game itself collapses `entry_resources`) was not tested.

## Add a row (works)

- Steps: `library:Create(controller, class, controller)`, `grid:AddChildToGrid(widget, 21, 0)`, `widget.Slot:SetColumn(1)` (the real rows use column 1), `widget.Text:SetText(FText("Hussite raid level"))`, `widget.Spinner:UpdateOptions({ {Value="0", Label=FText("Off")}, {Value="1", Label=FText("Gentle")}, {Value="2", Label=FText("Normal")}, {Value="3", Label=FText("Harsh")} }, false)`, `scrollbox:ScrollToEnd()`.
- Picture `evidence/m3-row-added.jpg`: the row "Hussite raid level" at the bottom, styled like the others, with arrows and the value "Harsh". The earlier test (#358) put the clone at the top left because it used `AddChild` on a grid. `AddChildToGrid` places it.
- Read the value: `Spinner:SelectIndex(3)`, then `GetCurrentIndex()` = 3 and `GetCurrentOption().Value:ToString()` = "3". `Next()` and `Previous()` change the index (wrapping is on). A real click on the arrows of the new row was not made.
- Not done: the icon of the clone (default); a hook that fires when the player changes the value (the spike polled with eval; `SelectionChangedEvent` and `OnSettingChanged` are delegates, and adding a delegate to a run-time widget may crash like `Button.OnClicked:Add`, so poll or read at "Continue"); making the row again each time the screen opens (needs a `NotifyOnNewObject` hook on `mainMenu_GameSetup_C`); carrying the value past the map load (mod state).
- Safety: all edits were in the menu of a loaded game, wrapped in `pcall`. `params` and `setupPreset` were not read or written.

## Not verified

A value change by a real click on the new row; the screen with a controller; a language change; a second open of the screen.
