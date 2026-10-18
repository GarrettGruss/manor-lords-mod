# Spec Delta

## Purpose

The fake game kit runs the real Lua files of `mod/` against a fake UE4SS API, so mod logic is tested in seconds without the game. It copies known game behavior and does not prove the real game behaves the same.

## ADDED Requirements

### Requirement: A test runs real mod files in a fake game
`FakeGame` SHALL run the real files `mod/<Name>/Scripts/main.lua` and the real shared modules in a Lua state with a fake UE4SS API. It SHALL give each test a temp run folder, set `HARNESS_RUN_DIR` to it, add the given environment, and restore `os.environ` and delete the folder on exit.

#### Scenario: The environment is restored
- **WHEN** a test ends
- **THEN** the environment variables are as before and the temp run folder is gone
- Checked by `harness/tests/test_fakegame_kit.py`.

#### Scenario: A mod test end to end
- **WHEN** a test loads `HarnessLoadProbe`, advances fake time and presses a key
- **THEN** the fake game records the expected calls
- Checked by `harness/tests/test_fakegame_example.py`.

### Requirement: Time moves only when the test moves it
The kit SHALL advance fake time only through `tick`, `advance` and `run_until_idle`. One step SHALL run the registered tickers, then the `LoopAsync` loops, then the queued `ExecuteInGameThread` work. `run_until_idle` SHALL fail after 400 fake seconds if loops stay alive.

#### Scenario: A loop that never stops
- **WHEN** a loop never returns true and the test calls `run_until_idle`
- **THEN** the call fails loudly at the limit
- Checked by `harness/tests/test_fakegame_kit.py`.

#### Scenario: Game thread work waits
- **WHEN** a mod queues work with `ExecuteInGameThread`
- **THEN** the work runs in the next step, not at once
- Checked by `harness/tests/test_fakegame_kit.py`.

### Requirement: The fake is strict like the game
The kit SHALL fail a mod for a nil key read or write, a property of an invalid object, an array index out of range, and an unknown `Key` name. With `array_wrap`, `fstring_mode` and `strict_threads` it SHALL also fail an array element used without `:get()`, a text compared without `:ToString()`, and a game object touched inside a `LoopAsync` callback.

#### Scenario: A nil key
- **WHEN** a mod reads or writes an object with a nil key
- **THEN** the test fails with a Lua error and traceback
- Checked by `harness/tests/test_fakegame_kit.py`.

#### Scenario: Object access in a loop
- **WHEN** `strict_threads` is on and a `LoopAsync` callback touches a game object
- **THEN** the test fails
- Checked by `harness/tests/test_fakegame_kit.py`.

### Requirement: Events are sent by the test
The kit SHALL run key binds with `press`, hooks with `fire_hook` and `NotifyOnNewObject` callbacks with `spawn`. A hook SHALL never fire by itself. Hook arguments SHALL be wrappers.

#### Scenario: A key with a modifier
- **WHEN** a test presses a key with a modifier
- **THEN** only the key binds with that key and modifier run
- Checked by `harness/tests/test_fakegame_kit.py`.

### Requirement: Each mod can have its own Lua state
With `separate_states=True` the kit SHALL load each mod into a fresh Lua state, load a shared module again for each mod, and make a second `load_mod` of the same name act like a hot reload. Globals SHALL stay in their state and the game API SHALL be shared.

#### Scenario: A shared module in two mods
- **WHEN** two mods require the same shared module with separate states
- **THEN** each mod gets its own copy of the module table
- Checked by `harness/tests/test_fakegame_kit.py`.

### Requirement: The fake game clock copies the real clock
`FakeGameClock` SHALL hold the clock at 0 after a load, start it at 1x, let that start undo an early pause, and support a late restart. The state `build_manor_lords_state` SHALL provide the main menu, the load screen, the engine, the player pawn, the calendar and an autosave timer that counts real time.

#### Scenario: Pause before the clock starts
- **WHEN** a mod pauses the game before the clock has started
- **THEN** the later start of the clock undoes that pause
- Checked by `harness/tests/test_fakegame_kit.py`.

### Requirement: Boot is tested in modes
The script `harness/tests/boot_state_machine.py` SHALL run `HarnessBoot` in the fake game in named modes and check the end state, the failure reason and, where set, the number of `pauseGame` calls. The script SHALL return a non-zero exit code on any problem.

#### Scenario: All modes
- **WHEN** the script runs with no mode
- **THEN** every mode ends in the state it expects
- Checked by `harness/tests/boot_state_machine.py`.

### Requirement: Every Lua file compiles
The script `harness/tests/lua_syntax.py` SHALL compile every `mod/**/*.lua` file and return exit code 1 on a failure.

#### Scenario: A syntax error
- **WHEN** a Lua file has a syntax error
- **THEN** the script names the file and exits with code 1
- Checked by `harness/tests/lua_syntax.py`.
