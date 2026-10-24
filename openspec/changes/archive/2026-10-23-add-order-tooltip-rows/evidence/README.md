# Evidence: add-order-tooltip-rows

Test scenario `order-tooltip-rows`, run `20261024-024516-b286` (slot 0, fixture `base`, game paused, real mouse on the order icon).

| File | Shows |
|---|---|
| `tooltip-after-tick.jpg` | After a forced tick: header with the mod order, row `Manor +10`. No native row. |
| `tooltip-after-leave.jpg` | After a leave: rows `Manor +10` and `Left for banditry +25`, header 85%. |

Known look issues: the mod rows show the game's small red arrow (the arrow is an image in the row and is not changed), and the native `Lingering Memories +0% None` block stays.
