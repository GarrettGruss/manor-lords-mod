# Mouse-free placement: preview hook (issues #104, #115)

Date: 2026-10-15. Result: PARTIAL. The ghost can be put at any world point. The placement is still refused. Row 30 and row 125 were not placed. 4 game launches (runs `s104h-1` to `s104h-4`, fixture `base`). No save function was called. `allow_eval` stayed false.

Follows `mousefree-placement.md`. Code: opt-in mod `mod/HarnessPlace` (hooks and writes start only after `HarnessPlace.arm`), tool `harness/tools/s104_place.py` (sends mod commands to a `--keep-open` run).

## Question
Can a Lua hook write the placement preview (`DummyBuilding`) after the native tick, and can that make a valid placement?

## Facts found
- `MyPawnCPP_BP3_C:ReceiveTick` fires every frame (also while the game is paused). `getMouse3d` is called once per frame by the Blueprint.
- A POST hook on `ReceiveTick` never fired in this build (0 calls). A PRE hook fires.
- Order in a frame: pawn `ReceiveTick` (pre), then the native pawn tick writes (0, 0, -100000) into `DummyBuilding`, then later actors tick.
  - A write from the pre hook is overwritten in the same frame (the next pre hook read -100000).
  - Fix: a late writer. The hook is on `MLPlayerController_C:ReceiveTick` pre, and `controller:AddTickPrerequisiteActor(pawn)` makes the controller tick after the pawn. The write there sticks: the ghost stays at the target at the end of each frame, and the screenshot shows the ghost mesh at the target (`runs/s104h-3/screenshots/hook2.png`, `hook3.png`; moving the target moved the ghost).
- Writing `LastMousePos` (before the native tick) does not change the native cursor result (`s104h-4`, probe mode: the ghost stayed at -100000).
- `regionUnderCursor` was already the player region (Nusslohe). Writing it each frame changed nothing.

## What still fails
- The ghost is orange with the text "Cannot build in this Region" at every tried spot, also near the village and the roads (3 spots).
- `LMB_BP_pressed` then `LMB_BP_released` with the ghost held at the target: hitching posts in the region stay 0.
- Reason (not proven): the validity check and the commit are native and use the failed cursor hit, not the component position. They have no reflected input that Lua can write.

## Hang to avoid
After the late writer ran with a `regionUnderCursor` write, `HarnessPlace.disarm` (`resetBuildingMode`) was followed by a frozen game thread (bridge and mod commands did not answer). The game was stopped. Cause not separated. The mod now writes `regionUnderCursor` only with `region = true`. Do not use it.

## Not done
- Spawned pivot actor and attach trick (relative write of the native tick): the first try crashed the game (`SpawnActor` or `K2_AttachToComponent`, not separated). Not repeated. It could only move the ghost anyway, not fix validity.
- Row 125 with pak `stable4`, command `place_building_at`, fake tests, skill update: not done, because the placement does not work.

## Next ideas
1. The blueprint route of spec 12 (`setPlacedBuilding(0)` then `convertBlueprintsToBuildings`, see `manor-lv3.md`) builds without a mouse. Check whether it can carry a normal building row.
2. A real or virtual mouse device on the PC (user action).
3. Find the native validity input: a hook on a reflected function that the native check calls through ProcessEvent (none seen: `updateCursor` and `updatePlacebuildingMesh` fire 0 and 1 times).

## Commands of `HarnessPlace`
`arm {x, y, z, type, late, probe, region}`, `disarm`, `state`, `press`, `release`, `pivot_attach`, `pivot_move` (crashed once, avoid).
