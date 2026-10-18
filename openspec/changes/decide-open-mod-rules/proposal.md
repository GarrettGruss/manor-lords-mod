# Proposal: Decide the open mod rules

Issue: #277. Legacy source: the loose open items of `docs/mod/M02`, `M04`, `M06`, `M07`, `M08`, `M10` and `M13` (listed in `openspec/changes/migrate-legacy-work/notes/inventory-mod.md`, section "Loose open items").

## Why

The legacy mod specs hold open items that are in no iteration file. Most of them wait for a game design decision of the owner, or are tuning. The migration of the legacy work (`migrate-legacy-work`) moves every open item into a change, so these items get this change. Each decision either closes an item or starts a new change.

## What Changes

- A list of the open items with the question for the owner (in `design.md`).
- For each answer: close the item, or open a new change (gate 1) for it.

## Non-goals

- No game design content is written here. The owner decides.
- No code.

## Legacy folders

`docs/mod/M02-invasion/`, `M04-bandits/`, `M06-sack_and_terms/`, `M07-vassals/`, `M08-tribute/`, `M10-finite_resources/`, `M13-manor_stronghold/` (read only).

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None (`skip_specs: true`). A decision that adds behavior gets its own change with delta specs.

## Impact

Only planning. Each answer may start a new change.
