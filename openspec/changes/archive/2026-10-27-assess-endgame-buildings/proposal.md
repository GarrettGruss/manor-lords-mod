# Proposal: Assess end-game buildings, guildhalls and a Health metric

Issue: #521. Owner request, 2026-10-28.

## Why
The owner lists end-game ideas for the Invasion Mod: ten one-off buildings (dockyard, boatwright, Rathaus, astronomical clock, apothecary, inn, cobblestone roads, bath-houses, tournament grounds), guildhalls with guild recruits, and a new Health metric. Before any design or spec work, we need to know what the engine allows today: new buildings, goods and recipes, unit templates, a new metric, and effects (happiness, influence, income, merchant visits, trade speed, experience).

## What Changes
- Read the wiki, the archived spikes, the living specs, the extracted game data and the mod code (desk research).
- Rate each concept: feasible now, feasible with pak work, needs a spike (with the exact question), or not feasible without native code. Give a rough effort and the dependencies.
- Recommend the order of spikes and first changes.
- Move newly established engine facts into the wiki.

## Non-goals
- Any code, pak or model. This change builds nothing.
- Game design. The notes only rate feasibility. Design stays with the owner (`design/mod/`).
- A native C++ layer. It needs an owner decision (`docs/wiki/concepts/native-modding.md`).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None.

## Impact
Read-only study. No game run. Files read: `docs/wiki/`, `openspec/changes/archive/`, `openspec/specs/`, `modtools/work/` (extracted tables, read-only, not committed), `mod/`.
