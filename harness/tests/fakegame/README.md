# fakegame: a fake UE4SS API for mod tests

Test a Lua mod without the game. Spec: `docs/specs/06-dev-loop-and-fixtures/` (part B).
Findings and limits: `implementation-notes/mock-kit.md` in that spec.

Run from the repo root:

```
uv run --no-project --python 3.12 --with lupa python -m unittest discover -s harness/tests -p "test_fakegame*.py" -v
```

## Write a mod test (under 30 lines)

This is a short version of `harness/tests/test_fakegame_example.py`.

```python
import unittest
import fakegame_path  # makes `fakegame` importable
from fakegame import FakeGame, build_manor_lords_state

class LoadProbeTests(unittest.TestCase):
    def test_f8_loads_the_wanted_slot(self):
        with FakeGame(env={"HARNESS_TEST_SAVE": "saveGame_0"}) as game:
            state = build_manor_lords_state(game)      # menu, load screen, engine, clock
            game.load_mod("HarnessLoadProbe")          # runs mod/HarnessLoadProbe/Scripts/main.lua
            game.advance(3)                            # fake seconds; the menu appears after 2 s
            self.assertEqual(game.press("F8"), 1)      # one key bind ran
            game.advance(10)
            self.assertEqual(state.calls, ["SwitchToLoadScreen", "LoadGame:2"])
            self.assertTrue(any("returned without error" in l for l in game.log_lines()))
```

Steps: open `FakeGame`, build a world, `load_mod`, move the fake time, press keys, assert on calls and files.
`FakeGame` sets `HARNESS_RUN_DIR` to a new temp folder, adds your `env`, and restores `os.environ` on exit.

## API

| Call | Use |
|---|---|
| `FakeGame(env, strict_threads, array_wrap, fstring_mode)` | Context manager. `env` value `None` removes a variable. |
| `game.obj("Class", **props)` | Fake UObject. Found by `FindFirstOf("Class")` while valid. |
| `game.method(obj, "Name", fn)` | `obj:Name(...)` calls `fn(obj, ...)`. |
| `game.array(items, wrap=None, visible=None)` | TArray: `GetArrayNum`, 1-based index, `ForEach`. `visible()` makes it fill over time. |
| `game.struct(**fields)` | Struct: a plain Lua table. |
| `game.text("x")` | FString-like value (`:ToString()`) or plain string, by `fstring_mode`. |
| `game.finder("Class", fn)`, `game.static(path, obj)` | Control `FindFirstOf` and `StaticFindObject`. |
| `game.tick(s)`, `game.advance(seconds)`, `game.run_until_idle()` | Move fake time (default step 0.5 s). |
| `game.press("F8", "CONTROL")`, `game.fire_hook(path, ...)`, `game.spawn(obj)` | Key binds, hooks, `NotifyOnNewObject`. |
| `game.load_mod(name)`, `game.exec(lua)` | Run a mod or Lua code. |
| `game.files()`, `read_json`, `read_jsonl`, `read_text`, `log_lines()`, `printed()` | Read the output. |
| `FakeGameClock(...)` and `build_manor_lords_state(game, ...)` | Game clock with pause and speed, and a Manor Lords state. |

`build_manor_lords_state` makes: `mainMenu_widget_C` (`SwitchToLoadScreen`, `LoadGame`),
`W_MainMenu_SaveLoadScreenV2_C` (`SortedSlotsByDate` that can fill over time), the IoHandler at
`/Script/ManorLords.Default__IoHandler` (`DoesSaveGameExist`), and `RTSMultiEngineCPP` with `regions`, `playerRef`
(`PawnCPP`, with `pauseGame`, `unPauseGame`, `setGameSpeed`, `InBox`), `TemporalComponent` and `getGameTimeAdjusted`.
It returns a namespace with `calls`, `clock`, `widget`, `screen`, `engine`, `player`.
Options: `wanted_slot_listed`, `save_exists`, `menu_delay`, `slot_list_delay`, `engine_delay`, `clock`.

The clock copies the real game (see `docs/specs/02-save-autoload/implementation-notes/pause-and-game-speed.md`):
it stands at 0 for `hold_seconds` after `LoadGame`, then the game starts it and undoes an earlier pause,
and the intro cinematic (`cinematic=(start, end)`, `currentUIMode` 1) ends later with a restart at 1x. `late_revert_after` is a restart with no sign (off by default). `PawnCPP.bIsPlayerPaused` is stuck at true until a pause call.

## What the fake does that helps you

- A nil key fails: `obj[nil]`, `array[nil]`, `obj[nil] = x`. A mod must never index with nil.
- A property of an invalid object fails (`IsValid()` still works). An array index out of range fails.
- `array_wrap=True`: elements are wrappers, so `array[i].field` fails until `:get()`.
- `fstring_mode=True` (default): a text property is not equal to a string until `:ToString()`, and other member access fails.
- An unknown `Key.X` fails at once.
- `strict_threads=True`: touching a game object inside a `LoopAsync` callback fails.

## What the fake does NOT cover

- It does not prove the real game behaves the same. Every behavior was copied from notes, not from the game code.
  Wrong or missing behavior in the fake gives a wrong pass. Check new findings with the real game.
- Lua version: lupa embeds **Lua 5.5**. The game uses **5.4**. Do not use 5.5-only features
  (`global` declarations, read-only `for` variables, new integer `for` rules) in mods. The kit cannot warn you.
  `require` returns two values in 5.4 and 5.5: in Python use `lua.eval('(require("X"))')`.
- Threads: there is one real thread. `LoopAsync` callbacks run in a step, then `ExecuteInGameThread` work runs.
  The game thread flag only matters with `strict_threads=True`. Real races, locks and crashes are not modeled.
  `RegisterKeyBind` callbacks and hooks are run as game-thread code. This is a guess.
- Wrappers: hook arguments are all wrappers (`:get()`). Wrapper modes are a switch; the real game may mix them.
  Out parameters, `FName` objects, `TMap`, `TSet`, delegates, enums and `UClass` objects are not built.
  Unknown properties return nil. The real game may error.
- `FindFirstOf` returns nil when nothing is found. Some UE4SS versions return an invalid object.
- `RegisterHook` never fires by itself. The test calls `fire_hook`. Hook registration on reload is not modeled.
- `os.time` and `os.clock` are fake. `os.date` uses the fake time. `io`, `os.execute` and `os.getenv` are real.
- Paths: `HarnessLog` runs `mkdir` through `os.execute` with Windows syntax, so the kit runs on Windows only.

## Restart of a mod (spec 06, part A)

`RestartMod(name)` only records the name in `game.fg.restarts`. A test can set `game.fg.on_restart` to a Lua function that acts like the
restarted mod. See `harness/tests/test_fakegame_harnessreload.py`. The real UE4SS gives the mod a new Lua state; the kit does not model that.
