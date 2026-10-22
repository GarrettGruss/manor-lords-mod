# Proposal: Add raid menu actions

Issue: #340.

## Why
Owner decisions (2026-10-20, `decide-open-mod-rules`):
- Answer 2: "Yes: buttons for the terms and the raid start in the raid menu." Narrowed by the owner on 2026-10-21: no Pay or Fight terms buttons and no Start raid button in the raid menu yet (see Open questions).
- Answer 8: "Yes: a button for the bandit buy-back in a mod menu."

Today the player can only pick the difficulty in the raid menu. Terms and the bandit buy-back need named commands, so only a test or a developer can use them.

## Dependency
This change builds on the open change `add-mod-menu-access-rule` (#308, branch `feat/add-mod-menu-access-rule`). That change makes one base menu module (`core/menu.lua`): a menu gets its bottom bar button, fullscreen view and click blocking from it, and adds only its id, label, content and actions. The buttons here are content and actions of menus built on `core/menu.lua`. Do not start the code before the base menu is merged. If #308 changes, update this change.

## What Changes
- A mod menu shows a button for the bandit buy-back, with the price. The button is disabled when the buy-back would be refused.
- The button calls the same function as its named command.

## Non-goals
- The base menu, bottom bar buttons and click blocking (`add-mod-menu-access-rule`).
- The game's bandit negotiation messages (a separate spike).
- Pay and Fight terms buttons and a Start raid button in the raid menu (owner, 2026-10-21: not yet; a later change may add them).
- Vassalage terms buttons.

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `mod/bandits`: new requirement for the buy-back button.

## Impact
- Code: `mod/InvasionMod/Scripts/features/bandits/` (menu content), the menu pak if a button needs a widget part.
- Tests: `test_fakegame_bandits.py`, new real game test scenarios with pictures.
- Picture evidence (UI feature).

## Open questions
1. Answered (owner, 2026-10-21): no Pay or Fight terms buttons and no Start raid button in the raid menu yet. Only the bandit buy-back button stays (`mod/bandits`). The raid menu itself does not change in this change.
2. Which menu holds the buy-back button: the raid menu, or a menu of its own for bandits?
