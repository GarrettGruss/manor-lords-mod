# Proposal: Fix stale harness skill text

Issue: #53. Legacy source: `docs/harness/00-harness-overview/README.md` (roadmap status) and issue #53 (housekeeping from the review of specs 00 to 14).

## Why
Issue #53 lists stale text. Most of it is fixed. One item remains in the skills: `.claude/skills/harness-overview/SKILL.md` says "Spec 11 (parallel game slots) is proposed". Spec 11 steps 1 to 4 are built (`harness/game-slots`). The skill also points to the spec 00 status lines, which are legacy and frozen. The living specs hold the status now. The other #53 skill items are done (`harness-coverage` says 36 of 39; the modules are named in `harness-overview`; holding the game speed is described).

## What Changes
- Fix the sentence on spec 11 in `harness-overview`.
- Replace the pointer to the spec 00 status lines with a pointer to `openspec/specs/` and `openspec list`.
- Scan the other harness skills for the same kind of stale text.

## Non-goals
- Edit legacy docs (spec status lines, the roadmap rows, the A/B box of spec 09). They are frozen.
- Skills of the Invasion Mod.

## Legacy folders
`docs/harness/00-harness-overview/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None.

## Impact
Skill text only. No code.
