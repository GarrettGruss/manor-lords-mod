# Load hook for the autosave push (task 1.1)

## Result

The hook is `/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ReceiveBeginPlay` (the player pawn). It fires once per world load. The InvasionMod already uses it (`mod_state`).

- A Blueprint script hook runs only its FIRST callback (the pre callback). A second (post) callback is ignored. Run 20261020-023614-9fa8 failed for this reason: the push was in the post callback and never ran.
- The pre callback runs before the pawn starts its timer. So the push waits 2 s (`ExecuteWithDelay`) and retries up to 5 times, until `is_disabled` is true.
- The hook is registered at READY, when the class is loaded. It stays for later loads.

## Load without a save function

No save is loaded. The test scenario `autosave-after-load` makes a world load with the console command `open /Game/NotStronghold/Maps/NewMapSets/Jagged_Cliffs` (bridge op `console`) after READY. This is a fresh start on a map. It creates a new pawn and a new timer (585 s remaining without the fix). It calls no save function.

## Real runs

- 20261020-023614-9fa8: fail, as expected (post callback). Timer 585 s after the load.
- 20261020-023736-1beb: pass. Log line: `autosave pushed away after a load: timer remaining 600.0 s -> 31535400.0 s (try 1)`.

Not tested: a load of a real save slot from the in-game menu (needs the owner). It runs the same pawn BeginPlay.
