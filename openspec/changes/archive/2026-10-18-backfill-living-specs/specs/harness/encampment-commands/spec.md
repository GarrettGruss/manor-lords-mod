# Spec Delta

## Purpose

Named harness commands that find camp sites and regions and that spawn, list and remove a placed actor from a pak Blueprint. A spike uses them to test a custom camp mesh in neutral or AI territory.

## ADDED Requirements

### Requirement: Camp sites and regions are read only
The harness SHALL list the building masters of one type on `encampment_sites` with `type` (default 100, the bandit camp), at most 20 rows. Each row SHALL give the name, type, constructed flag, class, position, region, owner and part count. `encampment_regions` SHALL list every region with its owner, settled flag, position and town center position. Both commands SHALL NOT change the game.

#### Scenario: Only the asked type
- **WHEN** a client sends `encampment_sites` with a `type`
- **THEN** only masters of that type are listed
- Checked by `harness/tests/test_fakegame_harnessencampment.py`.

#### Scenario: A type with no masters
- **WHEN** a client sends `encampment_sites` with a type that no master has
- **THEN** the reply is ok with an empty list
- Checked by `harness/tests/test_fakegame_harnessencampment.py`.

#### Scenario: Regions
- **WHEN** a client sends `encampment_regions`
- **THEN** every region is listed with owner and settled flag
- Not checked yet.

### Requirement: A pak actor can be spawned and removed
The harness SHALL spawn one actor of a loaded Blueprint class on `encampment_spawn`, list the spawned actors on `encampment_list`, and destroy one or all of them on `encampment_remove`. It SHALL destroy only actors that it spawned and SHALL keep at most 8.

#### Scenario: Spawn, list and remove
- **WHEN** a client sends `encampment_spawn`, `encampment_list` and then `encampment_remove` with the actor name
- **THEN** the actor is listed after the spawn and not listed after the remove
- Checked by `harness/tests/test_fakegame_harnessencampment.py`.

#### Scenario: Bad class or coordinate
- **WHEN** a client sends `encampment_spawn` with a bad class path, a class that is not loaded, or a coordinate beyond 1000000
- **THEN** the reply is not ok and nothing is spawned
- **AND** a valid class path is under `/Game/`, and the error for a class that is not loaded says to run `load_pak_blueprint` first
- Checked by `harness/tests/test_fakegame_harnessencampment.py`.

#### Scenario: The cap
- **WHEN** 8 actors are spawned and a client sends `encampment_spawn` again
- **THEN** the reply is not ok and says to remove one first
- Checked by `harness/tests/test_fakegame_harnessencampment.py`.

#### Scenario: Remove with nothing spawned
- **WHEN** a client sends `encampment_remove` with the name `all` and nothing is spawned
- **THEN** the reply is ok with 0 removed
- **AND** an unknown actor name is refused
- Checked by `harness/tests/test_fakegame_harnessencampment.py`.

#### Scenario: A pak camp stands in neutral territory
- **WHEN** a pak Blueprint is loaded and spawned in the game
- **THEN** the actor is alive at the asked position with its mesh
- Not checked yet.
