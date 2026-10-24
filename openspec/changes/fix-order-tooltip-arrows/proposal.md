## Why
Issue #462. Every mod row in the Public Order tooltip shows the game's small red down arrow, also for positive values such as `Manor +10`. The game shows an up arrow for positive factors.

## What changes
- A positive mod row shows an up arrow. A negative mod row shows a down arrow.
- How the arrow is switched (native field, brush copy or rotated image) is found in the implementation and recorded in `notes/`.

## Impact
- Spec `mod/order_tooltip`: one MODIFIED requirement.
- Code: `mod/InvasionMod/Scripts/features/order_tooltip/`.
