# Proposal: find out how Lua tells rich game, berries and fish from poor ones

Issue: #548. Follow-up of #546 (spike-region-rich-resources).

## Why

The vassal tribute rule uses the 2 rich resources of a region. The owner says (2026-11-01) that game, berries and fish can be rich. The earlier spike found no flag for them.

## Question

1. Where are berry areas, hunting grounds (game) and fishing areas stored?
2. What marks them rich (decal size, material, properties, tooltip)?
3. Which region has which rich food resource on the test map?
4. Which item id does each yield?

## What Changes

- New steps in the hidden probe `probe-region-resources` (read only, no save call).
- Findings in `notes/rich-food-resources.md` and wiki facts in `docs/wiki/concepts/engine-limits.md`.

## Non-goals

- Any mod code change. Any save call.

## Capabilities

### New Capabilities
- None. This is a spike (`skip_specs`).

### Modified Capabilities
- None.

## Impact

- Notes, probe steps and wiki facts.
