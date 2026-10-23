# Proposal: update-raid-difficulty-levels

Issue: #404

## Why
Owner decision (2026-10-22): "In the start menu, the yearly player raid, great raid, and vassal raids should be configured from 0 (off), 1 (easy), 2 (medium), 3 (hard)."

Today the start menu has one global Difficulty (Easy, Normal, Hard) and a Great raids On or Off switch. One value cannot tune the three raid types apart, and a raid type cannot be switched off.

## What Changes
- The start menu has three level settings, each 0 (off), 1 (easy), 2 (medium) or 3 (hard):
  - **Yearly player raid**: the large yearly plunder raid on the player.
  - **Great raid**: the great raid clock, waves, relief army and final battle.
  - **Vassal raids**: the subjugation raids against vassals.
- Level 0 turns that raid type off: it is not planned, does not spawn and has no banner and no menu entry.
- Level 1 to 3 is the difficulty of that raid type only. It replaces the single global difficulty for that type (squads, roles, waves, relief army).
- The global Difficulty setting is removed. The setting "Great raids" On or Off is replaced by the Great raid level (Off is level 0).
- The settings "First Hussite raid" and "Raid size" are kept (see the open questions).
- Defaults: level 2 for each of the three settings (the old default Normal is difficulty 2; Great raids was On).

## Assumptions
- Yearly player raid level 0 means no yearly raid at all; the small yearly plunder raid follows the same level (there is no separate switch for it).
- Raid size (Small, Medium, Large) stays the size class; the squads are the class multiplier times the level of the raid type.
- Level N maps to the old difficulty N for the numbers (squads, role mix, waves, relief army).
- `invasion_set_difficulty` and `invasion_pick_difficulty` stay as test commands; they set the three levels together. New commands set one level.

## Overlap
- `update-raid-banners` (#400): "Great raids Off" there is level 0 of the Great raid setting here. A raid type at level 0 shows no banner.
- `add-scenario-settings-menu` (#375) is not archived yet, so `mod/scenario_settings` has no living spec. The delta here uses MODIFIED for its requirements (validate shows an info line). Archive that change first, then this one; if the order changes, turn the delta into ADDED. `update-raid-clock-yearly` also changes the raid timing.

## Impact
- Specs: `mod/scenario_settings` (menu settings, Great raids setting, commands), `mod/invasion` (raid size, difficulty, subjugation raid, waves, relief army).
- Code: `features/scenario_settings`, `features/invasion` (`init.lua`, `plan.lua`), the widget `make_scenario_settings_widget.py`, the pak.
- Tests: `test_fakegame_scenario_settings.py`, `test_fakegame_invasion.py`, test scenarios under `scenario_settings/` and `invasion/`. Picture evidence of the new menu.

## Owner decisions (2026-10-22)
The owner approved gate 1 with the answers proposed above:
1. The global Difficulty setting is removed.
2. "First Hussite raid" and "Raid size" are kept.
3. The default is level 2 (medium) for each of the three levels (the menu "Use defaults" and an old save). The start value of the mod state before the menu applies anything is level 1, as the old difficulty was 1 (`config.invasion.levels`); this keeps the fake game tests and the fixtures that skip the menu on the old numbers.
4. The small yearly plunder raid follows the yearly player raid level. It has no own switch.
