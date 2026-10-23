## ADDED Requirements
<!-- Issue: #425 -->

### Requirement: A new game starts with the scenario kit
When the player clicks "Begin the game" in a new game (or the settings are applied by command), the mod SHALL give the player a start kit once: 10 villagers and 300 starting silver. The amounts SHALL come from config values. The mod SHALL NOT give the kit for a game loaded from a save, and SHALL NOT give it a second time. The mod SHALL store in the mod state that the kit was given, so it is saved with the game.

#### Scenario: A new game gets the kit
- **WHEN** a new game starts and the player clicks "Begin the game"
- **THEN** the village has 10 people and the player pawn property `silver` is 300
- **AND** the mod state holds the entry "kit given"
- Checked by `mod/InvasionMod/scenarios/scenario_settings/start_kit.py` (proposed) and `harness/tests/test_fakegame_scenario_settings.py` (proposed).

#### Scenario: A loaded save gets no kit
- **WHEN** a save loads, with or without the entry "kit given"
- **THEN** no silver and no villagers are added
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (proposed).

#### Scenario: The kit is given once
- **WHEN** the settings are applied a second time in the same game (for example by command)
- **THEN** no second kit is given
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (proposed).

### Requirement: The villagers replace the start population
The 10 villagers SHALL be 10 people (the count in the top bar) and SHALL replace the start population, not add to it. The 300 silver SHALL set the silver of the player pawn to 300.

#### Scenario: Ten people in total
- **WHEN** a new game begins
- **THEN** the village has exactly 10 people
- Checked by `mod/InvasionMod/scenarios/scenario_settings/start_kit.py` (proposed).
