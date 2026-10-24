# Question 1: a 6th scenario template (tasks 2.1 and 2.2)

## Verdict

**Yes, with a pak.** One new row in `DT_GameSetupPresets` gives a 6th template button without any Lua. A real click applies the row's settings to the game. A run-time Lua button works only for the picture. It cannot select a preset.

## Route B: pak (works)

- Built `presetsix_P.pak` with one file pair (`ManorLords/Content/ManorLords/Database/DT_GameSetupPresets`, 1.4 KB). Steps: table JSON from `pakmod.py tojson`, `clone_table_row.py <json> baron hussites_are_coming` (row 6 is a clone of `baron`), `fromjson`, `build`. Pak size 3752 bytes. `run.py --pak presetsix` installs and removes it.
- Result (run `menu-p-190638`): `ModePresets` has **6 children**, the last one `presetRowName = hussites_are_coming`. Picture `evidence/m5-pak-sixth-template.jpg`: six thumbnails, the new one shows the thumbnail of the cloned row.
- A real click (run `menu-q-191928`): the preset values reach `MLGameInstance.gameSetup` and the screen rows (see `menu-widgets.md`). So the row can set all game settings of the template (AI lords, baron, aggressiveness, raid frequency, camps, supplies).
- Not done in this spike: its own thumbnail (a texture asset and the soft path in the row), the title and tooltip text (rows in `DT_Translation_GameSetups`; hover was not tried), and the difficulty variants in `gameSetupData` (the clone keeps the baron variants).
- The row cannot carry the mod's own values (raid levels). Those stay in the mod's own menu or in added rows (`rows-edit.md`).
- The cloned `customTags` is empty, and the instance copy showed `customTags n=0`. A marker tag (to tell the mod that the Hussite template was chosen) was not tried: it needs a valid gameplay tag. Another way is a unique value combination in the row. Open.

## Route A: run-time Lua (partly)

- `WidgetBlueprintLibrary:Create` of `mainMenu_GameSetupPresetButton_C` and `ModePresets:AddChildToHorizontalBox` work (children 5 to 6). The new button has no `setupPreset`, so it shows a default image. Without a slot size the button is drawn very large and shrinks the others. `slot:SetSize({Value = 1, SizeRule = 1})` (Fill) fixes it (`evidence/m4-sixth-button.jpg`).
- `button:HandlePressed(true)` and `button.gamePresetSelected:Broadcast(false)` changed nothing, also on the five real buttons (instance and screen rows unchanged). The click handler is native. So a Lua-made button cannot select a preset by a call. A real click on the Lua button was not tried (it has no `setupPreset`).
- Verdict A: the picture works, the function does not. A mod would need its own click hook. Not recommended.

## Recommendation

Use the pak route (cheapest, no widget code). Costs: one table row in the mod pak. The patch tool `modpak.py` supports only the tables `buildingStats` and `DT_Upgrades` today, so it needs `DT_GameSetupPresets` added. A table pak replaces the whole file, so no other mod may change this table. One thumbnail and text rows are also needed. Risk: a game update can change the table.

## Not verified

The row text and thumbnail; `Continue` after the 6th template (no new game was started); a save and load; two mods that add rows.
