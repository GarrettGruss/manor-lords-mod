# Mock kit (part B): findings and limits

Date: 2026-10-10. Code: `harness/tests/fakegame/`. How to use it: `harness/tests/fakegame/README.md`.

## What was built
- A Lua prelude (`prelude.lua`) with the fake UE4SS globals, and a Python `FakeGame` on top of `lupa`.
- Fake objects, arrays, FString and RemoteUnrealParam wrappers are **Lua tables with metatables**, not Python userdata.
  Reason: a mod then gets real Lua errors with a Lua traceback, and a nil key can be made to fail in `__index`.
  Python builds and controls them (`game.obj`, `game.array`, `game.method`).
- Fake time: `os.time`, `os.clock` and `os.date` follow `game.fg.now`. The test moves it with `tick` or `advance` (step 0.5 s).
- `FakeGameClock` copies `pause-and-game-speed.md`: hold at 0 after the load, a start that undoes an early pause,
  and one late revert.
- `build_manor_lords_state` builds the menu, the load screen, the engine and the player with the field names of
  `jmap-findings.md` and `in-game-messages-and-hud.md`.
- `boot_state_machine.py` now runs on the kit, with the same six modes and checks. It still ends with a check that
  the clock stays stopped for 10 s after READY.

## Results
- All six boot modes pass on the kit.
- The two old HarnessBoot versions are still caught. Commit f1903e6 fails `happy` ("the clock moved after READY (0.0 -> 4.0)").
  Commit 1578d7c fails `happy` ("the clock moved after READY (0.5 -> 8.0)"). They were run with `boot_script` in `run_mode`.
- The happy path also passes with array wrappers on and off, and FString text on and off.
- A real finding from the example test: `HarnessLoadProbe` takes the first list that is not empty. If the slot list is
  still filling (`slot_list_delay` above 0), it reports "slot is not in the list". HarnessBoot does not have this problem.
  The probe is only a probe, so it was not changed.

## Differences from the real UE4SS (limits)
- **Lua 5.5 in the tests, 5.4 in the game.** The prelude uses only 5.4 features. The kit cannot find a mod that uses 5.5-only
  syntax. `lua_syntax.py` also compiles with 5.5.
- **Threads:** one real thread. Loops run first in a step, then queued game-thread work. Race conditions are not modeled.
  `strict_threads=True` only checks the "touch objects on the game thread" rule.
  Whether key bind callbacks run on the game thread in the real UE4SS is not known; the fake treats them as game thread.
- **Wrappers:** the real game may return `RemoteUnrealParam` only in some places. The kit has a switch (`array_wrap`),
  and hook arguments are always wrappers. This is a guess based on the `:get()` code in `HarnessBoot`.
- `FindFirstOf` and `StaticFindObject` return nil when not found. Some UE4SS versions return an invalid object.
- Unknown properties read as nil. The real game may raise an error.
- Out parameters, `TMap`, delegates, enums, `FName` and `UClass` are not built. `GetClass()` returns a simple object.
- Hooks do not fire by themselves, and reload behavior of hooks (spec 06, part A) is not modeled.
- The kit runs on Windows only, because `HarnessLog` uses Windows `mkdir` syntax through `os.execute`.
- `setGameSpeed(0)` leaves the clock at 0.27x. This is from one measurement (0.8 in 3 s).

## Not verified
- That the fake behaves like the real game in any case that was not already in the notes. The kit proves mod logic only.
- Use on a machine without Windows. Not tried.
