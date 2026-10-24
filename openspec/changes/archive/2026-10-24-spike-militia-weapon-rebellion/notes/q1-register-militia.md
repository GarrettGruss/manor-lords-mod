# Q1: register a militia squad of spearmen from villagers

Fixture `playtest-noai`, run `spike-militia-1` (kept open, bridge from Python, raw eval enabled by a local edit of `UEBridge/scripts/settings.lua`, reverted at the end).

## Method
`PawnCPP:addMilitiaSquad(region, FName("spearMilitia"))` with the player pawn and the player region (Riesenbuckel). It is the call that the militia hotkey makes (legacy note `adaptive-militia.md`). `canAddNewMilitiaSquad()` was true before each call.
Counts came from `FindAllOf("SMUnit")` grouped by `assignedSquadID`, and `pawn.commandedSquads:GetArrayNum()`. No Squad struct was read.

## Result: TRUE, the units are the villagers (not spawned)
| Call | commandedSquads | New squad | Units in squad | Squad 0 (no squad, villagers) | Total SMUnit |
|---|---|---|---|---|---|
| start | 0 | - | - | 83 | 201 |
| 1st | 1 | id 19 | 10 | 73 | 201 |
| 2nd | 2 | id 20 | 6 | 68 | 198 |
| 3rd | 3 | id 21 | 4 | 70 | 204 |

- The total unit count does not change at the call: units move from squad 0 to the new squad. So the squad is made of existing villagers (men: roles Husband and Son).
- Squad size is limited by the available men (10, then 6, then 4). The village had 5 families and 15 residents at the start.
- `units_census` then shows side `player` with 16 units (10 + 6), role still Husband or Son (not Soldier). The squad is registered, not rallied.
- No unit was spawned and nothing was rallied.

## Not verified
The template name stored in the squad (the Squad struct is on the crash list). The function accepted `spearMilitia`.
