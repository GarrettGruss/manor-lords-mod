# Proposal: Add raid menu actions

Issue: #340.

## Why
Owner decisions (2026-10-20, `decide-open-mod-rules`):
- Answer 2: "Yes: buttons for the terms and the raid start in the raid menu."
- Answer 8: "Yes: a button for the bandit buy-back in a mod menu."

Today the player can only pick the difficulty in the raid menu. Terms and the bandit buy-back need named commands, so only a test or a developer can use them.

## Dependency
This change builds on the open change `add-mod-menu-access-rule` (#308, branch `feat/add-mod-menu-access-rule`). That change makes one base menu module (`core/menu.lua`): a menu gets its bottom bar button, fullscreen view and click blocking from it, and adds only its id, label, content and actions. The buttons here are content and actions of menus built on `core/menu.lua`. Do not start the code before the base menu is merged. If #308 changes, update this change.

## What Changes
- The raid menu shows buttons for an open terms offer: Pay (accept the payment terms) and Fight (decline the terms; the raid goes on).
- The raid menu shows a button to start the planned raid at once.
- A mod menu shows a button for the bandit buy-back, with the price. The button is disabled when the buy-back would be refused.
- Each button calls the same function as its named command.

## Non-goals
- The base menu, bottom bar buttons and click blocking (`add-mod-menu-access-rule`).
- The game's bandit negotiation messages (a separate spike).
- Vassalage terms (a button for them can follow later).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `mod/raid_widget`: new requirements for the terms buttons and the raid start button.
- `mod/bandits`: new requirement for the buy-back button.

## Impact
- Code: `mod/InvasionMod/Scripts/features/raid_widget/`, `features/bandits/` (menu content), the menu pak if a button needs a widget part.
- Tests: `harness/tests/test_fakegame_raid_widget.py`, `test_fakegame_bandits.py`, new real game test scenarios with pictures.
- Picture evidence (UI feature).

## Open questions
1. "The raid start": does the owner mean a button that spawns the planned raid at once, or the Fight button after terms? This proposal has both (Fight declines terms; a separate start button spawns the planned raid).
2. Which menu holds the buy-back button: the raid menu, or a menu of its own for bandits?
