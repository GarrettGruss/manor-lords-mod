---
type: Testing
title: Fake game kit
description: How Lua mods are tested without the game, using lupa and the fakegame kit (FakeGame, prelude.lua, clock, Manor Lords state), the test layers, the kit limits, and how to write a mod test.
tags: [testing, lua, lupa, fakegame, mods]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T16:15:30Z }
sources:
  - resource: repo://harness/tests/fakegame/
  - resource: repo://harness/tests/test_fakegame_kit.py
  - resource: repo://harness/tests/test_fakegame_example.py
  - resource: repo://harness/tests/lua_syntax.py
  - resource: repo://harness/tests/boot_state_machine.py
  - resource: repo://harness/tests/fakegame_path.py
  - resource: repo://harness/tests/modstate_support.py
  - resource: repo://harness/tests/battle_support.py
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/implementation-notes/mock-kit.md
  - resource: repo://CLAUDE.md
  - resource: repo://CONTRIBUTING.md
  - resource: repo://openspec/changes/archive/2026-10-16-legacy-m12-tech-tree/implementation-notes/f9-key-crash.md
---

# Fake game kit

The fake game kit runs the real Lua files of `mod/` inside a Lua state that has a fake UE4SS API. No game is needed. It is the fast test layer: a full run takes seconds. The kit was built in spec 06, part B. See [mock-kit.md](../../../openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/implementation-notes/mock-kit.md) for the findings and limits, and [fakegame/README.md](../../../harness/tests/fakegame/README.md) for the API table.

The kit does not prove that the real game behaves the same. Every behavior was copied from notes. A wrong fake gives a wrong pass. A new finding must be checked in the real game (a spike or a scenario).

## Parts

| File | Job |
|---|---|
| [`fakegame/game.py`](../../../harness/tests/fakegame/game.py) | `FakeGame`: context manager. Makes a temp run folder, sets `HARNESS_RUN_DIR`, builds a `lupa` `LuaRuntime`, runs the prelude, loads mods, moves fake time, reads output. |
| [`fakegame/prelude.lua`](../../../harness/tests/fakegame/prelude.lua) | The fake UE4SS globals in Lua: objects, arrays, FString text, `FindFirstOf`, `StaticFindObject`, `RegisterHook`, `RegisterKeyBind`, `LoopAsync`, `ExecuteInGameThread`, `NotifyOnNewObject`, `Key`, `ModifierKey`, fake `os.time`, `os.clock`, `os.date`. |
| [`fakegame/clock.py`](../../../harness/tests/fakegame/clock.py) | `FakeGameClock`: game clock with pause, speed, the hold at 0 after a load, the intro cinematic, and the late revert. |
| [`fakegame/manorlords.py`](../../../harness/tests/fakegame/manorlords.py) | `build_manor_lords_state`: main menu, load screen, IoHandler, engine, player pawn, calendar, and the autosave timer. |
| [`fakegame_path.py`](../../../harness/tests/fakegame_path.py) | Import it first in a test. It puts `harness/tests` on `sys.path` so `fakegame` can be imported. |

Fake objects, arrays and text are Lua tables with metatables, not Python objects. A mod therefore gets real Lua errors with a Lua traceback. Python builds and controls them through `game.obj`, `game.array`, `game.method`, `game.struct`, `game.text`.

## How a test runs

1. `FakeGame(env=...)` starts. It creates `fakegame-*` in the temp folder, sets `HARNESS_RUN_DIR` to it and adds `env` (a value of `None` removes a variable). It puts `mod/shared/` on `package.path`, so `require("HarnessLog")` finds the real shared modules.
2. The test builds a world: `build_manor_lords_state(game)` or its own `game.obj(...)` objects.
3. `game.load_mod("Name")` runs `mod/<Name>/Scripts/main.lua`.
4. The test moves fake time with `game.tick(s)`, `game.advance(seconds)` (default step 0.5 s, the usual `LoopAsync 500` period), or `game.run_until_idle()` (fails after 400 fake seconds if loops stay alive).
5. The test sends events: `game.press("F8", "CONTROL")` for key binds, `game.fire_hook(path, ...)` for hooks (a hook never fires by itself), `game.spawn(obj)` for `NotifyOnNewObject`.
6. The test reads the output: `game.files()`, `read_json`, `read_jsonl`, `read_text`, `log_lines()` (the `mod.log` of `HarnessLog`), `printed()`, and `state.calls` of the Manor Lords state.
7. On exit, `FakeGame` collects Lua garbage (open files), restores `os.environ` and deletes the run folder.

One fake step runs in this order: registered tickers (the game clock), `LoopAsync` loops, then queued `ExecuteInGameThread` work. There is one real thread. Races are not modeled.

```python
with FakeGame(env={"HARNESS_TEST_SAVE": "saveGame_0"}) as game:
    state = build_manor_lords_state(game)
    game.load_mod("HarnessLoadProbe")
    game.advance(3)
    assert game.press("F8") == 1
    game.advance(10)
    assert state.calls == ["SwitchToLoadScreen", "LoadGame:2"]
```

This is the shape of [`test_fakegame_example.py`](../../../harness/tests/test_fakegame_example.py).

## Strict checks the fake gives

A mod fails in the kit for these mistakes, as it would fail (or crash) in the game:

- a nil key: `obj[nil]`, `array[nil]`, `obj[nil] = x`;
- a property of an invalid object (`IsValid()` still works), or an array index out of range;
- `array_wrap=True`: array elements are wrappers, so `array[i].field` fails until `:get()`;
- `fstring_mode=True` (default): a text property is not equal to a string until `:ToString()`;
- an unknown `Key.X`;
- `strict_threads=True`: touching a game object inside a `LoopAsync` callback fails.

## One Lua state for each mod

UE4SS gives every Lua mod its own Lua state. A shared module such as `HarnessCommands` is loaded again for each mod, and tables cannot cross between mods. By default the kit runs all mods in one state, which hides this. With `FakeGame(separate_states=True)`, each `load_mod` makes a fresh state. A second `load_mod` of the same name acts like a hot reload. Use `game.exec(lua, state="ModName")` to run code in one mod state. Mods that talk to each other must do it through files, as the real mods do. `RestartMod(name)` only records the name in `game.fg.restarts`. A test may set `game.fg.on_restart`.

## Clock and Manor Lords state

`FakeGameClock` copies [pause-and-game-speed.md](../../../openspec/changes/archive/2026-10-15-legacy-02-save-autoload/implementation-notes/pause-and-game-speed.md). The clock stands at 0 for `hold_seconds` after `LoadGame`. Then the game starts it at 1x, and that start undoes an early pause. An intro cinematic (`cinematic=(start, end)`) sets `currentUIMode` to 1 and ends with a restart at 1x. `late_revert_after` is a restart with no sign. `pause_works=False` and `starts=False` make broken games.

`build_manor_lords_state` returns a namespace with `calls`, `clock`, `widget`, `screen`, `engine`, `player`. Options include `wanted_slot_listed`, `save_exists`, `menu_delay`, `slot_list_delay`, `engine_delay`, `clock`. It also builds a fake autosave timer (`SetAutosavePeriodOnPawn`, 600 s period) that counts real time, like the real one ([autosave.md](../../../openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/implementation-notes/autosave.md)).

## Test layers

| Layer | Files | What it covers |
|---|---|---|
| Kit self tests | `test_fakegame_kit.py` | Objects, arrays, text modes, time, loops, keys, hooks, environment restore, clock, separate states. |
| Shared module tests | `test_fakegame_harness*.py` | One file for each shared module (`HarnessCommands`, `HarnessActions`, `HarnessSave`, `HarnessBattle`, ...). See [shared Lua modules](../architecture/shared-lua-modules.md). |
| Mod and feature tests | `test_fakegame_invasion.py`, `_bandits`, `_raid_*`, `_sack_*`, `_refugees`, `_tribute`, `_vassals`, `_manor_stronghold`, ... | The Invasion Mod features and stand-in mods. See [Invasion Mod features](../architecture/invasion-features.md). |
| Scenario tests | `test_fakegame_*_scenarios.py`, `test_fakegame_ui_scenario.py` | Scenario files from `harness/scenarios/` against the fake world, to check the checks before a real run. |
| Boot state machine | `boot_state_machine.py` | `mod/HarnessBoot` in modes such as `happy`, `slotlate`, `noslot`, `pausefails`, `cinematic`, `newgame`, `freshstart`. Run as a script. |
| Lua syntax | `lua_syntax.py` | Compiles every `mod/**/*.lua`. Exit code 1 on a failure. |
| Telemetry mock | `test_telemetry_mock.py` | `HarnessJson` and `HarnessTelemetry` with a small hand-made fake API (it does not use the kit). |
| Safety | `test_save_call_sites.py` | Only `HarnessSave.lua` may call a game save function. A rule from CLAUDE.md, Safety. |

Helper modules build shared fake worlds: `modstate_support.py` (engine and calendar for the mod-state contract), `battle_support.py` (unit templates, `spawnArmy`, mercenaries, a simple fight rule), `saveslot_support.py`. The fight rule is a stand-in. It tests Lua logic, not how the real game fights.

## Commands

Run from the repo root. Always start with `uv run python` (CONTRIBUTING.md, Set up).

```
uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"
uv run python -m unittest discover -s harness/tests -p "test_fakegame_kit.py" -v
uv run python harness/tests/lua_syntax.py
uv run python harness/tests/boot_state_machine.py [mode ...]
uv run python -m unittest harness/tests/test_telemetry_mock.py -v
```

`boot_state_machine.py` with no mode runs all modes. After READY it waits 10 more fake seconds and checks that the clock did not move.

## Write a new mod test

1. Put `import fakegame_path  # noqa: F401` first, then `from fakegame import FakeGame, build_manor_lords_state`.
2. Name the file `test_fakegame_<topic>.py` in `harness/tests/`. Discovery uses that pattern.
3. Build only the objects the mod reads. Use `game.method(obj, "Name", fn)` for UFunctions and record calls in a list to assert on them.
4. Use `separate_states=True` when the mod uses a shared module with a registry or talks to another mod.
5. Assert on ranges and on calls, not on exact timing the real game would not repeat (CLAUDE.md: the simulation is not deterministic).
6. Also turn on `array_wrap=True` and `fstring_mode` variations when the mod reads arrays or text. `boot_state_machine.py` does this for the boot path.

## What the kit does not cover

- Lua version. `lupa` embeds Lua 5.5. The game uses 5.4. Do not use 5.5-only features (`global` declarations, read-only `for` variables). The kit cannot warn you.
- Threads. Real races, locks and crashes are not modeled. The kit runs key bind callbacks as game-thread code, but in the real game they run on the input thread ([f9-key-crash.md](../../../openspec/changes/archive/2026-10-16-legacy-m12-tech-tree/implementation-notes/f9-key-crash.md)). A key callback that does Lua work passes here and can crash the game. Hooks are assumed to run on the game thread.
- Wrappers. Hook arguments are always wrappers. The real game may mix them.
- Not built: out parameters, `FName` objects, `TMap`, `TSet`, delegates, enums, `UClass` objects. Unknown properties read as nil, the real game may raise an error.
- `FindFirstOf` returns nil when nothing is found. Some UE4SS versions return an invalid object.
- `io`, `os.execute` and `os.getenv` are real. `HarnessLog` makes folders with `os.execute('mkdir "<path with backslashes>" >nul 2>&1')`, which is Windows syntax.

## Windows only

The project runs the tests on Windows. On Linux or WSL the Lua `mkdir` call above does not make the wanted folder. Instead it makes empty folders named like `\tmp\fakegame-xxxx` and a file `nul` in the current folder. So many `test_fakegame_*` tests fail there with `FileNotFoundError` (for example on `modcmd/<Mod>/0001.json`), and the repo root fills with empty folders. If you ran them on Linux, delete those empty folders and `nul`. Treat a Linux result as partial.

## Related

- [Python tests and coverage](python-tests.md): the other test layers and the full test set.
- [Shared Lua modules](../architecture/shared-lua-modules.md): the code these tests cover.
- Skill `harness-mod-state` for stand-in mods, and spec 07 `openspec/changes/archive/2026-10-15-legacy-07-feature-test-kit/` for the action kit that uses `test_fakegame_harnessactions.py`.
