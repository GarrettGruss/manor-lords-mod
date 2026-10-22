# Region unlimited flag (task 1.3)

Runs `20261021-051859-f8a3` (all property names of the player region) and `20261021-052220-1d6f` (all `Region` functions).

Result: no region flag for unlimited resources exists, as a property or a function. The only switch is `setProductionUnlimited(good)` (removes the production limit of a good) and `setProductionLimit(good, n)`. They switch cleanly both ways (run `20261021-052332-b91c`). If the game keeps the "finite or infinite" choice, it keeps it on the resource clump or the mine building, not on the region: not found yet.
