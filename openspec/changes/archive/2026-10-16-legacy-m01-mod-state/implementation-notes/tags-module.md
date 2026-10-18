# Iteration 01: ModState on pawn Tags (findings)

Date: 2026-10-16. Issue #142. Code: `mod/shared/ModState/ModState.lua`, `mod/InvasionMod/Scripts/features/mod_state/init.lua`.

## Run ids (real game, all pass)
| Check | Runs |
|---|---|
| A1, A4, A5, A6 `mod-state-default-load` (fixture `base`) | 20261016-230926-018f, 20261016-232119-da12 |
| A1 and A2 `mod-state-roundtrip`, 3 of 3 (write run, then read run) | write d1a7 / read e7f9; write 084e / read f60b; write f405 / read 9e72 (all 20261016-23xxxx) |
| A3 `mod-state-two-saves` write (slots A and B), read A, read B | 20261016-231802-5f41; read A 20261016-231906-9f6e; read B 20261016-232016-650e |

Run 018f passed its scenario, but its teardown failed: `rtsSettings.sav` changed. The user had their own game open at that time. It is not a harness or mod effect.
The kept slots (7 files each: saveGame 52, 54, 56, 58, 59) were deleted by hand. Slot 50 (8 files) is older and was left alone.

## Tag removal: not needed
The module never removes a Tag. A changed key overwrites its array element in place (`tags[i] = FName(...)`). A new key appends. A key has one element for the whole game, so there are no duplicates and no removal.
The in-game runs show overwrite and append work (roundtrip sets `selftest_int` twice and finds one entry). A removal from Lua was not tried, because the design does not need it.
A stale entry (a key that is no longer registered) stays in the save and shows up in `dump().unknown`.

## ReceiveBeginPlay finding
At `MyPawnCPP_BP3_C:ReceiveBeginPlay` the engine does not hold the new pawn yet (`engine.playerRef` is invalid or old). A direct `open` in the hook failed with "no live player pawn" (run efe0 log).
Fix: the hook starts a poll (500 ms, at most 240 polls). The poll runs `state:load()` on the game thread once `playerRef` is valid. In the read runs the loaded Tags were complete when the poll succeeded, so the saved Tags are restored by then.
A set between the load and the poll would be lost. In practice no mod code sets values that early.

## Boot crash with probe hooks
Run 20261016-230828-f23b: the game crashed 12 s into boot (`EXCEPTION_ACCESS_VIOLATION` at 0xc, stack `luaH_getint` <- `RemoteUnrealParam::prepare_to_handle` <- `auto_construct_object`). This is a hook-argument conversion. `mod_state` hooks take no arguments. The old `HarnessSaveProbe` hooks the same functions and reads their arguments, so it is the likely source. It did not recur in 9 later runs. The probe mods were not touched.

## Other facts
- A Lua state per mod: `ModState` is loaded again inside `InvasionMod`, so `ModState.open` is shared by the features of that one mod only.
- A Lua `nil` is dropped by JSON, so `stored_version` is absent in a dump of a save without the mod. Scenarios use `dump.get(...)`.
- A run cannot load a save by itself. Each save scenario has a write phase and a read phase (`--env MODSTATE_PHASE=read`, `--save <slot>.sav`).
