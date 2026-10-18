# Spec Delta

## MODIFIED Requirements

<!-- Issue: #266 -->

### Requirement: One scheduler timer runs all feature jobs
The mod SHALL run periodic feature work through `scheduler.every(name, every_ms, run)`. The scheduler SHALL use one `LoopAsync` timer with a tick of 100 ms and SHALL run due jobs on the game thread. A job that raises an error SHALL be logged with a stack trace and SHALL NOT stop the other jobs. The tick SHALL NOT be faster than 100 ms, because a 50 ms tick broke the Lua state after about 3 minutes with a menu open (spec 34).

#### Scenario: Two jobs, one fails
- **WHEN** two jobs are registered and one of them raises an error
- **THEN** the error is logged with its job name and the other job still runs at its interval
- Not checked yet.

#### Scenario: A menu stays open
- **WHEN** the tech tree menu stays open for 300 s while the mod state is read twice a second
- **THEN** the Lua state stays alive and the game keeps answering
- Not checked yet. Spec 34 recorded one passing run (`20261018-173614-d910`), but no committed test scenario repeats it.
