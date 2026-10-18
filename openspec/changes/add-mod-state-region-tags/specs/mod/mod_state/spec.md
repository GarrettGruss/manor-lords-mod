## ADDED Requirements
<!-- Issue: #273 -->

### Requirement: A region keeps its own values in its Tags
The mod SHALL be able to store a value for one region as a Name `<mod>:<key>=<value>` in the `Tags` of that region. The value SHALL come back after a save and a load. Values of two regions SHALL stay separate. The mod SHALL NOT call a save function.

#### Scenario: A region value survives a save and a load
- **WHEN** a test sets a value on the home region and a different value on a second region, makes a harness save, and loads that slot in a new run
- **THEN** each region reads back its own value
- **AND** the pawn values are unchanged
- Not checked yet (planned: `mod/InvasionMod/scenarios/mod_state/region_roundtrip.py`).

#### Scenario: A region value for a region that is not loaded
- **WHEN** the mod reads a value for a region that has no actor yet
- **THEN** the read fails with a message that names the region
- **AND** no default is returned in silence
- Not checked yet (planned: `harness/tests/test_fakegame_mod_state_region.py`).

### Requirement: A write past the tested limit fails loudly
ModState SHALL refuse a write that would pass the entry count or the entry length found by the limit test (see `design.md`). The error SHALL name the limit. The values already stored SHALL stay unchanged.

#### Scenario: Too many entries
- **WHEN** a test writes entries until the count limit is passed
- **THEN** the write that passes the limit fails with an error that names the count limit
- **AND** the entries stored before it are still readable
- Not checked yet (planned: `harness/tests/test_fakegame_mod_state_region.py`).

#### Scenario: A full Tags array saves and loads in time
- **WHEN** the Tags hold the maximum number of entries of the maximum length, and the game is saved and loaded
- **THEN** all entries come back
- **AND** the load takes less than the budget set in `design.md`
- Not checked yet (planned: `mod/InvasionMod/scenarios/mod_state/tags_limit.py`).
