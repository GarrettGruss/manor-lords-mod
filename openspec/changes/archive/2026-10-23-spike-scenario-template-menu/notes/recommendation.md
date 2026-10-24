# Recommendation (spike-scenario-template-menu, #416)

## Verdicts

| Question | Verdict | Route |
|---|---|---|
| 1. A 6th template "The Hussites Are Coming" on the game's screen | **Yes** | A pak row in `DT_GameSetupPresets` (button appears by itself, a real click applies the row's settings). Run-time Lua can draw a button, but it cannot select a preset. |
| 2. Remove rows and add mod rows | **Yes** | Run-time Lua only: collapse rows, clone `W_Menu_GameSetupSettingEntry_C` with `AddChildToGrid`, own choices with `Spinner:UpdateOptions`, read the value with `GetCurrentIndex`. |
| 3. Do the six settings change the mod AI | **No** | The mod reads none of them. They drive native raids, camps and lords. Camps 0 means no bandit pawn (the mod can make one with `spawnBanditCamp()`, spike #430). |

## Follow-up options for the owner (decision 5.4)

1. **Keep the separate start menu** (the owner decision of 2026-10-21, `add-scenario-settings-menu`). Cost: none. The two screens stay separate.
2. **One screen on the game's menu.** A change with these parts: (a) the 6th template row in the mod pak (add `DT_GameSetupPresets` to `modpak.py`, own thumbnail, text rows), (b) a Lua step that opens when the screen is created (`NotifyOnNewObject` on `mainMenu_GameSetup_C`): collapse rows that the mod does not use (Aggressiveness, Off Map Adversary, camps) and add the mod rows (the three raid levels, "First Hussite raid", "Great raids"), (c) read the rows when "Continue" is pressed and write them into the mod state after the map loads, (d) a way to know that the mod template was chosen (a unique setting combination or a gameplay tag in `customTags`; the tag was not tried). Risks: widget names can change in a game update; the screen is rebuilt on each open; no hook on a value change (poll); `UpdateAll` may undo a hidden row (not tested).
3. **Template only.** Add only the pak row (1a, 1d) as a "starter" that sets safe game values for the mod (for example baron Absent, camps 1, frequency None), and keep the mod menu for the mod values. This is the smallest change.

My suggestion: option 3 first (small, and it removes the playtest problem of mismatched game settings), and decide on option 2 after the owner has seen the pictures. Option 2 removes one screen but needs the most Lua UI code.

## Not verified (carry-over)

Row text and thumbnail of the new template; `Continue` after the mod template (no new game started); the value of an added row after a real click on its arrows; a hook on screen creation; save and load of any mod value.

## Safety notes of this spike

- No save function was called. `menu.sav` in the real save folder was identical to the backup after all sessions (hash `a3eabb42...`): the harness runs use a private `LOCALAPPDATA`.
- `allow_eval` was set to true in the `UEBridge/scripts/settings.lua` of the slot copies in use (`slots/1`, `slots/2`) and once in the game folder (slot 0). Each deploy resets it. The game folder file was compared with the repo file at the end: equal.
- The scratch pak `presetsix_P.pak` was removed by the run teardown. Its work folders are in the git-ignored `modtools/work`.
