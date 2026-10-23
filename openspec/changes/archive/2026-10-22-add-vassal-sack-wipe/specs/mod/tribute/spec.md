## MODIFIED Requirements
<!-- Issue: #341 -->

### Requirement: A long siege takes a vassal
The mod SHALL start the sack of the houses of a vassal (see `mod/vassals`) when a subjugation raid on its region has been active for `siege.days` game days (default 8) with at least `siege.min_living` of its units alive (default 0.5). The vassal SHALL be lost when the sack is complete. A vassal SHALL be sacked once for each raid. A younger raid, a beaten raid, a plunder raid and a raid on the home region SHALL start no sack.

#### Scenario: A subjugation raid holds for 8 days
- **WHEN** a subjugation raid targets a vassal region and stays active for 8 game days
- **THEN** the sack of the vassal houses starts
- **AND** when 80 percent of the buildings are ruins the vassal is lost with the reason `wiped`
- Checked by `mod/InvasionMod/scenarios/invasion/vassal_targets.py`.

#### Scenario: Siege rules in the fake game
- **WHEN** the raid is younger than 8 days, beaten, a plunder raid, or targets home
- **THEN** no sack starts and the vassal stays
- Checked by `harness/tests/test_fakegame_tribute.py`.
