## MODIFIED Requirements
<!-- Issue: #358 -->

### Requirement: The player picks the difficulty once
The mod SHALL keep a difficulty from 1 to 3. The player SHALL set it before the game starts, as a new game setting (name decided by the spike). The mod SHALL store the value in the save with the mod state. If the game has its own raider difficulty setting that Lua can read, the mod SHALL read that setting instead of its own option. For a game with no stored value, the difficulty SHALL be `invasion.difficulty` (default). The mod SHALL NOT show the pick banner. A named command SHALL set the difficulty at any time while the game runs, refuse a value outside 1 to 3, and re-plan the squads of an unspawned raid.

#### Scenario: The difficulty is set at the start of a new game
- **WHEN** a new game starts with the setting at 3
- **THEN** the difficulty is 3 and is stored in the mod state
- Not checked yet.

#### Scenario: The value survives save and load
- **WHEN** the game is saved with difficulty 3 and loaded
- **THEN** the difficulty is 3
- Not checked yet.

#### Scenario: The command sets the difficulty after a raid spawned
- **WHEN** a test sets difficulty 2 with the command at any time
- **THEN** the difficulty is 2
- Not checked yet.

#### Scenario: A pick at difficulty 2
- **WHEN** no pick was made and a test picks difficulty 2
- **THEN** `chosen` was false before and is true after, and the difficulty is 2
- Checked by `mod/InvasionMod/scenarios/invasion/difficulty_pick.py`.
