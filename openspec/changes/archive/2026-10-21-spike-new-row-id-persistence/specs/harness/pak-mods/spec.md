## ADDED Requirements
<!-- Issue: #284 -->

### Requirement: Upgrades use only vanilla ids
A pak SHALL NOT add a `DT_Upgrades` row with a new id, and SHALL NOT set `upgradesInto` of an upgrade to a new `buildingStats` id. A pak MAY add new `buildingStats` ids in the feature range (they load, are placed, built, saved and loaded).

#### Scenario: New building id
- **WHEN** a pak adds a `buildingStats` row in the feature range
- **THEN** the building can be placed, built, saved and loaded
- Checked by spike run `rowid-write-b` and `rowid-read-a` (notes/id-persistence.md).

#### Scenario: New upgrade id
- **WHEN** a pak adds a `DT_Upgrades` row with a new id
- **THEN** the game copies the cost into `needs` but never carries out the upgrade
- Checked by spike runs `rowid-control-b` and `rowid-control-e` (notes/id-persistence.md).
