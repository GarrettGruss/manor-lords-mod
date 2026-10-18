# Recommendation for the Invasion Mod (2026-10-18)

Spec 32, issue #233.

## Short answer
Yes for a player Wagenburg. The manor can be reskinned: wagons for the wall, a tent for the keep. It keeps the real wall collision, the gate, the hit points and the manor rules. It costs two data-free paks and no Lua. No for a separate enemy camp: a manor belongs to a region owner, and the reskin is global.

## What works (runs `s32-3`, `s32-7`, `s32-9`, `s32-11`)
- Wagon wall: all wall pieces show as wagons. Units path as before (4 runs without a crossing, entry by the gate).
- Tent keep: the keep builds with the tent mesh and keeps the garrison of 24.
- Collision is native obstacle data that a built wall piece adds. The mesh is only a look.

## Use cases
| Need | Verdict | How |
|---|---|---|
| The player builds a Wagenburg manor (a Hussite-themed stronghold) | Works | Ship `s32wall_P.pak` and `s32keep_P.pak`. Every manor of the game then has wagon walls and a tent keep. Add a gatehouse and tower model for a full look (same recipe). |
| A separate camp the invaders or an AI lord holds, with a real wall | Not proven, probably blocked | The wall needs a manor build (builders, region manor). `maxInRegion` of the keep is 1 and the region manor is the player's. An AI lord with a manor and a wall was not studied. A mod actor ring has no collision (spec 14 and spec 30 host c). |
| Bandit camp look | Use spec 30 host a (row 100) | Data only, one mesh, no collision. |

## Cost to ship
- Art: 30 Meshy credits for each model (60 here), 2 Gemini images each, one UE import, one cook of about a minute, 3.3 to 3.6 MB for each pak. Gate, tower and palace: 30 credits each.
- Code: none for the look. `mesh_actors` and the probe are test tools.
- The Meshy license for a public release is still open (spec 21). The user must check it.

## Risks
1. The swap is global. A player who does not want a Wagenburg manor sees wagons too. A per-camp look would need a new wall type with its own row, which the wall tool does not offer (no native hook).
2. The manor is the player's stronghold: region manor, taxes, garrison. A camp for the enemy cannot use it without an AI-owned manor. Check what an AI lord builds before the Invasion Mod relies on this.
3. The wagons are low (1.1 m) next to the 3.9 m palisade. Gameplay is unchanged (collision is the same) but archers and the look differ. A taller model is cheap to make.
4. The Meshy materials render grey and blue-grey (not brown). Fix the material before a release (spec 30, 31 notes).
5. Not tested: a closed gate, defenders on the wall, wall damage and fire, performance with several rings, save and load of the manor with the pak removed (the pak must stay installed).
6. The pak replaces game asset paths. A game update that renames the meshes would break it silently (the vanilla look returns, nothing crashes).

## Next steps
1. User check in the real game by eye (the screenshots are agent captures).
2. Gate and outer tower models, and a taller wagon, if the Wagenburg manor is wanted.
3. Study an AI lord with a manor and a wall: who builds, where the wall shows, and whether the pak look reaches it. The same mesh swap would apply to it.
