# Proposal: sync specs with the click hooks

Issue: #266. Branch: `docs/sync-specs-with-click-hooks`.

## Why

Legacy spec 34 (#254, widget click hooks) was finished after the living specs were written (`backfill-living-specs`). It changed two behaviors:
- The scheduler tick is 100 ms again. The user confirmed (2026-10-18) that 100 ms is correct, because a 50 ms tick crashed the game: it broke the Lua state after about 3 minutes with a menu open.
- Menu clicks are hook events of a click button, not polled presses with a cooldown.

Three living specs still describe the old behavior, so they are not true on `main`.

## What Changes

- `mod/core`: the scheduler tick is 100 ms, and it must not be faster.
- `mod/tech_tree_widget`: clicks are `OnClicked` hook events through `HarnessClickHooks`, handled once on the next tick. Remove the 0.4 s cooldown and the 50 ms poll. Two checks now exist (`tech-tree-widget`, `tech-tree-widget-clicks`).
- `mod/raid_widget`: the difficulty click is a hook event. Remove the press-and-cooldown rule.

## Non-goals

- No code change. The code on `main` is already right.
- No new capability for the shared module `HarnessClickHooks`. The widget requirements describe the behavior the player sees.
- No new rule for legacy work that changes behavior. That is a separate proposal.

## Legacy folders

`docs/harness/34-widget-click-hooks/` (read-only source).

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `mod/core`: the scheduler tick.
- `mod/tech_tree_widget`: how a click reaches the menu.
- `mod/raid_widget`: how a difficulty click reaches the menu.

## Impact

- Changed: three living specs, through the archive. `CHANGELOG.md`.
- This change has nothing to build, so it is a single pull request (gate rules of #264/#265).
