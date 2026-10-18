# Spec Delta

## Purpose

Named harness commands that read, and change in memory, number fields of the live game data tables, and the shared game-call module that player mods use. They let a test read a unit, item, building or upgrade row without the bridge crashing the game.

## ADDED Requirements

### Requirement: Table rows are read through a list of number fields
The harness SHALL read number fields of the `items` table (the default) or the `units` table on `datatable_info`, `datatable_read` and `datatable_rows`. It SHALL read only the fields on the list of the table and refuse any other field without reading it.

#### Scenario: Info and one field
- **WHEN** a client sends `datatable_info` and then `datatable_read` with `row` 16 and `field` Value
- **THEN** the info lists the row names and the row struct, and the read gives one number
- Checked by `harness/tests/test_fakegame_harnessdatatable.py`.

#### Scenario: A field that is not listed
- **WHEN** a client sends `datatable_read` with a field such as `Name`, or with a field of the other table
- **THEN** the reply is not ok with `not allowed` and the field is not read
- Checked by `harness/tests/test_fakegame_harnessdatatable.py`.

#### Scenario: All rows of the unit table
- **WHEN** a client sends `datatable_rows` with `table` units
- **THEN** separator rows are skipped and each row lists the six number fields
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

#### Scenario: Unknown table or row
- **WHEN** a client sends `datatable_info` with an unknown table, or `datatable_read` with an unknown row
- **THEN** the reply is not ok and the error names the table or the row
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

#### Scenario: The listed fields
- **WHEN** a client reads the `items` table or the `units` table
- **THEN** `items` allows `Weight`, `Value`, `spoilageRate`, `def`, `block`, `att` and `armorPierce`
- **AND** `units` allows `cost`, `maxSize`, `minMeleeTraining`, `minArcheryTraining`, `minHouseLv` and `combatExperience`
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

### Requirement: A number field can be written in memory
The harness SHALL write one number field of one row on `datatable_write` with `row`, `field`, `value` and `table`, and answer with the value before and after. The write SHALL last until the game ends and SHALL NOT write a file. The harness SHALL refuse a field that is not listed, a value that is not a number, and a missing row, field or value.

#### Scenario: Write and read back
- **WHEN** a client sends `datatable_write` with `row` 17, `field` Value and `value` 3.5
- **THEN** the reply gives before 2.0 and after 3.5
- **AND** the row reads 3.5
- Checked by `harness/tests/test_fakegame_harnessdatatable.py`.

#### Scenario: A field that is not listed
- **WHEN** a client sends `datatable_write` with a field that is not listed
- **THEN** the reply is not ok and the row is unchanged
- Checked by `harness/tests/test_fakegame_harnessdatatable.py`.

#### Scenario: A write with no number
- **WHEN** a client sends `datatable_write` for a unit row without a `value`
- **THEN** the reply is not ok
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

#### Scenario: A pak value in the game
- **WHEN** a pak changes an item value and the game runs
- **THEN** `datatable_read` returns the pak value
- Checked by `harness/scenarios/pak_item_value.py`.

### Requirement: Building and upgrade rows are read only
The harness SHALL read scalar fields of one `buildingStats` row on `building_stat` and number fields of one `DT_Upgrades` row on `upgrade_stat`, with `type` up to 70000. A request with the field `kind` SHALL use the wall reader. It SHALL NOT read soft object or struct array fields.

#### Scenario: A type above the limit
- **WHEN** a client sends `building_stat` with a `type` above 70000
- **THEN** the reply is not ok
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

#### Scenario: A building row
- **WHEN** a client sends `building_stat` with a valid `type`
- **THEN** the reply gives the display name, the scalar fields and the worker and occupant vectors
- Not checked yet.

#### Scenario: An upgrade row
- **WHEN** a client sends `upgrade_stat` with a valid upgrade id
- **THEN** the reply gives the listed number fields of the row
- Not checked yet.

### Requirement: Building row vectors are written only in an unsafe game
The harness SHALL refuse `building_stat_vector_write` unless the game runs with `HARNESS_ALLOW_UNSAFE=1`. With the variable set, it SHALL write one component (`X`, `Y`, `Z` or `W`) of `occupantTypes` or `workerTypes` of one building row, with a value from 0 to 100, and answer with the vector before and after. The write SHALL last until the game ends. The harness SHALL refuse a bad field, component or value and an unknown row, and SHALL write nothing then.

#### Scenario: The variable is not set
- **WHEN** a client sends `building_stat_vector_write` and the game has no `HARNESS_ALLOW_UNSAFE=1`
- **THEN** the reply is not ok and the error names the variable
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

#### Scenario: One component is written
- **WHEN** the variable is set and a client sends `building_stat_vector_write` for one component with a value of 5, and later with 0
- **THEN** the reply gives the vector before and after, and the component reads 5 and then 0
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

#### Scenario: Bad write input
- **WHEN** the variable is set and the request has a bad value, field or component, or an unknown row
- **THEN** the reply is not ok and nothing is written
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

### Requirement: The shared game-call module needs no harness module
The shared module `ManorCore` SHALL NOT require any harness-only module, so that a released player mod can use it. `ManorCore` SHALL hold the player region reader, the region list, `settle_region`, `forest_spot`, `tent_find_spot`, `rebel_raid_rally`, `show_banner` and the policy helpers. `settle_region` SHALL refuse a region that the settling pawn does not own, a type outside 1 to 5 and an unknown region.

#### Scenario: A released mod needs only ManorCore
- **WHEN** the shared closure of the mod `RefugeeWaves` is computed
- **THEN** it is exactly `ManorCore`
- Checked by `harness/tests/test_release_manifest.py`.

#### Scenario: Settle needs an owner
- **WHEN** `settle_region` is called for a region that the pawn does not own
- **THEN** the reply is not ok with `does not own` and no game call is made
- Checked by `harness/tests/test_fakegame_harnesslords.py`.
