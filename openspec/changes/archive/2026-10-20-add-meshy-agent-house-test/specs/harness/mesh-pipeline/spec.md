## ADDED Requirements
<!-- Issue: #320 -->

### Requirement: The Meshy agent CLI makes a house that is placed in the game
The harness SHALL have a test scenario that builds one vanilla house whose mesh was replaced by a model generated with `meshy-cli` and imported with the mesh pipeline. The model SHALL be generated privately on the Pro account and SHALL NOT be published to the Meshy Community page.

#### Scenario: The generated house stands in the world
- **WHEN** the test scenario runs with the test pak and builds the house
- **THEN** the building exists, uses the replaced mesh, and the screenshots show the generated house
- Checked by `harness/scenarios/meshy_house.py` (test scenario `meshy-agent-house`), runs 20261020-041549-7439 (pak) and 20261020-041739-4836 (vanilla). Pictures: `evidence/`. The mesh path stays the vanilla path, so the pictures tell the two runs apart.

#### Scenario: The run without the pak shows the vanilla house
- **WHEN** the same test scenario runs without the test pak
- **THEN** the building exists and uses the vanilla mesh
- Checked by `harness/scenarios/meshy_house.py` (test scenario `meshy-agent-house`), runs 20261020-041549-7439 (pak) and 20261020-041739-4836 (vanilla). Pictures: `evidence/`. The mesh path stays the vanilla path, so the pictures tell the two runs apart.
