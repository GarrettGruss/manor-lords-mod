# M01: mod-state

Feature folder: `mod_state`. Lua module: `ModState` (shared module). This is a core module, not game design. Batch 1.

## Goal
Keep the values of the mod across a save and a load. All later features use it.
The player never sees it.

## Player rules
None. The player only sees that the countdown, loyalty, influence and the other values come back after a load.

## Current state
Not started. The design and the proof are done in harness spec 24.

## Proven building blocks
- Option A works: names in `Tags` of the player pawn and the player region survive a save and a load. `docs/harness/24-mod-save-state/README.md` (section Recommendation, module design).
- Tags evidence and the unusable fields: `docs/harness/24-mod-save-state/implementation-notes/persistence-tests.md`.
- Save and load hooks: `docs/harness/24-mod-save-state/implementation-notes/save-hooks.md`.
- The menu save keeps Tags (manual check passed 2026-10-16): `docs/harness/24-mod-save-state/implementation-notes/menu-save-check.md`.
- The stand-in contract for mod state: `docs/harness/10-invasion-testability/implementation-notes/mod-state-contract.md`.
- Shared module layout and pak rules: `docs/harness/22-mod-pack-layout/README.md`.

## Design rules (from spec 24)
- Entry format: a Name `<mod>:<key>=<value>`. Example: `invasion:raid_days=412`.
- API: `ModState.open(mod, owner)`, `state:register(key, default, kind)`, `get`, `set`, `flush`. Versioning with the entry `<mod>:v=<n>`.
- Pawn Tags hold global state. Region Tags hold state of one region.
- `open` runs again on `ReceiveBeginPlay` of the pawn after each load.
- No feature writes Tags by itself. No feature calls a save function.
- A bridge `set` of a `Tags` array crashes the game. Use a Lua `FName` write.

## Tunables
- Flush interval in game seconds (default: flush on each change).
- Key registry: one table per feature, in the feature `config.lua`.

## Dependencies
None. Every other feature that keeps values depends on it.

## Open questions
1. How many entries and how long can the Tags be? The limit test (many entries, long entries, save and load time) is open in spec 24.
2. Is a region Tags entry kept for a vassal region that the player settles and then loses?
3. When is option C (side file plus id) needed? Decide only if the state grows past Tags.

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | tags-module | `ModState` module on pawn Tags, with default state on a save that has no mod marker | not started |
| 02 | region-state-and-limits | Region Tags and the size limit test | not started |
