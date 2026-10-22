# Spike 1.1: battle marker, unit distance and goods removal

Question: how does Lua read the battle marker and the distance of a unit to it, and how does it remove goods from a store without a crash?

## Method
- Run `spike276-a` (kept open, base fixture, bridge client from Python) and run `spike276-c` (hidden test scenario `harness/scenarios/spike_raid_baron_steal.py`, verdict pass, no crash).
- A baron lord (`spawn_ai_lord`, war, `lord_spawn_army` spearMilitia at dx 6000, `lord_challenge`) marches to a challenge. The scenario reads the marker and the squad positions each game day for 6 days, and removes 10 goods a day from one store with the guarded action `sack_goods`.

## Findings
1. **Battle marker.** The marker is the challenge `Center`. It equals the location of the `battlefield_BP_C` actor in `challenge.Battlefield` (21 such actors on Jagged_Cliffs). The command `lords_state` returns both (`center`, `battlefield_at`). Runs `-a` and `-c` gave the same place (-17065, -24729, battlefield_BP18). Assert "center equals battlefield actor place": true.
2. **Unit distance.** Read `SMUnit.realPos` (a Vector X, Y, Z), as the raid tracker already does (`world.read_units`). `lords_state` gives the squad center (`x`, `y`) and `distance_to_player`. Distance is `hypot(dx, dy)` of the X and Y.
3. **Unit of the distance.** The unit is the Unreal unit. A `lord_spawn_army` call with dx 6000 put the army 5999 units from the player pawn (pawn -37635, -53829; army -31636, -53829). 1 unit = 1 cm is the Unreal default, so 300 m is 30000. Not checked against a known length in meters (open).
4. **How far the army stands.** The army starts 32000 units from the marker. In run `-c` its squad center was 20125, 10551, 5319, then 14400 to 14500 from the marker for the fight (days 4 to 6). In run `-a` the squads of a lord stood about 14000 units from the center. So a threshold of 30000 only counts units at the spawn or on the march, not a unit in the fight. The owner must choose the threshold with this in mind (open question 3 of design.md).
5. **Remove goods.** `SMBuildingMaster:consumeGoodNoCheck(good)` removes one unit (spike S6; the mod already uses it in `world.plunder`). In run `-c`, 6 calls of `sack_goods` (10 units each, from storehouse id 2147463894, good 216) lowered the store by exactly 10 each time, with no crash. The same call on run `-a` store 2147463915: 72 to 62. All 6 asserts "day N: the store lost 10": true.
6. The mod command `world.plunder` takes goods from the store that holds most, from `region:GetBuildings()` stores. This list includes the manor (type 98) when it holds goods. A tier filter is needed there (see note `game-raid-manor-spike.md`).

## Not verified
- 1 unit = 1 cm (the meters of the 300 m threshold).
- Per unit distance in the fight: only squad centers were read in the scenario (per unit `realPos` works in the tracker; a bridge read of 100 units at spawn gave 25000 to 40000 from the marker).
- How the game difficulty can be read (open question 1).
