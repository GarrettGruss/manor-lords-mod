# Spec 29: Custom units (spike)

Status: DONE (2026-10-18). Issue: #178. Branch: `feat/29-custom-units-spike`. Notes: `implementation-notes/`. Recommendation for M00: `implementation-notes/recommendation-for-m00.md`.

## Goal
Find out whether the mod can add two new unit types:
1. **Hand cannon unit:** an early handgunner squad (Hussite "píšťala"). A ranged foot unit with high armor pierce, slow reload and short range.
2. **War wagon (Wagenburg):** a mobile wagon that blocks movement and shelters ranged units, or the closest feasible stand-in.

Both were cut from M00 as technical limits (decision 7: no handgunners; Factions: war wagons left out). This spike decides if they can come back.

## Non-goals
- New 3D models or animations in this spike (M00 out of scope for version 1). Reuse existing meshes, items and icons.
- Balance. Only "it exists, spawns, fights and does not crash".
- Player recruitment UI beyond a check of what the native recruit screen shows.

## Known facts (doc scan, 2026-10-18)
- Changing stats of existing templates is proven: live Lua writes (spike S7 `maxSize`; spec 25 `DT_Items` def and block; spec 28 and M05 live `SMUnit` writes).
- New rows are proven only for `buildingStats` and `DT_Upgrades` (spec 23). A new `DT_UnitTemplates` row is untested. Its row names are strings, not numeric ids.
- `DT_UnitTemplates` was never exported to JSON here. Another mod (LargerFormations, spec 13 `larger-formations.md`) replaces the whole table in a pak.
- Spawning works for 14 existing templates by name (M05 iteration 02).
- Recruit limits and the recruit menu look like native code (spike S7, spec 16).
- Ranged units exist (bow and crossbow militia, mercenary crossbowmen). Siege or vehicle units are not known to exist.

## Plan
### Part A: custom unit row (hand cannon)
1. Export `DT_UnitTemplates` and `DT_Items` to JSON (pak tooling, skill `harness-pak-mod`). Record the row layout: equipment arrays, weapon item ids, ranged fields (range, reload, projectile), size, icon.
2. Clone `crossbowMilitia` as `handCannon` in a pak (`--pak`). Change one visible stat and the weapon item. Add a new weapon item row cloned from the crossbow with higher `armorPierce` and `att`, lower rate of fire.
3. Check the row loads (`datatable_rows`, `datatable_read`, no soft-object reads through the bridge).
4. Spawn it from Lua (`spawn_units` with the new name; `spawnArmy`). Check squad size, equipment, that it shoots, and combat against militia (short A/B, N >= 5).
5. Look for a projectile or visual option: an existing projectile or effect that reads as a gun (smoke, sound). Record what exists; do not make new assets.
6. Check whether the native recruit screen lists the row.

### Part B: war wagon
1. Search the game data and class dump for wagons, carts and vehicles: trade carts, ox carts (spec 18 ox shed hitch work), siege objects, `Battlefield` and formation classes, placeable obstacles.
2. Test the closest stand-ins in order:
   - a spawned cart or wagon actor that blocks unit movement (collision);
   - a placeable obstacle or palisade piece placed by Lua near a squad (spec 14 wall notes: do not destroy game-owned actors);
   - a squad with a "wagon" role: high def and block, slow, holds position, ranged units behind it.
3. Record what moves with an army, what blocks pathing, and what crashes.

## Open questions
1. Does the game accept a new `DT_UnitTemplates` row name at load, and can Lua spawn it?
2. Which fields drive ranged combat (range, reload, damage), and are they in the template, the item, or code?
3. Is there any vehicle or movable obstacle class the AI and pathing respect?
4. Can a new unit be recruited by the player, or only spawned by the mod?

## Acceptance criteria
- A1: a verdict (proven / partly / blocked) for each of: new unit row loads, spawns, fights, is recruitable, has a gun-like look.
- A2: if the row spawns, an A/B of `handCannon` against `crossbowMilitia` (N >= 5) with run ids.
- A3: a verdict for the war wagon with the best stand-in found, and run ids.
- A4: notes in `implementation-notes/` (one file per topic), and a recommendation for M00 (bring hand cannons or war wagons back, or keep them out).
- A5: no game crash left unexplained; the AES key is never committed.

## Results (2026-10-18)
| Question | Verdict | Evidence |
|---|---|---|
| A1 new unit row loads | proven | `part-a-row-layout-and-load.md`, run `20261018-110301-5a1b` |
| A1 spawns | proven (32 units) | same |
| A1 fights | proven | `part-a-ab-results.md` |
| A1 recruitable | blocked by data alone (5 fixed recruit cards); widget pak or `unitType` rewrite untested | `part-a-gun-look-and-recruit.md` |
| A1 gun-like look | blocked (crossbow model; gun sounds and smoke exist but are not connected by data) | same |
| A2 A/B hand cannon against crossbow, N=5 | hand cannon much stronger vs Brigands (p 0.008); duel inconclusive (p 0.33); suite `20261018-110435-6c0f` | `part-a-ab-results.md` |
| A3 war wagon | vehicle blocked; stand-in squad `warWagon` spawns and fights (runs `20261018-115406-6f39`, `20261018-115541-0937`); spawned carts do not touch the path obstacle list | `part-b-war-wagon.md` |
| A4 notes and recommendation | done | `implementation-notes/` |
| A5 no unexplained crash | no crash in any run; AES key not committed | run summaries |

Answers to the open questions: (1) yes, a new row name loads and spawns. (2) Range, damage and armor pierce are item fields, not template or code. (3) No vehicle class that pathing respects. (4) Not recruitable by data alone.
