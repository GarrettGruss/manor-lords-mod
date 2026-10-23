# Wipe crash (run 20261023-010958-4796)

Scenario `vassals-wipe` on Goldhof (Hochweg, 34 buildings, 16 families, 46 people), slot 0, fixture `base`.

## What the crash report shows
- Crash type: `EXCEPTION_ACCESS_VIOLATION reading address 0x0000000000004455` (the report in `runs/<id>/crash/`).
- The call stack is inside UE4SS: `luaV_execute` called from `process_simple_actions` (`LuaMod.cpp:3819`) called from `engine_tick_hook`. This is a Lua action on the game thread (an `ExecuteInGameThread` job), and the fault is in a native frame under a Lua call, with game code (`ManorLords-Win64-Shipping`) below it. The minidump has no symbol for the game frames.
- The last mod log lines, in the same second (1792717867): `VASSALS lost ... reason=wiped`, `REFUGEES wave share=0.50 wanted=8 calls=2 ... families 10 -> 20 homeless 0 -> 8`, `VASSALS wiped ... villagers deleted families=16 people=46`. So in one tick the mod killed 46 people, freed the slot, and the refugee listener called the game (`settleRegion` twice) in the home region.
- No raid was active in this run (the scenario starts the sack with the command). So the owner hypothesis "a raid kills a family at the moment the mod removes it" is not what happened here. The double-kill idea (a dying unit killed again) still fits: `just_die` on 46 units, then game calls in the same tick, before the game has finished the deaths.
- Four other wipes of Goldhof did not crash (runs -005438-80b8, -010105-f526 gave up, -010329-225e, -011135-bce6), so the crash is rare and timing dependent.

## Fix (owner, 2026-10-22)
- The wipe now takes three polls: (1) remove all families except one; (2) when the family count was stable for one poll, remove the last family; (3) when the count was stable again, free the slot and tell the listeners (the refugee wave). The sack still waits one poll after the collapses.
- The game does not give a flag for a family that is dying, so "stable count for one poll" is the check.
- Result of the repeat runs: see the end of this file.
