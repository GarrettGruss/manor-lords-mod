## MODIFIED Requirements
<!-- Issue: #476 -->

### Requirement: Time moves only when the test moves it
The kit SHALL advance fake time only through `tick`, `advance` and `run_until_idle`. One step SHALL run the registered tickers, then the `LoopAsync` loops and the `LoopInGameThreadWithDelay` loops, then the queued `ExecuteInGameThread` work. `CancelDelayedAction` SHALL stop a game-thread loop. `run_until_idle` SHALL fail after 400 fake seconds if loops stay alive.

#### Scenario: A loop that never stops
- **WHEN** a loop never returns true and the test calls `run_until_idle`
- **THEN** the call fails loudly at the limit
- Checked by `harness/tests/test_fakegame_kit.py`.

#### Scenario: Game thread work waits
- **WHEN** a mod queues work with `ExecuteInGameThread`
- **THEN** the work runs in the next step, not at once
- Checked by `harness/tests/test_fakegame_kit.py`.

#### Scenario: A game-thread loop is cancelled
- **WHEN** a mod starts a loop with `LoopInGameThreadWithDelay` and later calls `CancelDelayedAction` with its handle
- **THEN** the loop runs at its interval until the cancel, and not after
- Checked by `harness/tests/test_fakegame_kit.py`.
