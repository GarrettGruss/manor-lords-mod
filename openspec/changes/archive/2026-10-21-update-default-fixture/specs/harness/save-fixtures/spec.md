## MODIFIED Requirements
<!-- Issue: #379 -->

### Requirement: Fixtures are listed in a manifest
The manifest `harness/fixtures/fixtures.json` SHALL list each fixture with its description, origin, tags and the SHA-256 of each file. The save files SHALL be stored in `harness/fixtures/saves/<name>/` under the stem `slot`, and git SHALL ignore that folder. The default fixture SHALL be `base-corpse-pit`, and it SHALL carry the tag `default`.

#### Scenario: The manifest is valid
- **WHEN** the manifest in the repo is read
- **THEN** it is valid and holds hashes and no save data
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: A stored file changed
- **WHEN** a stored fixture file no longer matches its hash
- **THEN** the harness refuses to use it
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: The default fixture
- **WHEN** a run names no fixture
- **THEN** it loads `base-corpse-pit`, the only fixture with the tag `default`
- Checked by `harness/tests/test_runlib_fixtures.py`.
