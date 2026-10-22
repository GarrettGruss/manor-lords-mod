## MODIFIED Requirements
<!-- Issue: #344 -->

### Requirement: Vassals pay iron and salt as the permanent supply
The tribute of a vassal SHALL include iron and salt next to the main goods (config `tribute.finite_goods`: iron 10 and salt 6 units for each family at the fixed share). The share follows the vassal policy and laws like the main goods. Tribute goods are not production, so they do not reduce a home deposit.

#### Scenario: One vassal pays at a season change
- **WHEN** one vassal with 5 families pays at a season change
- **THEN** the tribute paid is 10 iron and 6 salt
- **AND** the home stores rise by at least 10 iron and 6 salt
- **AND** the `mined` count of iron and salt stays 0
- Checked by `mod/InvasionMod/scenarios/finite_resources/vassal_supply.py`.

#### Scenario: A policy scales the finite goods
- **WHEN** a vassal policy or a law changes the tribute share
- **THEN** the paid iron and salt change with the share
- Checked by `harness/tests/test_fakegame_tribute.py`.
