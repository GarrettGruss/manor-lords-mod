# Proposal: Add raid menu actions

Issue: #340.

## Why
Owner decisions (2026-10-20, `decide-open-mod-rules`):
- Answer 2: "Yes: buttons for the terms and the raid start in the raid menu." Narrowed by the owner on 2026-10-21: no Pay or Fight terms buttons and no Start raid button in the raid menu yet (see Open questions).
- Answer 8: "Yes: a button for the bandit buy-back in a mod menu." Owner decision (2026-10-22): "raid menu should be used for local bandits". The buy-back button goes into the raid menu.

Today the player can only pick the difficulty in the raid menu. Terms and the bandit buy-back need named commands, so only a test or a developer can use them.

## Dependency
This change builds on `add-mod-menu-access-rule` (#308), now merged and archived: `core/menu.lua` is the base menu module. The button is content and an action of the raid menu, which is built on it.

## What Changes
- The raid menu shows one button for the bandit buy-back (local bandits), with the price. The button is disabled, with the reason, when the buy-back would be refused or no bandits are present.
- The button calls the same function as its named command.

## Non-goals
- The base menu, bottom bar buttons and click blocking (`add-mod-menu-access-rule`).
- The game's bandit negotiation messages (a separate spike).
- Pay and Fight terms buttons and a Start raid button in the raid menu (owner, 2026-10-21: not yet; a later change may add them).
- Vassalage terms buttons.
- A redesign of the raid menu (separate change). This change only adds the one button.

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `mod/bandits`: new requirement for the buy-back button in the raid menu.

## Impact
- Code: `mod/InvasionMod/Scripts/features/bandits/` (menu content), the menu pak if a button needs a widget part.
- Tests: `test_fakegame_bandits.py`, new real game test scenarios with pictures.
- Picture evidence (UI feature).

## Open questions
1. Answered (owner, 2026-10-21): no Pay or Fight terms buttons and no Start raid button in the raid menu yet. Only the bandit buy-back button stays (`mod/bandits`). The raid menu itself does not change in this change.
2. Answered (owner, 2026-10-22): the raid menu holds the bandit buy-back button for local bandits. No menu of its own for bandits. The raid menu redesign is a separate change.
