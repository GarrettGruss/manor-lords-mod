# M12 iteration 01 and 03: findings

## Settlement level
`Region.settlementLevel` of the player region is a plain number. `set_settlement_level(n)` (cheat manager) sets it. Runs: level 1, 2 and 3 were set and read back by `tech_tree_state.settlement_level` within one poll or at the next command.

## Militia units have no readable template
`unit.unitTemp` reads `None` for every unit. So the militia rule cannot use the template name.
- Side comes from the squad map of HarnessUnits (`unit.assignedSquadID.Value` to the pawn that commands the squad).
- Role: the squad of the saved game that holds the player militia (squad 27 in run 20261018-072546-6f73) has units with `currentUnitRole` 0 (Husband) and 2 (Son), 20 units. Squads that `spawnArmy` makes for the player (spearMilitia, retinue) have role 5 (Soldier).
- So the rule is: a unit in a squad of the player pawn with role Husband or Son (`unit_balance.militia_roles`). Militia raised from villagers match. Test squads from `spawn_units` do not (role Soldier). Mercenaries and retinue are not affected (TBD, playtests).

## Armor interaction
M05 sets `def` and `block` of unarmored units to 0. A multiplier on 0 stays 0. So Veteran Levies (militia defence +10 percent) only changes armored militia. The militia factor scales from the values the mod saw after the M05 write.

## Effects
- Public Order bonus: the target order is `clamp(natural + bonus - debuff)`. Real game: natural 100, approval 40, debuff 60: order 40; with Martial Law 50; with Iron Hand also 75.
- Approval bonus does not write `Region.Approval`. It only lowers the debuff. Reason: the game recalculates approval from its own sources and would overwrite a write.
- Buy-back price: `ceil(families x 10 x 1.0 x tech factor)`. Real game with Iron Hand: 2 families cost 25.
- Garrison squads for Fear of the Lord: the number of squads in `playerRef.commandedSquads` (TBD; M13 may refine).

## ModState
A string value allows only `A-Z a-z 0-9 _ . -`. The unlocked ids are joined with dots, so a node id may not contain a dot (the loader refuses it).

## Runs
See the iteration file.
