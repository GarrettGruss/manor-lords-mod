# Proposal: find out if vassals work with AI opponents 0

Issue: #543.

## Why

The scenario_settings feature sets the guard value `vassals` to 0 and shows "vassals are not enabled" when `numGenericAILords` is 0. The wiki says `spawnNewAILord` works with AI opponents 0. The owner asked if the vassal handover works end to end in such a game.

## Question

With AI opponents 0, is a settled player region handed to a new friendly AI lord that owns it, builds, keeps peace and pays tribute? Does the guard value block anything? Do two vassals work?

## What Changes

- A test scenario `vassals-spike-noai` (observation, saves nothing) run on the fixture `playtest-noai` in game slots 1 and 2.
- Findings in `notes/vassals-without-ai-opponents.md`, with a recommendation about the warning.

## Non-goals

- Any mod code change. The recommendation is not implemented here.
- Any save call.

## Capabilities

### New Capabilities
- None. This is a spike (`skip_specs`).

### Modified Capabilities
- None.

## Impact

- Notes, one test scenario and wiki facts. No mod code change.
