# Suite results

Suite `harness/suites/lua-thread-safety.json`, suite run `suite-20261024-052924-250d`. Code: branch `fix/fix-lua-thread-safety` (all timers on the game thread, key binds hand work to the game thread, deferred raid unit scan). One game at a time. 20 runs, 6278 s.

| Scenario | Runs | Passed | Crashes | TimeControlError | Spike numbers (before) |
|---|---|---|---|---|---|
| invasion-first-raid (about 470 s, speed 3) | 10 | 10 | 0 | 0 | crashed 3 of 11 |
| invasion-great-raid-waves | 10 | 5 | 0 | 5 | 3 of 5 speed failures with `async`, 0 of 5 with `game` |

- Crash folders: none in 20 runs (`runs/<id>/crash` is empty in every run).
- First raid: run ids `...-001` to `...-010` of the suite stamp `20261024-052924-250d`, all `pass`.
- Waves: failed runs `-011`, `-012`, `-014`, `-015`, `-017`. Message: `TimeControlError: speed 3 should give gameSpeed 8.0, but the game reports 1 after 3 tries`. The first day of the wave test ran at speed 8, then the game reported speed 1 and the harness could not set it back.
- Memory (`hostmem.jsonl`): free memory 3.3 to 4.2 GB of 16 GB, game 4.2 to 4.7 GB. No memory pressure.

## Reading
- The crash rate went from 3 of 11 to 0 of 10 in `invasion-first-raid`. With a crash rate of 27% before, the chance of 0 of 10 by luck is about 4%. The cause is still not proven, because other changes may also matter.
- The speed failure in the waves test did not go away (5 of 10). The spike had 3 of 5 with `async` and 0 of 5 with `game` (p = 0.17), so the weak hint is not confirmed: timers are not the cause of it. The cause is open. A follow-up change should find what resets the game speed after the first wave day.
