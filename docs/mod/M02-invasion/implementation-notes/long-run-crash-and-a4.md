# Long run crash and the A4 check (issue 163)

## Symptom
Scenario `invasion-no-double-raid` (120 game days, speed 3) on main after M03, M04.01 and M05.01:
- Crashes: EXCEPTION_ACCESS_VIOLATION in UE4SS Lua code (`luaH_set`, `lua_getiuservalue`, `Lua::get_string`, an `AActor` metatable lambda). The addresses are 0x0, 0x9, 0xa, 0xffffffffffffffff: the Lua state is corrupt.
- Every stack ends in `process_simple_actions` (a job queued with `ExecuteInGameThread`). The crash is always inside Lua, not inside game code.
- Crashes happen while a raid is active (the raid_behavior tick runs) or at a bandits poll.
- A4 failed with `[0, 18]`: all raiders were dead at the end.

## Findings
- One run with `unit_balance` off did not crash, but the sample is one run. A crash rate near 50 percent means one run proves nothing.
- A lazy unit poll alone (unit_balance, fewer reads) still crashed (fix-a2). Reading only raid units plus a slower building scan still crashed (fix-b1, fix-b2, fix-b4).
- Root cause (best explanation, not proven): InvasionMod ran four `LoopAsync` loops (invasion, raid_behavior, unit_balance, bandits) in one Lua state, plus the shared command pollers. A `LoopAsync` callback runs Lua on its own thread. Lua is not thread safe. Several threads and the game thread touched one Lua state, which corrupted tables and userdata.
- Fix: one scheduler (`Scripts/scheduler.lua`) with one `LoopAsync` whose body only queues the due jobs on the game thread.
- Extra load reductions kept: raid_behavior reads only raid units and scans buildings and the AI log every 5th look; unit_balance polls every 4 s and re-reads known units only when the unit count changes or every 10th pass.

## A4
With M05 unarmored raiders die, and M04 adds bandit units from families. The living bandit count says nothing about a double raid. A4 now asserts on the spawn event (exactly one, with exactly the planned raiders) and on the timer. The census stays as a metric.

## Runs
See the iteration result of M02 and the issue 163 comment.

Proof runs with the final code (`runs/fix-c1` to `fix-c5`, 120 days each): no crash in 6 of 6. c1, c3, c4, c5, c6 passed. c2 failed only the old A4 census check (27 bandit units, 18 planned, because M04 converted families); that check was removed. Before the fix: lead-third-1 and -4, fix-a2, fix-b1, fix-b2, fix-b4 crashed (6 of 9 long runs).
