## Why
Issue #557. Owner playtest (2026-11-04), screenshot of the Public Order tooltip:
1. `Manor +10` shows, and is applied to the order, when the manor is not built.
2. The up arrow of a positive row (`Manor +10`) is dark red, the same red as the down arrow. A positive row should have a green arrow like its green `+10` text.

## What changes
- The manor term of the order tick counts only when the player's manor is built (not a construction site). With no built manor the manor term is 0.
- With a manor term of 0 the tooltip shows no `Manor` row.
- The arrow of a row is green for a positive value and red for a negative value.

## Decisions (lead's defaults, the owner can correct them)
- "Built" uses the rule of the contracts feature: the first manor module of `HarnessManor.manor_state()` with `built = true`. A construction site does not count. If the manor state cannot be read, the manor counts as not built, and the tick logs a warning.
- The tech tree bonus `order_bonus` still applies without a manor. The tooltip does not show it as its own row (it never did: it is part of the `Manor` row). So the `Manor` row shows `base term + order_bonus`, and it shows when that sum is not 0. Showing the tech bonus as its own row is left to a later change.
- The tick record gets a seventh field `manor_built` (true or false) for the telemetry and the tests.

## Impact
- Spec `mod/bandits`: one MODIFIED requirement (the tick).
- Spec `mod/order_tooltip`: one MODIFIED requirement (rows and arrow colour).
- Code: `mod/InvasionMod/Scripts/features/bandits/`, `mod/InvasionMod/Scripts/features/order_tooltip/`.
