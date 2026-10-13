# Unit steering: move one squad to a chosen point (issue #59)

Date: 2026-10-13. Game 0.8.111, fixture `base`. Runs (in `runs/`, not in git): `s59-a` to `s59-h` (8 launches, no crash, no save call).
Code: `mod/shared/HarnessSteer/HarnessSteer.lua`, HarnessActions version 40, probe `harness/scenarios/probe_steer.py` (hidden).

## Question
Can a mod move a squad (player, AI lord or bandit) to a chosen point from Lua?

## Result
- PLAYER squad: YES, with one real OS right click. The mod puts the cursor over the chosen world point, and one right click orders the selected squad. Run `s59-h`: squad 32 started 1547 units from the point and stood 127 units from it (formation spacing) 5 game seconds later.
- A pure Lua order (no OS click): NOT FOUND. Calls from Lua do not move the squad (see the table).
- AI and bandit squads: not tried again. Spec 15 part 3 showed that `formALineArmy` does nothing for them, and the AI re-targets them. The player path needs a squad that the player pawn commands.

## Method and numbers
| Run | Call | Result |
|---|---|---|
| s59-b, s59-d | `steer_move`: `PawnCPP:formALineArmy({squad}, line, "Line", line)` on the owner pawn of a spawned player squad, point 4000 units away | The call is accepted. A hook sees the right arguments (line A=(-33872,-53910) B=(-33872,-53310)). The squad does NOT move: distance 4000, 4002, ... 3996 over 60 game seconds. So `formALineArmy` is not the order. |
| s59-e | `steer_select` (`PawnCPP:selectSquad`), then a real right click at a window fraction (0.62, 0.45) | The squad walks to the clicked terrain point: distance 2803 -> 53 within 5 game seconds. Hooks on 14 functions (`formALineArmy`, `RMB_BP_pressed/released` of `PawnCPP` and of the `MyPawnCPP_BP3` class, the `InpActEvt_RightMouseButton` events, `SetPushStance`) saw NOTHING from the click, only our own `selectSquad`. The order runs in native code, outside `ProcessEvent`. A replay of hooked calls is therefore not possible. |
| s59-f, s59-g | `steer_cursor` (`PlayerController:ProjectWorldLocationToScreen` then `SetMouseLocation`), `getMouse3d` check, then Lua calls `PawnCPP:RMB_BP_pressed()` and `RMB_BP_released()` | Cursor placement WORKS: asked point (-36373,-53010) gave `getMouse3d` (-36512,-52875), 140 units off. The two Lua calls do NOTHING: distance 1544 -> 1545 over 60 game seconds. They are empty events, the order is read from the input system. (s59-f paused the game right after the call and then the unpause failed; do not pause there.) |
| s59-h | `steer_select`, `steer_cursor` to a world point, then `ctx.order_with_mouse()` (right click at the current cursor, no pixel math) | WORKS: 1547 -> 127. |

Also: `getMouse3d` gives z = -100000 when no terrain is under the cursor; the point must be on screen (the camera sits at the player pawn, so spawned squads are near it).

## Commands added (HarnessActions version 40)
`steer_state` (read: side, units, centre, mean unit target), `steer_select`, `steer_cursor`, `steer_mouse3d`, `steer_rmb` (does nothing, kept as evidence), `steer_move` (`formALineArmy`, does nothing), `steer_hook` and `steer_hook_log` (record calls of chosen functions; paths joined by commas). Python: `Actions.steer_*`, `ScenarioContext.order_with_mouse`, `osinput.right_click`, `osinput.order_with_mouse`.

## Not verified
- AI lord and bandit squads (they ignore `formALineArmy`; the real right click works only for squads the player commands).
- A move to a point that is off screen (the camera would need to move first).
- Other native paths: for example a keyboard injection, or a call to a native function that the UI uses (not reflected, so unreachable from Lua).
- The cursor and focus belong to the OS: do not run it while a person works on the PC. The cursor is restored afterwards.

## Decision
A harness test can send a player squad to a point with `steer_select` + `steer_cursor` + one real right click (hidden, like `place-building`). For enemies keep the earlier answer: steer the AI inputs (war, challenge, bait, waypoint), not the squad. A scenario with `COVERS` and a 3 of 3 run is still to do.
