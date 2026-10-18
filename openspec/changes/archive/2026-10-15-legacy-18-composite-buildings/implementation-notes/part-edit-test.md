# Can Lua add or remove a part of a built master? (2026-10-13)

Question: spec 18, plan step 2. Method: new unsafe HarnessActions commands (version 38, module `HarnessParts`): `master_parts` (read only),
`master_part_add`, `master_part_remove` (modes `hide`, `destroy`, `unlink`). They need `HARNESS_ALLOW_UNSAFE=1`. Probe: scenario
`probe-composite` (hidden). Runs: `s18-plot-1`, `s18-plot-2` (fixture `burgage-start`, a burgage plot) and `s18-tent-2` (fixture `base`,
`settle_region` on the player region, then the new tent). Run `s18-tent-1` used a plot by mistake (env variable of the probe was not read
in the launcher). 4 launches, the game is closed. No save function was called.

## What the masters hold
- Plot (type 3): 44 to 46 parts, house mesh part first, plus 1 extension (`Type` 0) with 17 parts (31 on the base fixture plot).
- Tent (type 87), made by `settle_region`: 17 parts, no extension, 3 families. First part mesh `SM_MERGED_C_HuntersTent`, then `SM_MERGED_c_campfire`,
  `SM_MERGED_sittingLog`, ... Every part is class `SMBuilding`.

## Results (same on plot and tent)
| Action | Result |
|---|---|
| Append a new `SMBuilding` to `buildings` | WORKS as a list change: spawn of class `SMBuilding` (class of part 1) with the master as owner, `actor.buildingMaster = master` accepted, the count went 17 -> 18 (tent), 45 -> 46 (plot). The count and the part stayed after 2 game days. No crash. |
| Give the new part a mesh | NOT DONE. A bare `SMBuilding` has no `StaticMeshComponent0`; `AddComponentByClass` did not give a usable component. So the new part is an invisible actor. Not seen on screen. |
| `hide` (SetActorHiddenInGame) | Accepted, part stays in the list. Visible effect not checked on a screenshot. |
| `unlink` (empty the array, append the others again) | WORKS: count 18 -> 17. `RemoveAt` does not exist on a TArray in this UE4SS build. The actor is not destroyed. No crash. |
| `destroy` (`K2_DestroyActor`) | Call returns, but the part stays valid and in the list; in one run its location read as 0,0,0. Not a clean removal. The game seems to keep these actors. |
| Master after the changes | `IsConstructed` stays true, families unchanged, no change after 2 game days. |

## Verdict
- A mod can edit the part list of a built master in memory (append, unlink) without a crash. The master does not react: it has no hook that
  rebuilds visuals from the list. Visible parts need a mesh component on the new actor, which was not solved.
- The part list is not what defines function. The tent holds families through `occupantFamilyIDs` and `buildingFunction` 7, not through parts.
- Caveat: not checked on screen, not checked after a save and load (nothing may be saved by the harness; the game's own load would drop
  actors that the save does not know).
- Next, if wanted: spawn the part from a real `BM_*` class (a class that has the mesh component) instead of the bare `SMBuilding`.
