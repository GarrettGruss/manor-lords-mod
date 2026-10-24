# Findings: the template "The Hussites Are Coming" (#451)

## What was built
- Row `hussites_are_coming` in `DT_GameSetupPresets`: a clone of `peaceful_citybuilding` with the owner settings in all three difficulties (`gameSetupData/*/...`) and in `currentGameSetup`. Text rows `hussites_are_coming`, `_goal`, `_setup` in `DT_Translation_GameSetups` (one English text for every language).
- Pak: `pakmod.py buildmod InvasionMod` gives `mod/InvasionMod/paks/InvasionMod_P.pak` (51 KB, four files). The `example` feature is set to `"pak": false`, so its test rows (building 1000) do not go into the player pak.
- The mod menu widget stays in `raidmenu_P.pak`. A real run needs both: `--pak raidmenu --pak InvasionMod`.

## Values checked in the real game (run `hussite-tpl-13`, real mouse click on the 6th template)
Screen labels: End Goal Growth, AI Opponents 0, Off Map Adversary Absent, Raider Frequency None, Initial Bandit Camps 0, Random Bandit Camp spawn limit 0, Starting Season Spring, Starting Supplies Standard, Royal Tax No tax, Armament Delivery No, Residential Requirements Balanced, Food Spoilage Standard, Approval Low Penalty, Well Placement Underground Water, Weather Events Difficult.
Stored values (read with `game_setup_state`): AI lords 0, adversary_baron false, raiding frequency 0, camps 0 and 0, starting day 61, supplies 1, royal tax 0, armament false, requirement bias 0, spoilage 2, loyalty loss 0.5, water veins true, weather 2.

## Thumbnail
The row reuses the game thumbnail `mode_citybuilding` (the same picture as the City Building template). A new image was not made. A new image needs a texture asset in the pak and a changed soft path in the row.

## Title text
The tooltip of the 6th template shows the title "The Hussites Are Coming" and the two texts. Both text blocks have the heading "Victory Conditions": that heading is the game's own (it comes from the screen, not from the row).

## Marker
The game keeps no template name (`scenario` stays `None`). The mod detects the template from its settings combination: Royal tax None, Weather Difficult, Approval Low penalty, AI lords 0, adversary absent and no bandit camps (`rules.is_hussite_template`). No game template has this combination. It stores `hussite_template` (1 or 0) in ModState at new game start. A player who sets all these values by hand gets the same marker.

## A bug found and fixed on the way
The scenario settings feature decided "new game or loaded" once per session. A game that was loaded first and then went back to the main menu and started a new game never opened the mod start menu (run `hussite-tpl-8`). The decision is now made again after each ModState load (new player pawn). Fake-game test `SecondGameInOneSessionTests`; real run `hussite-tpl-13`.

## Interaction with add-game-settings-guard (#438)
With this template: AI opponents 0 gives `vassals` false, camps 0 gives `villager_banditry` false. Off map adversary Absent gives `hussites_enabled` false if the guard reads that field, and the guard would then lock the three raid rows. The owner must decide the field mapping in #438 (see proposal).

## Open for the owner
- The release pipeline (`harness/release.py`, `mod.json` `pak`) ships one pak (`raidmenu`). The template needs `InvasionMod_P.pak` too. A release with the template needs a second pak entry or one merged pak.
- A table pak replaces the whole `DT_GameSetupPresets` and `DT_Translation_GameSetups` file, so another mod that changes them conflicts.
- Real runs on a computer where other games start steal the window focus: the test scenario retries the mouse action.
