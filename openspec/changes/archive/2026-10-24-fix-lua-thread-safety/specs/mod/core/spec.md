## MODIFIED Requirements
<!-- Issue: #476 -->

### Requirement: One scheduler timer runs all feature jobs
The mod SHALL run periodic feature work through `scheduler.every(name, every_ms, run)`. The scheduler SHALL use one game-thread timer (`HarnessLoop.every`) with a tick of 100 ms and SHALL run due jobs on the game thread. A job that raises an error SHALL be logged with a stack trace and SHALL NOT stop the other jobs. The tick SHALL NOT be faster than 100 ms, because a 50 ms tick broke the Lua state after about 3 minutes with a menu open (spec 34).

#### Scenario: Two jobs, one fails
- **WHEN** two jobs are registered and one of them raises an error
- **THEN** the error is logged with its job name and the other job still runs at its interval
- Not checked yet.

#### Scenario: A menu stays open
- **WHEN** the tech tree menu stays open for 300 s while the mod state is read twice a second
- **THEN** the Lua state stays alive and the game keeps answering
- Not checked yet. Spec 34 recorded one passing run (`20261018-173614-d910`), but no committed test scenario repeats it.

## ADDED Requirements

### Requirement: Key bind callbacks do not change shared Lua tables
A key bind callback runs on the input thread. It SHALL NOT read or write the mod state tables. It SHALL only queue the action with `ExecuteInGameThread`, and the table work SHALL run in that queued function.

#### Scenario: A menu key is pressed
- **WHEN** a key bind for a menu toggle or for Esc fires
- **THEN** the toggle request is stored only after the game thread runs the queued function
- Checked by `harness/tests/test_fakegame_menu.py`.

### Requirement: A unit scan does not run in the tick of a wave spawn
After a wave spawn the mod SHALL run the scan over all units in a later game-thread tick. Loops over `FindAllOf` results SHALL check `IsValid` for each object before they use it.

#### Scenario: A wave spawns
- **WHEN** a wave spawn finishes
- **THEN** the unit scan does not run in the same scheduler tick
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.
