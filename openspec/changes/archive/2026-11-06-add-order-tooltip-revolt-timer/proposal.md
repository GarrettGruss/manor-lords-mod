## Why
Issue #586. The Public Order tooltip shows why the order has its value, but not what happens when it is low. The game's Approval tooltip shows a timer. The player of the mod sees no sign that peasants will revolt, or when, or why a revolt did not happen. The row `Left for banditry` also says that peasants leave, but they revolt.

## What changes
- Rename the row `Left for banditry` to `Peasants revolted` (tooltip text only; banners and logs keep their text).
- While the banditry timer runs (order under the threshold), the tooltip shows a revolt counter below the rows: `Peasants revolt in <N> days`. After the timer expired and the revolt was blocked, the counter shows the days to the next try (the next order tick). Without a timer, there is no counter.
- Below the counter, a text item `Revolt blocked: <valid> of <needed> armed homes` shows only when the revolt would be blocked (too few armed families, or no Outlaws pawn). When the revolt can happen, the item is not shown.
- The count of armed homes is cached for a few seconds, because it reads every home inventory.
- Spike first: can the tooltip show a text line with no value? If not, the items use the label and value shape of the existing rows (recorded in `notes/`).

## Impact
- Spec `mod/order_tooltip`: one MODIFIED requirement, two ADDED requirements.
- Spec `mod/bandits`: one ADDED requirement (a read-only revolt status for the tooltip).
- Code: `mod/InvasionMod/Scripts/features/order_tooltip/`, `mod/InvasionMod/Scripts/features/bandits/`, `config.lua`.
- The texts come from the owner request: "Peasants revolted", "Peasants revolt in N days" and "Revolt blocked: V of N armed homes". The owner may change them later in `rows.lua`.
