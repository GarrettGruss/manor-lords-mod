## Why

Issue: #451. The Invasion Mod needs game settings that fit the mod: no AI lords, no off-map adversary, no native raids and no bandit camps (the mod controls them). Today the player must set these by hand on the New Game screen, and a wrong setting breaks the mod (see change `add-game-settings-guard`, #438). Spike #416 showed that one new row in the game data table `DT_GameSetupPresets` gives a 6th button in the "Scenario Templates" row, and a real click applies the row to the game settings. The owner chose this route (option A, 2026-10-23).

## What Changes

- A new row `hussites_are_coming` in `DT_GameSetupPresets`, shown as a 6th scenario template with the title "The Hussites Are Coming".
- Selecting it sets these game settings: End goal Growth, AI opponents 0, Off map adversary Absent, Raider frequency None, Initial bandit camps 0, Random bandit camp spawn limit 0, Starting season Spring, Starting supplies Standard, Royal tax None, Armament delivery No, Residential requirements Balanced, Food spoilage Standard, Approval Low penalty, Well placement Underground water, Weather Difficult.
- The mod keeps its own start menu. A new game started from the template opens it as today. The mod settings (raid levels, first raid, raid size) stay in that menu.
- The row is built by the existing mod pak build path (`pakmod.py buildmod InvasionMod`): patches for `DT_GameSetupPresets` are added to `harness/tools/modpak.py` (tables with named rows, not only numeric ids), and the row is a patch file of the feature `scenario_settings`.
- A thumbnail: the row reuses an existing game thumbnail (`mode_citybuilding`). A new image is not made in this change.
- A marker: the mod stores `hussite_template` (true or false) in ModState at new game start, when the chosen template can be detected from the game setup. If it cannot be detected, the change records this in `notes/` and the marker stays out.

## Interaction with add-game-settings-guard (#438)

With this template, the guard (#438) reads: `vassals` = false (AI opponents 0), `villager_banditry` = false (camps 0) and `hussites_enabled` = true or false as the guard maps "Off map adversary". The template sets Off map adversary to Absent, so the guard would lock the Hussite raid rows if it reads that field as `hussites_enabled`. The owner must decide before both changes are built: either the guard reads another field for `hussites_enabled`, or the template keeps the adversary Present. This change builds the settings as the owner listed them and records the conflict in the issue. Default if no decision: the template is built as listed, and the guard change resolves the mapping.

## Open questions (with defaults)

- Option labels (Spring, Standard, Difficult and others) map to stored values. The change reads the labels from the screen in a real run and checks each one. Default: the values of the nearest existing row (`peaceful_citybuilding`, Medium).
- Title text: the row name text comes from `DT_Translation_GameSetups`. Default: a patch of that table when the title key is known; otherwise the title is set at run time and noted.

## Impact

- Specs: `mod/scenario_settings` (ADDED requirement).
- Code: `harness/tools/modpak.py` (named-row tables), the feature patch file `mod/InvasionMod/data/scenario_settings/patches/`, the mod pak, wiki and skill `harness-pak-mod`.
- A table pak replaces the whole file `DT_GameSetupPresets`. No other mod may change this table. A game update can change the table.
