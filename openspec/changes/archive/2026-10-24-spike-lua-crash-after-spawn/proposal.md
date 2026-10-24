# Proposal: Spike Lua crash after spawn

Issue: #465.

## Why
The game crashes often with `EXCEPTION_ACCESS_VIOLATION`. Owner approved this spike on 2026-10-24.

Known crashes:
- `levels-great-raid-waves-2`: read `0xffffffffffffffff`, stack `UE4SS!getgeneric ltable.c:302`, about 1 s after a great wave (15 squads, 448 raiders) spawned.
- `levels-first-raid-4`: read `0x18`, `LuaMadeSimple.cpp:572` metamethod lambda, during a 5-day fast-forward.
- `levels-first-raid-6`: read `0x25e55dc06e1`, after a bandits season change.
- Spike #430: read `0x328` with 3 bandit camps and a second lord.
- Banditcamp runs `20261024-024700-6523` and `20261024-021558-0d65`.
- Early crashes at the first camera picture, before any mod action.

## What Changes
- Collect all crash reports into one table, grouped by signature.
- Audit the mod Lua code for thread and lifetime risks.
- Test hypotheses with A/B runs (one game at a time). Add a free-memory metric to telemetry.
- Recommend fixes. Implement only clearly safe, low-risk ones. List the rest for a follow-up change.

## Non-goals
- A large refactor of the mods.
- Any save call.

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None. A spike records findings only.

## Impact
- Notes in `notes/`. Possibly small safe code fixes and a telemetry metric.
- Real game runs, one at a time, single-player.
