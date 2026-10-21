# Proposal: Spike bandit message toggle

Issue: #343.

## Why
The owner decided (chat, 2026-10-20, `decide-open-mod-rules`, item 8): "Yes: a button for the bandit buy-back in a mod menu. Also test whether the game's bandit negotiation messages can be turned off, because they may conflict with the mod."

The feature `mod/bandits` lets the player buy families back from a bandit squad. It sends the native negotiation letter (`raider_suggestSettle+<price>`). The game also shows its own bandit negotiation messages. The two may show at the same time or disagree. The button goes with the base menu change (#308). This spike covers only the messages.

## What Changes
- Find which message class or event makes the game bandit negotiation messages.
- Find out whether Lua can suppress them: hook and skip, a data table row, or a setting.
- Record the side effects of each way, and whether the mod buy-back still works.
- Write the results to `notes/` with screenshots, and recommend one way.

## Non-goals
- The buy-back button and menu. That is part of the change for #308.
- Changing the buy-back rules of `mod/bandits`.
- Any save call (CLAUDE.md, Safety).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None. A spike records findings only.

## Impact
- Real game runs, one at a time, single-player, no save call. Each run id goes into the notes.
- Screenshots go in `notes/` or `evidence/`, each listed with its test scenario and run id.
