# Spec Delta

## Purpose

RefugeeWaves is a standalone player mod. A random event sends homeless refugee families to the village. The player must house them, or some of them turn into a bandit raid.

## ADDED Requirements

### Requirement: A wave can start each game month
The mod SHALL roll for a refugee wave at the start of each game month. The chance is `chance_percent` (default 15). The village SHALL have at least `min_families` families (default 10). No wave starts while another wave is active. The mod SHALL NOT start a wave in the month it loads.

#### Scenario: A sure chance starts a wave at the next month
- **WHEN** the chance is 100 percent and a new game month starts
- **THEN** a wave starts at that month and not before
- **AND** a chance of 0 never starts a wave
- Checked by `harness/tests/test_fakegame_refugeewaves.py`.

#### Scenario: A small village gets no wave
- **WHEN** the village has fewer than `min_families` families
- **THEN** no wave starts
- Checked by `harness/tests/test_fakegame_refugeewaves.py`.

### Requirement: A wave settles homeless families
A wave SHALL be 1 to `max_calls` (default 3, at most 5) calls of the game settle function on the player region. A village of `families_per_extra_call` (default 10) families allows one more call. The families arrive homeless in a tent camp near the woods, or near the village if there are no woods. The mod SHALL NOT house the refugees.

#### Scenario: A wave adds families
- **WHEN** a wave starts with one call
- **THEN** the families rise by 3 to 6
- **AND** the homeless families rise by 1 to 5
- Checked by `harness/scenarios/refugee_wave.py`.

#### Scenario: The number of calls is capped
- **WHEN** a big village starts a wave
- **THEN** the number of calls is at least 1 and at most `max_calls`
- Checked by `harness/tests/test_fakegame_refugeewaves.py`.

#### Scenario: The camp place
- **WHEN** the village has woods, or has no woods
- **THEN** the camp is near the woods, or near the village, or at the settled centre if no spot exists
- Checked by `harness/tests/test_fakegame_refugeewaves.py`.

### Requirement: The player is told about the wave
The mod SHALL show the banner "Refugees have arrived" and SHALL write a log line when a wave starts.

#### Scenario: Banner and log
- **WHEN** a wave starts
- **THEN** a banner is shown and a log line is written
- Checked by `harness/tests/test_fakegame_refugeewaves.py`.

### Requirement: Homeless refugees lower approval
The wave families SHALL stay homeless until the player builds homes. The game lowers approval by a one-time step for the homeless families. The mod adds no approval change of its own.

#### Scenario: Approval falls while homeless
- **WHEN** a wave is active and its families are homeless
- **THEN** approval falls by at least 3 points
- **AND** the wave stays active
- Checked by `harness/scenarios/refugee_wave.py`.

### Requirement: The wave ends when the families are housed
The mod SHALL end a wave with the outcome "housed" when the homeless count is back at the count from before the wave. Housing wins over any later check. Partly housed families keep the wave active.

#### Scenario: The player builds homes
- **WHEN** the player builds 5 burgage plots during a wave
- **THEN** the wave ends with the outcome "housed" within 24 game days
- **AND** no rebellion is counted and approval recovers by at least 2 points
- Checked by `harness/scenarios/refugee_wave.py`.

#### Scenario: Partly housed
- **WHEN** only some of the wave families have a home
- **THEN** the wave stays active
- Checked by `harness/tests/test_fakegame_refugeewaves.py`.

### Requirement: Impatient refugees turn into a raid
The mod SHALL end a wave with a rebellion when its families stay homeless for `homeless_days_limit` game days (default 30), or when approval falls under `approval_floor` (default 40). Then `rebel_share_percent` (default 50) of the homeless wave families leave and come back as a bandit raid. If the raid call fails, the wave ends as "rebellion_failed" and no family is removed.

#### Scenario: The timer ends the wave
- **WHEN** the families stay homeless for longer than the limit
- **THEN** the outcome is "rebelled" and one rebellion is counted
- **AND** about half of the wave families leave and bandit units appear
- Checked by `harness/scenarios/refugee_wave.py`.

#### Scenario: Low approval is a trigger too
- **WHEN** approval is under the floor before the day limit
- **THEN** the rebellion starts early
- **AND** approval exactly at the floor does not start it
- Checked by `harness/tests/test_fakegame_refugeewaves.py`.

### Requirement: A load adopts the homeless families
The mod SHALL keep no wave state in the save. After a load, homeless families found at the first check SHALL be the active wave, when `adopt_on_start` is true (default). The mod SHALL NOT call a save function.

#### Scenario: Adopt after a load
- **WHEN** the first check finds homeless families and no wave is active
- **THEN** they become the active wave
- **AND** with `adopt_on_start` off, or after the first check, nothing is adopted
- Checked by `harness/tests/test_fakegame_refugeewaves.py`.

### Requirement: The mod runs without the harness
The mod SHALL load with the shared module ManorCore only. Without the harness registry only the test commands are missing. With it, the mod SHALL register `RefugeeWaves.configure`, `start_wave`, `check`, `status` and `forget_wave`, and reject bad settings.

#### Scenario: Commands and bad settings
- **WHEN** the harness registry is present and a test sends a bad setting
- **THEN** the commands and metrics are registered and the bad setting is refused
- Checked by `harness/tests/test_fakegame_refugeewaves.py`.
