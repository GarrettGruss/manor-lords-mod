# M13 iteration 03: retinue-squads

Branch: `feat/M13-manor_stronghold-03-retinue-squads`. Issue: #215 (follow-up of iteration 02).

## Goal
Retinue men above the native limit of 12. The native hire cannot go above 12 (iteration 02). Try a mod-owned hire without the mouse.

## Routes tried
1. `PawnCPP:InitializeEmptyRetinueSquad(Region)`: the bridge could not pass the region object (push_objectproperty error, run `20261018-141330-93b7`). Not pursued: an empty squad has no way to be filled from script.
2. `RTSMultiEngineCPP:spawnArmy` with the player pawn as owner and template `retinue_tier1`: works. One squad of 36 player-owned men (role Soldier). Used.
3. Data in a pak: not possible. The 12 and 24 limits are constants in the game code (note `larger-formations.md`); only a DLL patch changes them.

## Changes
- `manor_stronghold/squads.lua`: the mod pays `squad_men * hire cost` (36 x 50 = 1800 silver), spawns the squad beside the manor, keeps the squad ids and counts the living men.
- Rule (TBD): each 12 of the retinue bonus allows one extra squad (`bonus_per_squad`). One tree node (+12) allows one squad of 36.
- Commands `retinue_squad_hire`, `retinue_squad_state`. Scenario `manor-stronghold-retinue-squads`.

## Acceptance criteria
- S1: no squad without the bonus; the hire is refused.
- S2: Militia Rights allows 1 squad.
- S3: the squad has 36 living men; with the 5 bound men the retinue is above 12.
- S4: the men are player-owned (census side player +36).
- S5: a second squad is refused.
- S6, S7: Brigands (18) attack; some bandits die; at least 20 of 36 men survive.

## Result
Works. Runs `20261018-141824-1038` and `20261018-142051-8932` pass (36 of 36 men alive after the fight, bandits killed). Probe run: `20261018-141330-93b7`.
Limits: the squad size is the template size (36), not a free number. The squads are not saved by the mod (mod state does not keep the squad ids; a loaded game has the squads from the game save only if the game keeps them: not tested). The men are not bound to the manor and are not in the native retinue editor.
Notes: `../implementation-notes/iteration-03-retinue-squads.md`.
