# Lead 1.1: real loot (R3)

Probe: test scenario `probe-lead-loot` (fixture `manor-bailey`, slot 0). Command `lead_unit_gear` (`SMUnit:GetEquippedID(slot)`, slots 0..3).

## Result
- `GetEquippedID` works on a living unit. Each call gives a plain number (an equipped id). No call raised an error.
  - Run 20261021-041104-4698: 1 bandit squad of 32 `spearMilitia`: 128 of 128 slot reads were numbers (`gear_numeric_alive` 128, `gear_other_alive` 0). Ids seen: slot 0 `52` or `163`, slot 1 `133` (one unit `312`), slot 2 `271` (one `157`), slot 3 `273`. The first unit differed (a leader: `52 312 157 273`).
  - Run 20261021-041325-0a68: the same squad fought 3 player squads. The alive count fell 32, 26, 19, 15, 15 over 24 game seconds. `dead_*` stayed 0 at every read, and `gear_numeric_*` fell with the units (128, 104, 76, 60, 60).
- A dead unit is not readable. A unit that dies leaves the unit list at once: no `SMUnit` with the `assignedSquadID` of the squad is left, and `dead` was never true (`units_dead` 15 after the fight and 0 units after `bandit_kill_squads`). So the read must happen BEFORE the death. A loot feature has to remember the gear of a squad while it lives (for example at spawn or at each raid tick), then pay out when the squad dies.
- `ItemsLooted` is 0 on every unit.
- Goods move: `manor_put` (`addToInventory`) gave 5 of good 1 (stock 0 to 5, `manor_stock_gain` 5).
- Not found: the map from an equipped id to a good or item row. That needs the item data table (soft object fields: not read through the bridge, see Safety).

## Risks
- Equipped ids are numbers from an unknown table. A loot feature needs that map first.
- The probe killed the squad with `bandit_kill_squads` and also watched a real fight. In both cases the dead units disappear at once.

## Does a mod feature need it?
Only the idea "bandits drop loot in proportion to their gear". No feature in the design needs it now. Keep the command as a tool. Drop the lead unless the owner asks for gear-based loot.
