## MODIFIED Requirements
<!-- Issue: #560 -->

### Requirement: The villagers replace the start population
The 10 families SHALL be the family count of the top bar. The mod SHALL make the family count of the player region exactly the configured value. When the region has fewer families, the mod SHALL add the missing families with `settleRegion` (homeless families in a tent camp). Each `settleRegion` call SHALL also add a second tent camp, one ox and a small supply package (Modest, argument `supply` 0). The owner accepted these extras on 2026-11-04, until a data-based fix exists. When the region has more families, the mod SHALL remove the last families by `just_die` on their members, and SHALL NOT call `K2_DestroyActor` on a unit. The 300 silver SHALL set the silver of the player pawn to 300.

#### Scenario: Ten people in total
- **WHEN** a new game begins
- **THEN** the player region has exactly 10 families (the number of people follows from the families; it is reported, not asserted)
- **AND** the test reports the number of people
- Checked by `mod/InvasionMod/scenarios/scenario_settings/start_kit.py` (runs 20261028-235239-119a, 20261028-235402-4828) and `harness/tests/test_fakegame_scenario_settings.py`.

#### Scenario: A region with more families is cut
- **WHEN** the region has more than 10 families at "Begin the game"
- **THEN** the last families are removed until 10 families remain
- Checked by `mod/InvasionMod/scenarios/scenario_settings/start_kit.py` (runs 20261028-235239-119a, 20261028-235402-4828) and `harness/tests/test_fakegame_scenario_settings.py`.

#### Scenario: The settle call adds accepted extras
- **WHEN** the start kit adds families with one `settleRegion` call
- **THEN** the call adds 5 families, one more tent camp (type 87), 4 region buildings, one ox and about 79 goods (the Modest package)
- **AND** the extras are accepted until a data-based fix exists
- Checked by `harness/scenarios/probe_settle_families_only.py` (runs sfo-mult0, sfo-type5, sfo-type4; a probe, not an assertion).
