# Proposal: find out if Lua can read the rich deposits of a region

Issue: #546.

## Why

The owner decided on 2026-11-01 a new vassal tribute rule: each month a vassal sends a fixed base of 100 of each of the 2 rich resources of its region. Policy scales it (Light x0.5, Fair x1, Heavy x1.5). If a region has only 1 rich deposit, farmland is the second and pays flax. The mod must know the rich deposits of each region.

## Question

1. Where does the game store deposits per region?
2. How does Lua tell a rich deposit from a poor one, and a deposit from a region?
3. What is the good id of each rich deposit?
4. What are the rich deposits of each region on the test map?
5. If it is not readable, what config table is the fallback?

## What Changes

- A hidden probe scenario `probe-region-resources` (read only, no save call). The real mouse hovers over the deposits to read the game tooltip.
- Findings in `notes/region-rich-resources.md`, and wiki facts in `docs/wiki/concepts/engine-limits.md`.

## Non-goals

- Any mod code change. The tribute change uses the findings later.
- Any save call.

## Capabilities

### New Capabilities
- None. This is a spike (`skip_specs`).

### Modified Capabilities
- None.

## Impact

- Notes, one probe scenario and wiki facts. No mod code change.
