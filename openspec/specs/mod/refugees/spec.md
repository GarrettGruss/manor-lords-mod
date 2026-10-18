# mod/refugees Specification

## Purpose
A lost vassal sends refugee families to the home region. The player must house them, or the unhoused families turn into bandits.

## Requirements

### Requirement: A lost vassal sends a refugee wave
The mod SHALL send a wave of refugee families to the home region when a vassal is lost. The wave size SHALL be `ceil(vassal families x share)` with a share between `share_min` and `share_max` (default 0.30 and 0.60), and at least 1 family. The mod SHALL show the banner "Refugees have arrived".

#### Scenario: A vassal is lost
- **WHEN** a handed-over vassal of 5 families is lost
- **THEN** the home region gains 5 families and the wave is active
- **AND** the home region has at least 1 homeless family when it has fewer than 5 free home slots
- Checked by `mod/InvasionMod/scenarios/refugees/refugee_wave.py`.

#### Scenario: The loss starts the wave by itself
- **WHEN** the vassals feature reports a lost vassal in the fake game
- **THEN** the refugees feature sends a wave without a command
- Checked by `harness/tests/test_fakegame_refugees.py`.

### Requirement: Families arrive in steps of 5
The mod SHALL bring the wave in with `settleRegion` calls on the home region. One call SHALL add 5 families (`families_per_call`). The number of calls SHALL be the wave families divided by 5, rounded to the nearest whole number, at least 1 and at most `max_calls` (default 3). Free home slots take the first families. The others SHALL wait as homeless in the tent camp.

#### Scenario: A small and a large wave
- **WHEN** a wave of 2 families and a wave of 40 families are computed
- **THEN** the small wave makes 1 call and the large wave makes 3 calls
- Checked by `harness/tests/test_fakegame_refugees.py`.

### Requirement: Refugees lower approval while they are homeless
The mod SHALL leave approval and food to the game. The homeless refugees SHALL lower the approval of the home region while they stay.

#### Scenario: Approval falls
- **WHEN** a wave is active and the refugees stay homeless for 4 game days
- **THEN** the approval of the home region falls by at least 3
- Checked by `mod/InvasionMod/scenarios/refugees/refugee_wave.py`.

### Requirement: Only one wave is active
The mod SHALL refuse a new wave while a wave is active, and when the home region is not known. The mod SHALL keep the wave state (active, start day, homeless base, wave families, outcome counters) in ModState. A new wave SHALL be possible after the wave ends.

#### Scenario: A second wave
- **WHEN** a second wave starts while the first is active
- **THEN** the second wave is refused and nothing changes
- Checked by `mod/InvasionMod/scenarios/refugees/refugee_wave.py`.

#### Scenario: A wave after the end
- **WHEN** a wave has ended
- **THEN** a new wave starts
- Checked by `harness/tests/test_fakegame_refugees.py`.

### Requirement: A housed wave ends housed
The mod SHALL poll an active wave every `poll_ms` (default 4000 ms). The unhoused families SHALL be the homeless families now minus the homeless base at the wave start. When the unhoused count is 0 or lower, the wave SHALL end with the outcome `housed`.

#### Scenario: The player builds homes
- **WHEN** the player builds homes for the refugees during a wave
- **THEN** the wave ends `housed` within 24 game days
- **AND** no family of the wave turned to bandits
- Checked by `mod/InvasionMod/scenarios/refugees/housing_and_timeout.py`.

#### Scenario: Active while homeless
- **WHEN** the refugees stay homeless
- **THEN** the wave stays active
- Checked by `harness/tests/test_fakegame_refugees.py`.

### Requirement: Unhoused refugees turn into bandits
When a wave is `timeout_days` old (default 45 game days) and refugees are still unhoused, the mod SHALL turn at most `max_rebel_families` (default 6) unhoused families into bandits, in squads of `families_per_squad` (default 2), through the bandits route. The outcome SHALL be `rebelled`. When the rebellion call fails, the wave SHALL stay active, the error SHALL be logged, and the next poll SHALL retry.

#### Scenario: The timeout passes
- **WHEN** a wave has a timeout of 3 game days and the refugees stay unhoused
- **THEN** the wave ends `rebelled`
- **AND** the converted families are between 1 and the unhoused count
- **AND** bandit units appear and the home region loses those families
- Checked by `mod/InvasionMod/scenarios/refugees/housing_and_timeout.py`.

#### Scenario: A failed rebellion
- **WHEN** the rebellion call fails
- **THEN** the wave stays active and the next poll tries again
- Checked by `harness/tests/test_fakegame_refugees.py`.

### Requirement: The feature offers named commands
The mod SHALL register `InvasionMod.refugees_state`, `refugees_vassal_lost`, `refugees_send_wave` and `refugees_set_timeout`. `refugees_vassal_lost` SHALL take a slot and an optional share in percent. `refugees_set_timeout` SHALL change the timeout for one session, from 1 to 120 days. An empty slot SHALL be refused.

#### Scenario: Timeout command
- **WHEN** a scenario sends `refugees_set_timeout` with 3 days
- **THEN** `refugees_state` reports a timeout of 3 days
- Checked by `harness/tests/test_fakegame_refugees.py`.
