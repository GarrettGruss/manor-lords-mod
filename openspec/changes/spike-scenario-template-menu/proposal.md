# Proposal: Spike scenario template menu

Issue: #416.

## Why
Owner request (2026-10-23, with a screenshot of the New Game "Scenario Templates" screen). The screen shows 5 template pictures, the "Template Difficulty" banners (Relaxing, Default, Challenging) and settings rows with left/right arrows: End Goal, AI Opponents, Off Map Adversary, AI Aggressiveness, Raider Frequency, Raider Free Years, Initial Bandit Camps, Random Bandit Camp spawn limit, Starting Season, Starting Supplies, and more below.

The mod has its own start menu (`mod/scenario_settings`). The owner wants to know if the mod can use the game's screen instead, and which game settings change the mod's behavior.

Known facts (change `spike-new-game-difficulty-setting`, #358, archived):
- `MLGameInstance.gameSetup.currentGameSetup` is readable from Lua, but it is not saved.
- Visiting the setup screen changes `menu.sav`.
- The module `mod/shared/HarnessGameSetup` reads the setup.

## What Changes
Nothing is built. The spike answers three questions and ends with a recommendation:

1. Can the mod scenario ("The Hussites Are Coming") be added as a 6th scenario template on this screen? Test Lua at run time and a pak (data table, widget, template asset).
2. Can the mod remove settings rows from this screen, or add its own rows (for example the raid levels yearly, great and vassal, 0 to 3, from change `update-raid-difficulty-levels`), instead of the separate start menu?
3. Do the game settings Raider Frequency, Off Map Adversary, AI Aggressiveness, Random Bandit Camp spawn limit, Initial Bandit Camps and Raider Free Years change the mod AI (Hussite raids in `mod/invasion` and `raid_behavior`, `mod/bandits`, vassals and sack)? Or do they only drive native raids and camps?

## Outcomes
- `notes/menu-widgets.md`: widget classes and data source of the screen.
- `notes/template-add.md`: answer to question 1, with the cheapest working route or the proof that none works.
- `notes/rows-edit.md`: answer to question 2.
- `notes/setting-effects.md`: answer to question 3, with A/B results per setting.
- `notes/recommendation.md`: verdict per question and a follow-up change proposal.
- Lasting engine facts go to `docs/wiki/`.

## Non-goals
- Building the feature (template, rows or a new start menu).
- Changing `mod/scenario_settings`, `mod/invasion` or `mod/bandits`.
- Calling any save function.
