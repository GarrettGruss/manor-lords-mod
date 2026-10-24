## Why

Issue: #454. The mod keeps its own public order (mod order, feature `bandits`). The top bar shows it, but the Public Order tooltip still lists only the game's own factors, so the player cannot see why the mod order is what it is. Spike #422 (route B, owner accepted) proved that a hook on the tooltip widget can add rows with the mod's own text and colour.

## What Changes

- New feature `order_tooltip` (requires `bandits`). It hooks `BigTooltip_ApprovalAndPublicOrder_C:updateContents`. Each time the tooltip opens it adds one row (`approvalFactorWidget_C`) for each mod order term, and writes the mod order in the header sum.
- Rows (English, order points, colours as the game: red negative, green positive):
  - `Manor +10` (the manor term of the last tick, with the tech tree order bonus included);
  - `Homeless families -N` (N is the homeless term of the last tick, 5 for each family), only when N is above 0;
  - `Left for banditry +25`, shown from the leave until the next order tick.
- The header shows the mod order, for example `77%`.
- The native rows are hidden while the mod order is active, because they do not change the mod order.
- `bandits` gets one small read-only accessor `order_terms()` that returns the last tick terms and the leave gain.
- If the hook does not fire or a call fails, the tooltip stays native and the mod logs once. No error is raised.

## Open questions (with defaults)

- Hide the native rows? Default: yes (they do not affect the mod order, and a native "-10%" next to a mod order of 77% confuses). The owner may change it to keep them.
- How long does `Left for banditry +25` show? Default: until the next order tick. The owner may change it.
- Texts are plain English strings (no translation table).
- Before the first tick there are no terms: the tooltip shows only the header (mod order) and no mod row.

## Impact

- Specs: new capability `mod/order_tooltip` (ADDED). Reason: the feature has its own hook, its own widget code and its own tests, and the next order sources of other features (for example tribute) can add rows to it. `mod/bandits` is not changed in its spec (the accessor is an internal read).
- Code: new `mod/InvasionMod/Scripts/features/order_tooltip/`, a small accessor in `features/bandits/init.lua`, `feature_list.lua`, `mod.json`.
- Tests: fake-game tests for the row builder, a real run with the OS mouse hover (exclusive, needs a visible window).
