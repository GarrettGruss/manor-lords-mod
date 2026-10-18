# Proposal: add region state and a size limit to ModState

Issue: #273. Legacy source: `docs/mod/M01-mod_state/README.md` (iteration table row "02 region-state-and-limits", no iteration file).

## Why

ModState keeps values in the Tags of the player pawn only (iteration 01 of M01, built). The legacy spec plans a second step that is not built:
- State of one region (for example a vassal region) in the Tags of that region.
- A limit test: how many entries and how long they may be, and how long a save and a load take.

Open question 1 of M01 (the Tags limit) is still open. Spec 24 marks it open too. Features add keys with each iteration, so the limit must be known before the state grows further.

## What Changes

- ModState can open a region owner and keep `<mod>:<key>=<value>` entries in the Tags of that region.
- ModState fails loudly when a write would pass the tested limit.
- A limit spike measures the entry count, the entry length and the save and load time. Its note goes into `notes/` of this change.

## Non-goals

- Option C of spec 24 (a side file). It is decided only if the state grows past the Tags.
- Moving existing features (vassals, tribute) from pawn Tags to region Tags.
- Any save call. The mod never saves. Tests use the guarded harness action `save_game`.
- Tags of AI lords and buildings.

## Legacy folders

`docs/mod/M01-mod_state/` (read-only). Related: `docs/harness/24-mod-save-state/` (open size limit).

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `mod/mod_state`: region owner state and a loud limit check (new requirements).

## Impact

- Code: `mod/shared/ModState/ModState.lua`; tests in `harness/tests/`; test scenarios in `mod/InvasionMod/scenarios/mod_state/`.
- Wiki and CHANGELOG: the mod state page and `Unreleased`.
