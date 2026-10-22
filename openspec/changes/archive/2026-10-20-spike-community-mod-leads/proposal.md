# Proposal: Spike community mod leads

Issue: #280. Legacy source: `openspec/changes/archive/2026-10-15-legacy-13-mod-inspection/README.md` and `openspec/changes/archive/2026-10-15-legacy-13-mod-inspection/implementation-notes/summary.md` ("Proposed follow-up spikes").

## Why
Spec 13 read 20 community mods and proposed follow-up spikes. The inspection is done. Some leads were used later: the M2 data lead (`maxInRegion`, `placedWithin`) is in the walls and housing modules, the P3 refugee lead is in the bandit settlement work (spec 15), and the battle place lever became the battlefield anchor (spec 10). Five leads have no code and no test yet:
1. R3 real loot: read `GetEquippedID` of killed raiders and move goods with `addToInventory`.
2. Stances: `SetBehaviourStance` on an AI squad (only `harness/scenarios/probe_steer.py` touches it).
3. Unit growth: `spawnCompleteUnit` to add units to a lord army one squad at a time.
4. Squad camp state: read `Squad.camp` and `campLocation` while a baron army waits.
5. Building mesh swap: `LoadAsset_Blocking` plus `SetStaticMesh` on one finished building (the code uses `SetStaticMesh` in parts and walls, not this load path).

Each is a claim from DLL strings or Lua source that no game test has checked.

## What Changes
- For each lead, run one short probe in the real game and write the result to `notes/`.
- Say for each lead whether a mod feature needs it. Drop the leads that no feature needs.

## Non-goals
- Installing or running any community mod.
- Copying mod code. Notes describe and cite only.

## Legacy folders
`openspec/changes/archive/2026-10-15-legacy-13-mod-inspection/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None now. A working probe that becomes a command adds a requirement to the matching `harness/*-commands` capability.

## Impact
Needs the real game. Follow the Safety rules for `FName` arguments (`CLAUDE.md`).
