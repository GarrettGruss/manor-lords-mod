# Proposal: Spike public order factor

Issue: #403.

## Why
Owner idea (chat, 2026-10-22): "for lowering public approval, there is one mechanic already in the game called unemployment that lowers order by 10%, and there is another mechanic from the manor that raises order by 10%. Potentially we could build a new pak object that lowers order."

Known facts:
- Writing `Region.Approval` from Lua does not hold. The game overwrites it between polls (`openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/open-items.md`).
- The feature `mod/bandits` writes `Region.publicOrder` each tick (`openspec/specs/mod/bandits/spec.md`).
- `Region` has `summedApprovalFactors`, `summedPublicOrderFactors` and `publicOrderMemory` (legacy-15 `homeless-rebellion.md`, legacy-02 `jmap-findings.md`).
- A pak can add data table rows (spec 29, `DT_UnitTemplates`) and new assets (skill `harness-pak-mod`, `docs/wiki/workflows/pak-mods.md`).

A game-native factor would hold and show in the order tooltip. This spike finds out if one can be added or toggled.

## What Changes
- Find where the order and approval factors (unemployment -10%, manor +10%) are defined.
- Test whether a pak can add a factor row, or an effect that applies an existing negative factor.
- Test whether the mod can switch such a factor on and off at run time.
- Check the order tooltip, and save/load persistence.
- Write results to `notes/`, end with a recommendation and a follow-up change.

## Non-goals
- Building the follow-up feature.
- Changing `mod/bandits` or other features.
- Any save call outside the guarded harness action `save_game`, which needs a fresh backup and the owner informed first (CLAUDE.md, Safety).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None. A spike records findings only.

## Impact
- Static search of extracted data in `modtools/work` and the jmap/usmap files. No game needed.
- Real game runs, one at a time, single-player, with `--pak`. Each run id goes into the notes.
- Pictures go in `evidence/`, each listed with its test scenario and run id.
- Never print or commit the AES key.

## Owner decision (2026-10-23)
- The mod keeps its own order value `mod_order` (internal state).
- Route A (tested first): after each game recompute, write the region public order = game value + `mod_order`, every tick. Check that the shown value and the game effects follow. Result: `notes/tick-write.md`.
- Backup, route B (only if A fails): overlay a mod bar or number on the game's top bar that shows the mod order. Not built now, only recorded.

## Owner decision (2026-10-23, after the tick-write test): accept route A
- The mod overwrites the region `publicOrder` every tick with its own value. The mod keeps `mod_order` and the last game value itself.
- The effects of order are applied in mod code. This is a separate later change.
- Flicker (short 0 and 100 transients, about 12 percent of samples) is accepted as a risk.
- Route B (overlay bar) is not needed now.
