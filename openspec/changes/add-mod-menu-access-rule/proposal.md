# Proposal: Add mod menu access rule

Issue: #308.

## Why
The owner set a rule for all mod menus (chat, 2026-10-19 and 2026-10-20): the player opens the root of each mod menu from the game UI with the mouse, in at most 2 clicks, without a hotkey. The two current mod menus break it: the raid menu opens only with F8 (`mod/raid_widget`) and the tech tree menu only with F9 (`mod/tech_tree_widget`).

## What Changes
- New `mod/core` requirement: the root of every mod menu opens from the game UI in at most 2 clicks, with no hotkey needed. Submenus inside a root menu are exempt, for example a tech menu with branching paths. A hotkey may stay as an extra shortcut.
- The raid menu and the tech tree menu get a UI entry point that meets the rule.
- New menus (for example the tribute menu of `add-liege-influence`) follow the rule.

## Non-goals
- A click limit for submenus.
- Removing the F8 and F9 keys.

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `mod/core`: adds the menu access rule.

## Impact
Pak widget work for a UI entry point (a button in the game HUD or in an existing game menu). Picture evidence for each entry point. Feature specs `mod/raid_widget` and `mod/tech_tree_widget` keep their key requirements.
