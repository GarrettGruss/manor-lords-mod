## Why

The owner wants the player to set up the scenario before the game starts. Issue: #375.

Owner decisions (2026-10-21):
- The mod does not use or change the game's own new game and Game Setup menus. It does not read the game's Raider Frequency.
- The Invasion Mod opens its own scenario settings menu when a new game starts.
- The settings are kept with the save and applied again on load.

This replaces the plan of the spike `spike-new-game-difficulty-setting` (#358) to put the difficulty in the game's new game menu. The spike showed that this is fragile: the stock entry writes only game properties, and a game update can rename the widgets.

Design served: `design/mod/invasion-mod.md` (the raid schedule and the difficulty). The change keeps all pillars: it only sets existing mod values before play and adds no new mechanic. Pillar 4 (dread from knowing) is kept: raids stay announced.

## What Changes

- A new menu, the scenario settings menu, opens when a new game starts. It shows a short background text of the scenario and these settings:
  - Difficulty: Easy, Normal, Hard (mod difficulty 1, 2, 3; default Normal). Exists today.
  - First Hussite raid: after 1, 2 or 3 years (default 2). Does NOT exist yet as a mod option. It sets the first year in which the yearly season roll of the approved change `update-raid-clock-yearly` (#339; chances 25, 33, 50, 100 percent per season) may bring the raid. This change depends on that change: it is implemented after it.
  - Raid size: Small, Medium, Large (default Medium). The sizes exist. Today the size class is picked at random. The menu fixes the class.
  - Great raids: On or Off (default On). Does NOT exist yet. Today the great raid clock always runs.
  - Buttons "Use defaults" and "Begin the game". The game stays paused until Begin.
- The background text is a configurable text. The owner writes it.
- The settings are stored in the mod state and applied again when the save loads. The menu does not open for a loaded game.
- Named commands let a test scenario skip the menu or choose values without the mouse. `invasion_set_difficulty` keeps working at any time.
- Look: the approved mockup https://claude.ai/artifact/9bisAE2P6W2dugtfKdzuL7 (illuminated manuscript, the style of the raid menu of #340). PNG images load at run time (decision #333).

## Capabilities

- New: `mod/scenario_settings` (the menu, the settings, the new game detection, the commands).
- Modified: `mod/invasion` (the difficulty is no longer picked once with a prompt; it comes from the settings).
- Modified: `mod/raid_widget` (the difficulty buttons are removed).
- Reused, not changed: `mod/mod_state` (storage), the menu framework of #308 (`core/menu.lua`).

## Non-goals

- No change to the game's own menus, and no read of Raider Frequency.
- No new difficulty levels, no new raid sizes, no new raid types.
- The raid menu (F8) loses its three difficulty buttons (owner, 2026-10-21): REMOVED requirement "A click on a difficulty button picks the difficulty" of `mod/raid_widget`.
- No save call. The mod never saves. Only the harness action `save_game` may save.

## Impact

- Code (later): a new feature folder `mod/InvasionMod/Scripts/features/scenario_settings/`, small changes in `features/invasion/init.lua`, the menu images in the pak.
- Harness: named commands only. Harness code does not name the mod.
- Supersedes the menu part of #358. `invasion_set_difficulty` from that spike stays.
