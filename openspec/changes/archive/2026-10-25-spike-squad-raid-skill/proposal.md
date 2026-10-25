# Proposal: find out if the native squad raid skill can be driven from Lua

Issue: #492.

## Why

An external native mod (AI Tweaks 0.7.1, game 0.8.117, read-only review) starts a native raid task for a squad. It calls a native `SquadComponent` function with (squad id, skill 19, enable, flag). Skill 19 is "raid". The Invasion Mod needs to know if Lua can read or toggle this skill without native code. These facts are hints, not proven:
- Each squad holds a byte array of active skill ids.
- Skill 9 looks like a march mode that is restored after the raid.
- The reflected `rallied` bool may not be updated by the rally path.
- The raid target building is chosen natively.

## Question

Does UE4SS reflection show a function or property on `SquadComponent`, `PawnCPP` or a related class that reads or toggles squad skill 19? If yes, what does one call do to a player squad?

## What Changes

- Read-only listing of functions and properties (names with skill, ability, raid, loot, plunder, stance, mode, behaviour).
- Only if a candidate exists: one call with skill 19 on, observe a few game minutes, then off.
- Findings go in `notes/`. Lasting facts go in the wiki.

## Non-goals

- Control of the raid target from Lua.
- Reading `Squad` structs, `GetSquad`, or any call from the list in DANGEROUS_ACTIONS.md.
- Any save call.

## Capabilities

### New Capabilities
- None. This is a spike (`skip_specs`).

### Modified Capabilities
- None.

## Impact

- Notes in this change folder and wiki facts. No code change.
