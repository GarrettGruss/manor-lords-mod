# harness/game-actions Specification

## Purpose
The game actions let a scenario create a game situation (resources, time, raids, letters, building placement) and prove that the change happened. The kit is the Python class `Actions` (`ctx.actions`) and the helper mods `HarnessActions` and `HarnessPlace`.

## Requirements

### Requirement: Every action reads the state back
The action kit SHALL run each action in four steps: check that the game world is loaded, read the state, make the change, read the state again. It SHALL return a record with `action`, `ok`, `args`, `before` and `after`, and add a short line to the scenario notes.

#### Scenario: A change that holds
- **WHEN** a scenario calls `ctx.actions.add_silver(100)` and the game applies it
- **THEN** the record has `ok` true and `after` minus `before` equal to 100
- **AND** the scenario notes get one line for the action
- Checked by `harness/tests/test_runlib_actions.py`.

#### Scenario: A change that the game ignores
- **WHEN** an action writes a value and the read-back differs
- **THEN** the record has `ok` false
- **AND** the run records a failed assertion named "action <name> read-back", so the verdict is `fail`
- Checked by `harness/tests/test_runlib_actions.py`.

#### Scenario: The game world is not loaded or the game ended
- **WHEN** an action runs and the world is not loaded, or the game process has ended
- **THEN** the action raises `ActionError`, or the liveness error, before any change
- Checked by `harness/tests/test_runlib_actions.py`.

#### Scenario: Silver in the real game
- **WHEN** the scenario `silver-change` sets, adds and takes silver while the game is paused
- **THEN** the player value, the HUD number and the telemetry show 650
- Checked by `harness/scenarios/silver_change.py`.

### Requirement: Unknown and impossible actions fail loudly
The action kit SHALL raise `ActionNotPossible` for an unknown action name, a name in the `NOT_POSSIBLE` list, or a name that starts with an underscore. The message SHALL give the reason, or list the available actions. The scenario runner SHALL turn the error into a failed scenario.

#### Scenario: A known impossible action
- **WHEN** a scenario calls `ctx.actions.spawn_raiders()` or `choose_raid_type`
- **THEN** `ActionNotPossible` is raised with the reason from `NOT_POSSIBLE`
- **AND** the scenario ends with the verdict `fail` and a clear message, not a crash
- Checked by `harness/tests/test_runlib_actions.py`.

#### Scenario: An unknown action
- **WHEN** a scenario calls `ctx.actions.run("no_such_action")`
- **THEN** `ActionNotPossible` lists the available action names
- Checked by `harness/tests/test_runlib_actions.py`.

#### Scenario: The hidden self-test in the real game
- **WHEN** the hidden scenario `selftest-action` calls an impossible action
- **THEN** it fails with a clear message
- Checked by `harness/scenarios/selftest_action.py`.

### Requirement: Unchecked values are refused
The action kit SHALL accept only values that were checked in the real game: season names (`winter`, `spring`, `summer`, `autumn`), item names (`timber`, `planks`, `fish`) or item ids, letter paragraphs (`welcome_from_hildebolt`), and region values (`Approval`, `publicOrder`, `regionalWealth`, `supplies_food`). It SHALL raise `ActionNotPossible` for other values.

#### Scenario: Unknown season or item name
- **WHEN** a scenario calls `set_season("monsoon")` or `give_item("gold", 1)`
- **THEN** `ActionNotPossible` is raised and nothing is changed in the game
- Checked by `harness/tests/test_runlib_actions.py`.

#### Scenario: Region and weather values
- **WHEN** a scenario sets `Approval` and `regionalWealth` after `set_season("winter")`
- **THEN** the date is in winter and the region values hold at the read-back
- Checked by `harness/scenarios/winter_region.py`.

### Requirement: Resource and time actions
The action kit SHALL provide actions for the player's resources and the clock: `add_silver`, `set_silver`, `add_influence`, `set_influence`, `add_kings_favour`, `give_item`, `set_day`, `set_season`, `set_region_value`, `add_regional_wealth`, `set_settlement_level` and `set_weather`. Each SHALL be verified by its read-back. An action that targets a region SHALL use the player region unless a region name is given.

#### Scenario: Calendar actions
- **WHEN** a scenario calls `set_day` or `set_season`
- **THEN** the read-back checks the day and the season of the calendar
- Checked by `harness/tests/test_runlib_actions.py`.

#### Scenario: A region name that does not exist
- **WHEN** a scenario names a region that the game does not have
- **THEN** the action raises an error that names the region
- Checked by `harness/tests/test_runlib_actions.py`.

### Requirement: Raid and unit actions
The action kit SHALL provide raid, unit and sack actions through the helper mod, for example `set_raid_timer`, `spawn_raid`, `spawn_bandit_camp`, `units_census`, `kill_units`, `drop_loot`, `spawn_units` and `sack_village`. A spawn action SHALL check the change in bandit units against the squad size (18 for each squad, 54 for an elite raid).

#### Scenario: A spawn with the wrong size
- **WHEN** the game adds a different number of units than the action expects
- **THEN** the record has `ok` false
- Checked by `harness/tests/test_runlib_raids.py`.

#### Scenario: A raid in the real game
- **WHEN** the scenario `raid-spawn` calls `spawn_raid`
- **THEN** the number of bandit units rises by 18 for each squad
- Checked by `harness/scenarios/raid_spawn.py`.

#### Scenario: The raid timer
- **WHEN** a scenario calls `set_raid_timer(3)` and runs game days
- **THEN** the timer falls by one each game day and a raid spawns on the day it reaches 0
- Checked by `harness/scenarios/raid_timer.py`.

### Requirement: Letters
The action kit SHALL provide `send_letter(paragraphs, sender)`, which makes an AI lord send a letter to the player through the `HarnessActions` command `send_letter`. The check SHALL be that the player InBox holds one more letter with the same paragraphs.

#### Scenario: A letter arrives
- **WHEN** a scenario sends the paragraph `welcome_from_hildebolt`
- **THEN** the InBox count rises by 1 and the last letter has that paragraph and an AI lord as sender
- Checked by `harness/scenarios/letter_delivery.py`.

#### Scenario: A letter that does not arrive
- **WHEN** the InBox does not change
- **THEN** the record has `ok` false
- Checked by `harness/tests/test_runlib_actions.py`.

### Requirement: Real-mouse building placement
The action `place_building(type_id, fx, fy)` SHALL place a building with a real OS left click at a fraction of the game window. It SHALL take the OS input lock, bring the game window to the front, check that the cursor is over the window and over ground, and restore the cursor afterwards. It SHALL refuse to click when the window is not in front or no ground is under the cursor. The check SHALL be that the player region has one more building of that type.

#### Scenario: No click without focus or ground
- **WHEN** another window is in front, the cursor is outside the game window, or the cursor is not over ground
- **THEN** no click is sent
- **AND** the button is released and the game is paused again after an error
- Checked by `harness/tests/test_runlib_osinput.py`.

#### Scenario: The context has no mouse
- **WHEN** `place_building` runs in a context without a mouse placer
- **THEN** it raises `ActionNotPossible`
- Checked by `harness/tests/test_runlib_osinput.py`.

#### Scenario: A building is placed in the real game
- **WHEN** the hidden scenario `place-building` places a HitchingPost
- **THEN** the player region has one more HitchingPost and the cursor ends within 2 px of its start
- Checked by `harness/scenarios/place_building.py`.

### Requirement: Mouse-free placement mod
The mod `HarnessPlace` SHALL do nothing until the command `HarnessPlace.arm` runs. After that it SHALL write a chosen world point into the building preview on each pawn tick, so a building can be placed with no mouse device. It SHALL offer the commands `arm`, `disarm`, `state`, `bp`, `press` and `release`, with limited numeric arguments (world limit 200000, building type 1 to 600).

#### Scenario: The mod is armed
- **WHEN** a scenario calls `HarnessPlace.arm` with a point and a building type
- **THEN** the building mode is active and `HarnessPlace.state` reports the ghost location
- Not checked yet.

### Requirement: Unsafe spike commands need an opt-in
The unsafe test commands SHALL be refused unless the game process runs with `HARNESS_ALLOW_UNSAFE=1`. The refusal text SHALL name the variable. Unsafe commands are for test games, never for a user save.

#### Scenario: Refusal without the variable
- **WHEN** a scenario sends `master_part_add` or `master_part_remove` and the variable is not set
- **THEN** the command is refused with a message that contains `HARNESS_ALLOW_UNSAFE=1`
- Checked by `harness/tests/test_fakegame_harnessparts.py`.

### Requirement: Helper mod command channel
The helper mod `HarnessActions` SHALL read numbered request files `<run>/commands/<nnnn>.json` in order, run each command on the game thread, and write `<nnnn>.result.json`. Both sides SHALL write a `.tmp` file and then rename it. The client SHALL wait at most 10 s for an answer. The mod SHALL refuse an unknown command, a bad number and bad input before any game call.

#### Scenario: Normal exchange
- **WHEN** the client sends `ping`
- **THEN** the mod answers with its version, and the next request gets the next number
- Checked by `harness/tests/test_fakegame_harnessactions.py`.

#### Scenario: Refusal and silence
- **WHEN** the mod answers `ok` false, or does not answer in 10 s
- **THEN** the client raises `CommandRefused` with the reason, or a `CommandError` with a hint, and a dead game stops the wait
- Checked by `harness/tests/test_runlib_actions.py`.

#### Scenario: Bad input
- **WHEN** a request has an unknown command, the wrong number or bad values
- **THEN** the mod writes an error result and makes no game call
- Checked by `harness/tests/test_fakegame_harnessactions.py`.
