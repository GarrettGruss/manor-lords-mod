# Rich game detection without a hover (spike #550)

Runs (slot auto, fixture base, map Jagged_Cliffs, read only, no save call): `rg-funcs`, `rg-hook`, `rg-call`, `rg-widgets`, `rg-lairs`, `rg-deer2`, `rg-compare` (7 runs; `rg-deer` was a harness miss before the step was added). Probe: `harness/scenarios/probe_rich_game.py` (env `HARNESS_PROBE` = funcs, hook, widgets, lairs, deer, compare). Saves were backed up first (`backups/saves-20261101-rich-game`).

## Answer: NOT readable from Lua. Keep this verdict until a new idea appears.

## What was tried
1. Tooltip path (`rg-funcs`, `rg-hook`, `rg-call`).
   - The text sits in `MainUICPP_C.WhiteTooltipRT`. It is bound to the Blueprint function `MainUICPP_C:whiteTooltip` (fires about every frame; hook shows no args). The pawn has `PawnCPP:getSmallTooltip`, `updateTooltip` (native, also fires every frame).
   - Both are parameterless getters that read the object under the mouse inside native code. Called directly with no hover they return nothing (`getSmallTooltip` = empty array, `whiteTooltip` = None). Hook events carry no return value and no hovered object. No function takes a `ResourceNode` as argument, so the text cannot be built for a chosen node.
   - Hover in these runs showed no tooltip (cursor at the paw icon, text empty), so no text was captured with the hooks. The hook itself was installed fine.
2. Properties (`rg-compare`). All properties of the 4 deer nodes (with super) and their `ResourceZoneDecal` were read. The only differences are struct memory addresses. There is no count, max, herd size or rich flag. The node has one own function, `onPaperMapViewChanged`.
3. Managers (`rg-lairs`, `rg-deer2`).
   - No object exists for 12 animal class names (AnimalLair, AnimalCPP, SMAnimal, and others).
   - `RTSMultiEngineCPP:getDeerLairLocations()` (no arguments) returns 4 vectors. They equal the 4 deer node positions exactly. Positions only, no count or flag. The same list name fits `PawnCPP:doesPlacebuildingAffectDeerLair`, `AffectAnimalLairs`, `deerDecalMat`; these are placement checks, not data.
   - Other animal names on the engine: `getAnimalRoleFromGoodType`, `breedAnimal`, `SM_AnimalTraps`, `DT_AnimsetDeer` (livestock and animation data, no wild count).
   - No widget holds it: the paw icon over the area is not a `UserWidget` (53 widget classes listed, none about animals).
4. Rule on the 4 nodes: no separating readable value. Rich (Riesenbuckel, tooltip 17/28) and poor (Hochweg 12/16, Krumme Leite 14/18, Rangbachau 17/17) nodes are identical in every readable number (decal size 4500, scale 1, no clumps).

## Fallback ideas for a mod (not tested)
- Cheap proxy: nothing found. The max (28 vs 16 to 18) lives in native state.
- Read the text from the tooltip widget while the real mouse hovers (only possible in a harness run, not for players).
- Ask the owner whether rich game may be treated as "never rich" or as a per-game setting the player confirms.

## Not verified
- Hooks on `whiteTooltip` give no return value, so whether the pawn's `getSmallTooltip` returns the deer text during a hover is not known. The hover in `rg-call` produced no tooltip, so this stays open.
- Native C++ fields behind the node (not reflected), pak data tables for the map, and the map save file were not examined.
