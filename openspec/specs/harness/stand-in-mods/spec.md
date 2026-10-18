# harness/stand-in-mods Specification

## Purpose
The stand-in mods are toy models of mod-defined logic (outposts, captives, tribute, raids). They prove that the harness can drive and observe the state that a mod defines, before or beside the real mod. They are test fixtures, not player mods.

## Requirements

### Requirement: Stand-ins use the mod command contract only
The mods `InvasionStandIn` and `RaidStandIn` SHALL register their commands and metrics in `HarnessCommands` under their own mod name. They SHALL keep their state in plain Lua tables. They SHALL NOT add a game hook or a loop other than the command poller. Their only game read SHALL be the day counter.

#### Scenario: Names and registration
- **WHEN** a stand-in loads
- **THEN** every command and metric has the mod name as prefix and is served from the own Lua state of the mod
- Checked by `harness/tests/test_fakegame_invasionstandin.py`.

#### Scenario: No extra loop
- **WHEN** a stand-in loads next to the other harness mods
- **THEN** it adds no loop except the command poller
- Checked by `harness/tests/test_fakegame_invasionstandin.py`.

#### Scenario: Load again
- **WHEN** a stand-in is loaded again (hot reload)
- **THEN** it starts with a fresh state and one poller
- Checked by `harness/tests/test_fakegame_invasionstandin.py`.

### Requirement: Stand-ins follow the game days
Each stand-in command and metric read SHALL first run the toy rules for every game day that passed since the last call. Without a game map, the commands SHALL still work and the toy time SHALL NOT move. `RaidStandIn` SHALL also offer `set_day` and `advance_days` to move the toy day by hand.

#### Scenario: Days between two calls
- **WHEN** several game days pass between two calls
- **THEN** all passed days are counted by the toy rules
- Checked by `harness/tests/test_fakegame_invasionstandin.py`.

#### Scenario: No engine
- **WHEN** no game map is loaded
- **THEN** the commands work and the day does not move
- Checked by `harness/tests/test_fakegame_invasionstandin.py`.

#### Scenario: Manual days
- **WHEN** a scenario calls `RaidStandIn.advance_days`
- **THEN** the toy rules run for each day, and the toy day moves without the game
- Checked by `harness/tests/test_fakegame_raidstandin.py`.

### Requirement: Outposts, evacuation, captives and tribute
`InvasionStandIn` SHALL model outposts (found, lose, upgrade, level 1 to 3), raid reveal by scouting range, the raid target (the lowest-numbered alive outpost, then the town), evacuation of families and grain between regions, captives with ransom, and tribute of the kinds `payment`, `hostages` and `vassal`. An unprotected alive outpost SHALL pay tribute and leak intel after 3 game days. A command that breaks a rule SHALL be refused and change nothing.

#### Scenario: Outpost rules
- **WHEN** a scenario founds, upgrades and loses outposts
- **THEN** level, trade value and scouting range follow the toy formulas, and a lost outpost has none and may be founded again
- Checked by `harness/tests/test_fakegame_invasionstandin.py`.

#### Scenario: Reveal and target
- **WHEN** a raid is revealed with a distance
- **THEN** it is seen only when the distance is not more than the scouting range of an alive outpost, and raiders hit the lowest alive outpost first
- Checked by `harness/tests/test_fakegame_invasionstandin.py`.

#### Scenario: Evacuation and captives
- **WHEN** a scenario evacuates families and grain, captures and frees captives
- **THEN** both regions are read back, bad counts are refused, and nothing changes after a refusal
- Checked by `harness/tests/test_fakegame_invasionstandin.py`.

#### Scenario: Tribute
- **WHEN** a scenario offers a payment, hostages or a vassal tribute
- **THEN** a payment moves silver, hostages cost no silver, a vassal pays each toy year and never more than the treasury holds, and a second vassalage is refused
- Checked by `harness/tests/test_fakegame_invasionstandin.py`.

#### Scenario: Reset
- **WHEN** a scenario calls `InvasionStandIn.reset`
- **THEN** all toy state returns to its start values
- Checked by `harness/tests/test_fakegame_invasionstandin.py`.

### Requirement: Stand-in scenarios prove the test method
The scenarios `standin-outposts`, `standin-captives` and `standin-tribute` SHALL pass on the stand-in and SHALL fail loudly when the mod breaks a rule. They SHALL fail when the mod does not register its commands.

#### Scenario: Scenarios pass on the stand-in
- **WHEN** the three scenarios run against the stand-in in the fake game
- **THEN** all pass, and they can run twice in one game
- Checked by `harness/tests/test_fakegame_standin_scenarios.py`.

#### Scenario: A broken rule fails the scenario
- **WHEN** the mod has no commands, a blind outpost that still sees, a tribute never charged, or a metric that stays zero
- **THEN** the covering scenario fails with a clear message
- Checked by `harness/tests/test_fakegame_standin_scenarios.py`.

### Requirement: Raid director toy
`RaidStandIn` SHALL model a raid director: a raid is planned, announced a set number of days before arrival, and then arrives. Only one raid SHALL be scheduled at a time. A timer shorter than the lead time SHALL announce at once. The tier (1 to 4) SHALL set size, gap, variety, targeting and breaking point. The calendar SHALL have 360 days with 90 days a season. Automatic raids SHALL arrive only in the allowed season of their faction, and winter SHALL pause an active raid.

#### Scenario: Announcement
- **WHEN** a raid is planned with an announce lead time of N days
- **THEN** it is announced N days before arrival, or at once when the timer is shorter
- Checked by `harness/tests/test_fakegame_raidstandin.py`.

#### Scenario: Seasons
- **WHEN** a scenario runs three toy years of automatic raids
- **THEN** no raid arrives in winter and both factions raid in their seasons
- Checked by `harness/tests/test_fakegame_raidstandin.py`.

#### Scenario: Tiers
- **WHEN** the tier rises from 1 to 4
- **THEN** raids are bigger and more frequent, and the announced kind is the dominant unit type
- Checked by `harness/tests/test_fakegame_raidstandin.py`.

### Requirement: Raid behavior, warlord and sack toy
`RaidStandIn` SHALL end a raid with a retreat reason: `leader_dead`, `morale_break`, `full_loot` or `timer_end`. At the top tier only `leader_dead` SHALL end it. A raid that retreats with a living leader SHALL raise the warlord level (up to 5). A dead leader SHALL reset it. Sacks inside the sack window that reach the sack limit SHALL set `game_over` true. A command that forces a retreat without an active raid SHALL be refused.

#### Scenario: Retreat triggers
- **WHEN** a scenario forces each retreat condition in a fresh raid
- **THEN** the raid ends with the matching reason, and at the top tier only a dead leader ends it
- Checked by `harness/tests/test_fakegame_raidstandin.py`.

#### Scenario: Warlord
- **WHEN** a raid escapes with its leader alive
- **THEN** the next raid is bigger, and a dead leader resets the level
- Checked by `harness/tests/test_fakegame_raidstandin.py`.

#### Scenario: Sack limit
- **WHEN** two sacks fall inside the sack window
- **THEN** `game_over` is true, and a sack outside the window is forgotten
- Checked by `harness/tests/test_fakegame_raidstandin.py`.

### Requirement: Seeded randomness
`RaidStandIn` SHALL use a seeded random generator. The same seed SHALL give the same raids and another seed SHALL not. The raid scenarios SHALL take a base seed from the run folder name and write it to `scenario.log`.

#### Scenario: Repeatable run
- **WHEN** two runs use the same seed
- **THEN** their raids are equal
- Checked by `harness/tests/test_fakegame_raidstandin.py`.

#### Scenario: Scenarios with many run names
- **WHEN** the random raid scenarios run with many run names
- **THEN** they pass for each
- Checked by `harness/tests/test_fakegame_raid_scenarios.py`.

### Requirement: Raid size setting from the environment
`RaidStandIn` SHALL read `RAID_STANDIN_SIZE_PERCENT` when it loads. The value SHALL be a number from 10 to 1000 (default 100) and it SHALL scale raid sizes. A bad value SHALL stop the mod with an error. A suite variant SHALL be able to set it with `env`.

#### Scenario: Scaled size
- **WHEN** the variable is 150
- **THEN** the raid size is larger than at 100, and the A/B suite `raid-size-ab` reports a difference
- Checked by `harness/tests/test_fakegame_raid_scenarios.py`.

#### Scenario: A bad value
- **WHEN** the variable is 5
- **THEN** the mod stops with an error that names the variable
- Checked by `harness/tests/test_fakegame_raidstandin.py`.

### Requirement: Laws and settlement toy
`RaidStandIn` SHALL model the laws `conscription`, `tithe` and `cuman_pact`, the war economy, food and morale. A law the town cannot pay SHALL be refused. Morale SHALL stay between 0 and 100. Food SHALL not fall below 0.

#### Scenario: Laws
- **WHEN** a scenario enacts a law
- **THEN** silver, food, defense or morale change by the toy rules, and the cuman pact halves cuman raids only
- Checked by `harness/tests/test_fakegame_raidstandin.py`.

#### Scenario: Limits
- **WHEN** the threat runs long
- **THEN** morale stays between 0 and 100 and food stays at 0 or more
- Checked by `harness/tests/test_fakegame_raidstandin.py`.
