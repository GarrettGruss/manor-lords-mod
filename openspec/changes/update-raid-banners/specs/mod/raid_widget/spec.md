## ADDED Requirements
<!-- Issue: #400 -->

### Requirement: The raid menu lists the upcoming raids
The raid menu SHALL show a persistent notice of the upcoming raids, below the five raid lines. Each entry SHALL show the raid type (`player raid`, `vassal raid` or `great raid`), the target (`you` or `your vassal <name>`), the size estimate and the days left. The list SHALL be sorted by days left and SHALL show `no raid planned` when empty. It SHALL NOT list a raid type that is switched off. The player SHALL be able to open it at any time, also after a banner was skipped by a load.

#### Scenario: Two raids are planned
- **WHEN** a player raid in 20 days (54 raiders) and a vassal raid on `V` in 45 days (30 raiders) are planned and the menu is open
- **THEN** the list shows the player raid first, then the vassal raid, each with target, size and days left
- Not checked yet (planned: `harness/tests/test_fakegame_raid_widget.py`).

#### Scenario: A missed banner
- **WHEN** a game loads 10 days before a raid whose 30 day banner was skipped
- **THEN** the menu list shows that raid with 10 days left
- Not checked yet (planned: `harness/tests/test_fakegame_raid_widget.py`).

#### Scenario: Nothing planned
- **WHEN** no raid is planned
- **THEN** the list reads `no raid planned`
- Not checked yet (planned: `harness/tests/test_fakegame_raid_widget.py`).
