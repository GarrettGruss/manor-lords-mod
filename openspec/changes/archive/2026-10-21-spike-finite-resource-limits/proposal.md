# Proposal: Spike finite resource limits

Issue: #342.

## Why
The owner decided (chat, 2026-10-20, `decide-open-mod-rules`, item 7): "An iron mine or a salt mine is enough. Test: can a resource's finite limit be set high, and can a region's unlimited flag be switched? The player region gets large finite limits of salt and iron, never infinite. Test a finite mine switched to infinite: does it still work after its finite deposit is used up?"

The feature `mod/finite_resources` now keeps its own stock for iron, salt and clay and sets the production limit of a good to 0 when the stock is empty. The owner wants a simpler model: the player region holds large finite limits of salt and iron, and they are never infinite. The engine facts for this are not known yet.

## What Changes
- Find out, in the real game, whether the finite limit of a resource in a region can be set to a high value from Lua.
- Find out whether the unlimited flag of a region can be switched from Lua, and what it changes.
- Find out what a mine does after it is switched from finite to infinite, when its finite deposit is already used up.
- Write the results to `notes/` and recommend how the later feature sets "large and finite, never infinite".

## Non-goals
- Changing the feature `mod/finite_resources` or its living spec. That is a later change.
- Clay. The owner said an iron mine or a salt mine is enough.
- Any save call (CLAUDE.md, Safety).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None. A spike records findings only.

## Impact
- Real game runs, one at a time, single-player, no save call. Each run id goes into the notes.
- Raw Lua eval and bridge reads are allowed for the experiment (CLAUDE.md). Do not read struct values with soft object fields.
