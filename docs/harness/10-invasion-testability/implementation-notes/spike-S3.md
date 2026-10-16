# Spike S3: observation of units

Date: 2026-10-10. Runs: probe-s1-a to d (crash search), probe-s2-a, probe-s5-a, chk-telemetry.

## Question
Which properties tell side, type, state, position, health and carried goods of a unit, and what does a census cost?

## Method
Lua module `mod/shared/HarnessUnits` (`census`, `counts`, `unitsOfSide`, `register_telemetry`), command `units_census` (HarnessActions), Python helpers `harness/runlib/units.py`, action `ctx.actions.units_census(sample)`. Telemetry: set `HARNESS_TELEMETRY_UNITS=1` before the launch and each sample gets `custom.units` (counts, about 10 ms). Verified in run `chk-telemetry` (4 samples with `custom.units`).

## Property map (jmap `SMUnit`, read in the game)
| Need | How | Status |
|---|---|---|
| side | no owner on the unit. `assignedSquadID.Value` -> the squad list `commandedSquads` of each `PawnCPP` -> `isMainPlayer`, `isBandit`, `isAI`. No squad = `civil` | verified: bandit 18 at the start, villagers civil |
| raiders versus bandits | both are side `bandit`; no field separates them | not possible |
| role | `currentUnitRole` (EUnitRole): raiders and bandits are `Soldier`, villagers `Husband` | verified |
| unit template / type | `unitTemp` (Name) reads `None` for raiders | not possible |
| squad type, control (fleeing, engaged) | `Squad.squadType`, `Squad.Control`. `PawnCPP:getSquadByID` returns the struct and **ended the game** (3221226505), and `GetSquadUnits` returned 0 members | not possible |
| state | `dead` (bool), `morale` (1.0 for all), `combatExperience` (0 for all, read only) | verified (read) |
| position, region | `realPos` (Vector), `currentRegion` -> `regionName` | verified |
| health | no hit point property exists on `SMUnit` | not possible |
| carried goods | `ItemsLooted` (Int) on the unit, and `Inventory` (Array of Good, empty on raiders) | `ItemsLooted` read and written, see S5 |
| per-squad data | squad size and centre are computed from the units of one `assignedSquadID` | verified |

`ItemsLooted` lives on `SMUnit` (IntProperty). Natural raiders reached 4 to 5 per unit (53 to 69 in total for 18 units one to two days after arrival). Its unit (items or silver value) is unknown.

## Cost of one census
| Units | ms |
|---|---|
| 189 to 240 | 8 to 25 (first call 25, then 9 to 14) |
| 310 to 420 | 12 to 17 |
The bridge round trip is separate: about 0.1 to 0.2 s per command.
Output size: counts, up to 16 squad rows and at most 30 sample rows (default 0).

## Bug found
A crash with exit code 3221226505 at the first census (run probe-s1-a/b) was `getSquadByID`; the helper does not call it any more. One more crash (probe-s1-c) happened after the last unit was read and did not repeat in later runs (more than 15 census calls). Cause not found; if telemetry units is on and the game ends, suspect this.

## Verdict
partial. Method verified for side (player, ai, bandit, civil), role, position, region, state dead, loot, counts and cost. Not possible: unit type or template, raider-versus-bandit split, health.
