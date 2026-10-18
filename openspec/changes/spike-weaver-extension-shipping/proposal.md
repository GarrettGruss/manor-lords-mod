# Proposal: decide and ship a weaver plot extension

Issue: #230. Legacy source: `docs/harness/31-burgage-extension/README.md`. Legacy issue: #230 (awaiting user).

## Why

The spike of spec 31 is done. A new extension number is not possible with data, because the extension type list is native. A weaver in an existing slot (the tailor, Type 6) works: Lua sets the job and the recipe, and a Meshy shed replaces the slot mesh. The recommendation and the cost estimate are in the legacy README ("Recommendation").

The owner must decide if a weaver ships, and which slot it takes. Some real-game checks are still open.

## What Changes

- The owner decides: ship the weaver in the tailor slot, use another slot, build a stand-alone weaver building instead, or stop.
- Open checks run: plot panel text and icon, a save and load round trip, several plots, the texture look, and a check by the owner.
- If the owner approves: a mod feature that sets the job and the recipe after every load, and ships the pak.

## Non-goals

- A new extension number. It needs native code and is out of reach.
- Game design text. The owner writes it in `docs/mod/M00-invasion-mod/`.
- Calling a save function outside the guarded action `save_game`.

## Legacy folders

- `docs/harness/31-burgage-extension/` (notes: `data-model.md`, `new-extension-number.md`, `weaver-reskin-recipe.md`, `custom-model.md`).
- `docs/harness/33-meshy-materials/` (texture fix).

## Capabilities

### New Capabilities
- None yet. This change is a spike with a decision (`skip_specs`). A delta spec for the mod feature is written when the owner approves shipping.

### Modified Capabilities
- None.

## Impact

- Pak `mod/HarnessActions/paks/weavermesh_P.pak`, probe `probe_extension.py`, commands `master_artisan`, `master_artisan_set`, `plot_upgrade` (living spec `harness/building-commands`: unsafe commands).
- If shipped: a new mod feature and a `DT_Upgrades` row edit in the mod pack.
