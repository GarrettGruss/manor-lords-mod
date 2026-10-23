## ADDED Requirements
<!-- Issue: #339 -->

### Requirement: No raid comes in the first game year
The mod SHALL NOT plan or spawn a raid in the first game year after the game start. Base game raids stay lifted (see "The mod owns the base game raid timer").

#### Scenario: The first year is quiet
- **WHEN** the 3 season changes of the first game year pass (a fake game test moves the calendar by real season changes; the real game test scenario runs the first days and counts the other changes with a test command)
- **THEN** no raid is planned and the log has no raid spawn event
- Checked by `harness/tests/test_fakegame_invasion.py` and `mod/InvasionMod/scenarios/invasion/yearly_raid.py`.

### Requirement: One raid comes in each later game year, by a season roll
From the second game year, the mod SHALL roll at each season change while no raid was done in the current game year. The chance of the roll SHALL be `yearly.chance_by_season` (default 25, 33, 50 and 100 percent for the first to the fourth season). A successful roll SHALL plan one raid in that season. The mod SHALL spawn at most one raid in a game year. The year, the roll state and the planned raid SHALL be kept in ModState and SHALL survive a load. A season SHALL NOT be rolled twice.

#### Scenario: Chances by season
- **WHEN** a test runs the season roll with the roll value 0.2 in the first season of year 2
- **THEN** a raid is planned
- **AND** with the roll value 0.9 no raid is planned and the second season rolls next
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: The last season always raids
- **WHEN** no raid was planned in the first three seasons of year 2
- **THEN** a raid is planned in the fourth season, whatever the roll value is
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: One raid a year
- **WHEN** 3 game years pass in a test scenario
- **THEN** exactly 2 raids spawn (years 2 and 3), at most one in each year
- Checked by `harness/tests/test_fakegame_invasion.py` (3 years of real season changes) and `mod/InvasionMod/scenarios/invasion/yearly_raid.py` (season changes counted by a test command).

#### Scenario: A load does not repeat a roll
- **WHEN** the game is loaded in a season that was already rolled
- **THEN** no new roll runs in that season
- Checked by `harness/tests/test_fakegame_invasion.py`.

## REMOVED Requirements

### Requirement: The first minor raid is planned within a day range
**Reason**: Owner decision 2026-10-20: one raid per year, none in the first year, timed by a season roll.
**Migration**: Use "One raid comes in each later game year, by a season roll". The settings `first_raid_days_min` and `first_raid_days_max` are removed.

### Requirement: A subjugation raid follows the first raid
**Reason**: The timing of every raid now follows the yearly rule. A fixed wait after the first raid conflicts with one raid per year.
**Migration**: The subjugation raid is planned by the yearly roll like any raid. Its size and behavior rules move to the requirement "A subjugation raid is large and does not plunder" below.

## ADDED Requirements

### Requirement: A subjugation raid is large and does not plunder
A subjugation (major) raid SHALL be large: 3 x difficulty squads. It SHALL be a lord raid that does not plunder and does not leave. The yearly roll SHALL pick the kind of the raid by the kind rules: the first yearly raid is a plunder raid, the second is the subjugation raid (once), and every later yearly raid is a plunder raid.

#### Scenario: The subjugation raid at difficulty 1
- **WHEN** a subjugation raid spawns
- **THEN** it has 3 squads x difficulty
- **AND** the tracker shows `kind = subjugation`, no plunder and no leave reason within 12 game days
- Checked by `mod/InvasionMod/scenarios/invasion/subjugation_raid.py`.
