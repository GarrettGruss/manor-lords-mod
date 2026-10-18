# Recommendation for the Invasion Mod (2026-10-18)

Spec 30, issue #229.

## Short answer
Yes. A Meshy Wagenburg can be a military encampment in the game. Use host a (retarget the bandit camp row) for bandit camps. Use host c (a spawned actor) for camps in neutral or AI territory.

## Choice
| Need | Host | Why |
|---|---|---|
| Bandit camps look like a Wagenburg | a: row 100 `BlueprintPath` set to `BM_Wagenburg_C` | Works. Data only. The game's own spawn, the saved camps and the bandit counts keep working (s30-2 and s30-3 against control s30-4). |
| A camp in neutral or AI land that the mod controls | c: `World:SpawnActor` of the same class | Works in neutral and AI regions. Needs a respawn on load. No game logic (no owner, no units). Pair it with `bandit_spawn_at` for units. |
| A camp that the player builds | b: new row (block 4000 to 4099) | The row loads. Placement was not run here (needs the mouse). It is proven for other new ids in spec 18 and 21. |

## What it costs to ship
- One pak (3.4 MB now): the cooked `BM_Wagenburg`, `SM_Wagenburg`, one material and 5 textures. Smaller texture caps cut the size.
- One `buildingStats` row change (row 100) as a spec 22 patch in the mod pack (`data/<feature>/patches`). Host a needs no new row.
- Host c: a mod command that spawns the class (the harness command `encampment_spawn` is a test command), a saved list of places in ModState, and a respawn on load. About 100 lines of Lua.
- Art: 30 Meshy credits (about 0.60 USD at Pro) and 2 Gemini images. A new look needs a new try.
- Release gate: the Meshy license for a public release is still open (spec 21). The user must check the account terms first.

## Risks and open points
- The model renders light grey, not brown (see `meshy-model.md`). Fix the material before a release.
- The camp is one mesh. Wagons cannot be destroyed one by one, and units cannot use gaps.
- Bandit units spawn at the camp centre. Check that they are not stuck in the ring (collision of the mesh). Not tested.
- Host a changes every bandit camp. A mix (some tents, some Wagenburg) needs a second class or a hook.
- The camp of an invading army is not a building master. Host c is the only way for it.
- Spec 29 (war wagon units) has no notes yet. If it finds a vehicle class, a moving wagon could replace the static ring.
