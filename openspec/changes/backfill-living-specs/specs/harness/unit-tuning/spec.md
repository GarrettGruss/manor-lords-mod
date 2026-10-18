# Spec Delta

## Purpose

Live unit tuning lets a person or an agent change combat stats of a whole side in the running game and watch the effect. Overrides live in the running game only. The parts are the commands of `HarnessTune`, the client `harness/runlib/tune.py` and the Streamlit page `harness/tools/tune_ui.py`.

## ADDED Requirements

### Requirement: The state of every side
The command `tune_state` SHALL report, for the sides `player`, `bandit`, `ai_lord` and `other`, and for each squad: the number of living units, the mean of each stat, the active overrides, the number of living units without an owner, and the timer state. It SHALL work in a normal game without a harness spawn registry.

#### Scenario: Sides without a registry
- **WHEN** units of several sides live in the game and none were spawned by the harness
- **THEN** `tune_state` lists each side with its living units and mean stats
- Checked by `harness/tests/test_fakegame_harnesstune.py`.

### Requirement: Set a stat for a side or a squad
The command `tune_set` SHALL write one stat (`att`, `def`, `block`, `armorPierce`, `morale` or `charge`) on all living units of one side, or of one squad, and SHALL keep it as an override. The value SHALL be a number from 0 up to the maximum stat value. The command SHALL refuse an unknown side, an unknown field, a bad value, a missing scope, and both side and squad together. A dead unit SHALL NOT be written. An override for one squad SHALL win over the value of its side.

#### Scenario: A side is changed
- **WHEN** a scenario sets `att` for the side `bandit`
- **THEN** all living bandit units get the value, other sides do not change, and `tune_state` shows the override
- Checked by `harness/tests/test_fakegame_harnesstune.py`.

#### Scenario: Bad input
- **WHEN** the side, field or value is bad, or the scope is missing or doubled
- **THEN** the command is refused with a message and nothing is written
- Checked by `harness/tests/test_fakegame_harnesstune.py`.

#### Scenario: Squad over side
- **WHEN** a side value and a squad value are both set
- **THEN** units of that squad get the squad value
- Checked by `harness/tests/test_fakegame_harnesstune.py`.

### Requirement: Overrides reach later units
A timer SHALL apply the active overrides again every 2 seconds, so units that spawn later get them. Without an override, the timer SHALL write nothing. The command `tune_apply` SHALL run one pass at once.

#### Scenario: A later unit
- **WHEN** a unit spawns after `tune_set`
- **THEN** it has the override within the timer period of 2 s
- Checked by `harness/tests/test_fakegame_harnesstune.py`.

#### Scenario: No override
- **WHEN** no override exists
- **THEN** no stat is written
- Checked by `harness/tests/test_fakegame_harnesstune.py`.

### Requirement: Reset restores the original values
The command `tune_reset` SHALL remove overrides and restore the value that a unit had before its first write. Without arguments it SHALL remove all overrides. With a side or squad, or a field, it SHALL remove only those and keep the others. It SHALL refuse bad input.

#### Scenario: Reset all
- **WHEN** a scenario resets after setting stats, with a late unit present
- **THEN** all units, also the late ones, have their original values again
- Checked by `harness/tests/test_fakegame_harnesstune.py`.

#### Scenario: Reset one side and field
- **WHEN** a scenario resets one side and one field
- **THEN** the other overrides stay active
- Checked by `harness/tests/test_fakegame_harnesstune.py`.

#### Scenario: Original value
- **WHEN** a stat is set twice before a reset
- **THEN** the reset restores the value from before the first write
- Checked by `harness/tests/test_fakegame_harnesstune.py`.

### Requirement: The tune client talks to a running game
The module `harness/runlib/tune.py` SHALL send the tune commands to the command folder of a running game and SHALL NOT start the game. A run can take commands when it has a `commands` folder or a `ready.marker`. Without `--run`, the newest such run SHALL be used, and a missing run SHALL fail with a clear message. A second client SHALL continue after the highest request number. A spawn group count outside 1 to 6 SHALL be refused before any command is sent.

#### Scenario: Round trip
- **WHEN** a client reads the state, sets a value and resets it
- **THEN** each command is answered, and a refusal raises an error with the reason
- Checked by `harness/tests/test_fakegame_tuneclient.py`.

#### Scenario: No live run
- **WHEN** no run has a commands folder or a ready marker
- **THEN** the lookup fails with a message that names the command to start a game
- Checked by `harness/tests/test_fakegame_tuneclient.py`.

#### Scenario: Spawn count
- **WHEN** a group count is 0 or 7
- **THEN** the client raises an error before it sends anything
- Checked by `harness/tests/test_fakegame_tuneclient.py`.

### Requirement: Presets are exported as files
The client SHALL turn the active overrides into a preset `{created, run, overrides}` with the values grouped by side. It SHALL write the preset as `<name>.json` in the chosen folder through a `.tmp` file and a rename. The file name SHALL keep only letters, digits, `-` and `_`.

#### Scenario: Export
- **WHEN** a preset is exported with a name that has unsafe characters
- **THEN** the file name is clean and the content groups the overrides by side
- Checked by `harness/tests/test_fakegame_tuneclient.py`.

### Requirement: The tuning page shows command errors
The Streamlit page `harness/tools/tune_ui.py` SHALL start with `uv run streamlit run harness/tools/tune_ui.py -- --run <id>`. It SHALL show state, sliders to apply and reset overrides, a button to spawn a test fight, and a preset export. It SHALL show a command error on the page and not stop.

#### Scenario: The page runs against a game
- **WHEN** a person starts the page against a game that was started with `--keep-open`
- **THEN** the page shows the state, applies an override, and shows an error when a command fails
- Not checked yet.
