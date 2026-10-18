# Spec Delta

## Purpose

Named harness commands that read the start settings and the victory goal of the running game, and set the goal. A test uses them to stop the victory screen after a region claim.

## ADDED Requirements

### Requirement: The game start settings are read only
The harness SHALL answer `game_setup_state` with the goal, the victory status, the difficulty, the scenario name, the number of generic AI lords, the starting supplies multiplier and the starting day. `game_setup_state` SHALL NOT change the game. The harness SHALL answer with an error when no game instance exists.

#### Scenario: Read the settings
- **WHEN** a client sends `game_setup_state` in a running game
- **THEN** the reply is ok and has the goal, the victory status and the difficulty
- Not checked yet.

#### Scenario: No game instance
- **WHEN** a client sends `game_setup_state` and no game instance exists
- **THEN** the reply is not ok and says that there is no game instance
- Not checked yet.

### Requirement: The victory goal can be set
The harness SHALL write the goal on `game_setup_set_goal` with `goal` a whole number from 0 to 3 (0 Conquest, 1 Dominance, 2 Endless, 3 Growth). The reply SHALL give the settings before and after. The harness SHALL refuse a goal that is missing, not a whole number, or outside 0 to 3, and SHALL write nothing then.

#### Scenario: Set the goal to Endless
- **WHEN** a client sends `game_setup_set_goal` with `goal` 2
- **THEN** the reply is ok and the goal after the write reads 2
- Not checked yet.

#### Scenario: A goal outside the range
- **WHEN** a client sends `game_setup_set_goal` with `goal` 4, or with no goal
- **THEN** the reply is not ok and the goal is unchanged
- Not checked yet.
