# Proposal: add the start sack for a plundered village

Issue: #274. Legacy source: `openspec/changes/archive/2026-10-16-legacy-m14-plundered-start/README.md` (iteration table row "01 start-sack", no iteration file).

## Why

The design (M00) prefers a start in a village that was recently plundered: ruins, a small and scared population and low supplies. The game has no start setting for it. The legacy spec plans to run the start sack once in a new game, with the sack tools that exist. M14 is not started. M00 decision 25 (2026-10-16) puts it out of scope for the first release. The user decided on 2026-10-18 that all open legacy work moves into changes, so the first step gets a change. This change stays in the backlog until the user starts it.

## What Changes

- In a new game the mod runs the start sack once: it takes a share of buildings, stock and people.
- A flag in ModState stops a second start sack after a load.

## Non-goals

- A start setting in the game start menu.
- The fallback of M00: a normal settler start with a raid story event in the first days. It can be a later iteration.
- Finite home resources (built in the feature `finite_resources`).
- Any rule that needs the first raid of M02.

## Legacy folders

`openspec/changes/archive/2026-10-16-legacy-m14-plundered-start/` (read-only). Related: `openspec/changes/archive/2026-10-15-legacy-26-game-start-settings/`.

## Capabilities

### New Capabilities
- `mod/plundered_start`: the start sack that runs once in a new game.

### Modified Capabilities
- None.

## Impact

- New feature folder `mod/InvasionMod/Scripts/features/plundered_start/` and `scenarios/plundered_start/`.
- It requires `mod_state`. It uses the sack tools that `sack_and_terms` also uses.
- Wiki and CHANGELOG.
