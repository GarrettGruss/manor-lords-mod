# Design: Spike finite resource limits

## Context
- `mod/InvasionMod/Scripts/features/finite_resources/world.lua` uses the region functions `setProductionLimit`, `setProductionUnlimited`, `isProductionLimited` and `getProductionLimit`. That is the workplace limit rule, not the deposit of a mine.
- The deposit of a mine (the finite amount that a resource node holds) and the unlimited flag of a region are different things. The spike must find which property or function holds each one.
- Read first: living spec `openspec/specs/mod/finite_resources/spec.md`, the code above, and `docs/wiki/concepts/engine-limits.md`.

## Questions the spike answers
1. Where is the finite limit of iron and salt stored (region, resource node, mine building)? Can Lua write a high value, and does the game keep it?
2. Is there a region flag for unlimited resources? Can Lua switch it, and does a switch back work?
3. A finite mine is switched to infinite after its deposit is used up. Does it work again, and does it stay finite when switched back?
4. Does the game show the new limit in its own UI (the workplace screen)?
5. Which way gives "large finite, never infinite" with the least risk?

## Method
- Use a test save with an iron mine and a salt mine. Use bridge reads first, then single writes, one change per run.
- Record before and after values for each write. Do not use `Tags` writes or soft object field reads (CLAUDE.md, Safety).
- Raise the game speed to use up a small deposit.

## Safety
- Single-player only. No save function, no `Request Autosave`. Back up the save folder before runs.
- Do not edit game files or game paks.
