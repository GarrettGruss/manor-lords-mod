# Proposal: find out if Lua can read rich game without a mouse hover

Issue: #550. Follow-up of #548 (spike-rich-food-resources).

## Why

Rich resources are random per game start, so a config table for rich game is not acceptable. The tooltip shows "Wild Animals (17/28)" and "Rich Resource", but only on a hover.

## Question

Can Lua get the game area (current/max) or its rich flag without a hover? Try: the tooltip code path, node and component properties, managers, and a comparison of the 4 deer nodes.

## What Changes

- New hidden probe `probe-rich-game` (read only, no save call).
- Findings in `notes/rich-game-detection.md` and wiki facts in `docs/wiki/concepts/engine-limits.md`.

## Non-goals

- Any mod code change. Any save call.

## Capabilities

### New Capabilities
- None. This is a spike (`skip_specs`).

### Modified Capabilities
- None.

## Impact

- Notes, one probe, wiki facts.
