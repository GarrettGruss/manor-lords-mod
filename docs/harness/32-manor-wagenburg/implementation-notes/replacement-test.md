# Replacement test: wagons for the wall, a tent for the keep (2026-10-18)

Spec 32, issue #233. Game 0.8.111, fixture `manor-closed` (a built manor with a closed palisade ring and a gatehouse, Hochweg), single player, `--slot auto`. No mouse, no eval, no save call. `allow_eval` was not changed.
Scenario: `harness/scenarios/probe_manor_wagenburg.py` (hidden). Keep flow: the helpers of `probe-manor-flow` (`manor_blueprint_add` type 57, `manor_planner commit`, spec 12 round 9).
New command `mesh_actors` (HarnessActions 58, `HarnessWalls`): read only, the owner class and position of the actors whose static mesh matches a name part.

## Runs
| Run | Pak | What | Result |
|---|---|---|---|
| `s32-1` | none | first control, speed 3 | pass; the track was too coarse (first sample already at the gate). Not used. |
| `s32-2` | none | control, speed 1 | pass |
| `s32-3` | `s32wall` | wall mesh swap, same scenario | pass. Wagons show on the whole ring. |
| `s32-4` | `s32wall` + `s32keep` | `probe-manor-flow`, keep type 57 mouse-free | pass. Keep built on day 12, `getModularGarrisonLimit` 24 (as the vanilla keep of spec 12 round 9). Wagon ring and a new blue-grey object next to the manor house in `end.png`. |
| `s32-5` | none | keep mode plus path test | fail: `TimeControlError`, the clock did not restart after the keep build (before the track). The keep was built on day 9. |
| `s32-6` | none | same, with `popups()` | same failure. Fix: option `HARNESS_PATH=0` skips the path test after a keep build. `start.png` shows the vanilla wooden keep (control). |
| `s32-7` | `s32wall` + `s32keep` | keep mode, path off, close screenshots | pass. Keep built on day 9. |
| `s32-8`, `s32-10` | none | path control | pass (see `pathing-test.md`) |
| `s32-9`, `s32-11` | `s32wall` | path with wagons | pass |

## Wall: wagons replace the palisade pieces (WORKS)
- The pak replaces `SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam` by asset path. No row, Blueprint or Lua change.
- All 56 built pieces show as wagons along the wall line, wheels on the ground, in a continuous line. Screenshots (git-ignored): control `runs/s32-2/screenshots/ring_c.png` (dark palisade), wagons `runs/s32-3/screenshots/ring_c.png` and `runs/s32-9/screenshots/ring_c.png`, close `runs/s32-7/screenshots/keep_z3000_c.png`.
- The wagon is 240 cm long and 119 cm wide; the palisade piece is 219 cm long. In the pictures the wagons stand nose to tail, and some touch or overlap at the corners.
- The wagons are 1.1 m high; the palisade was about 3.9 m high. The wall reads lower. A taller wagon (cover, shields) or a non-uniform scale would fix the height. The collision does not change.
- No crash in 11 runs. The ghost pieces and the planner road use the same mesh and also show wagons.

## Keep: a tent replaces the keep (WORKS)
- The pak replaces `SM_MERGED_C_SG_Manor_MainTower_Lv1_New`. The keep was added mouse-free at (11000, -52200) with `manor_blueprint_add` type 57 and `mesh` set to the vanilla keep path (the manor has no keep blueprint to copy the mesh from, spec 12 round 9).
- The planner ghost, the construction site and the finished keep use that mesh. After 9 game days the keep stood as a 6 m x 7 m tent (`runs/s32-7/screenshots/keep_z3000_c.png`, `keep_z1200_c.png`). The control builds the wooden Lv1 keep (`runs/s32-6/screenshots/start.png`).
- Garrison limit 24 after the build (`s32-4`): the native keep rule still works with the tent mesh. (With the Lv3 tower mesh it did not, spec 12 round 9: the mesh key matters, here the key `MainBld_167` is unchanged.)
- The tent is smaller than the keep (7 m against 18 m high). Palace (row 98) was not changed. It is the manor house; a command tent would fit it better than the keep. Same recipe, one more model.

## Not done
- Gate (row 95) and outer tower (row 472): same recipe, not run. The vanilla gatehouse shows in the wagon ring (`ring_c.png`).
- A closed gate, damaged wagons (hit points 15 per piece) and a fire were not tested.
- The grey colour of the wagons (see `meshy-assets.md`).
