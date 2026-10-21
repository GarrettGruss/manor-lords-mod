## MODIFIED Requirements
<!-- Issue: #341 -->

### Requirement: A lost vassal sends a refugee wave
The mod SHALL send a wave of refugee families to the home region when a vassal is lost. The wave size SHALL be `ceil(vassal families x share)` with the share 0.50 of the population before the loss (`share_min` and `share_max` both 0.50 by default), and at least 1 family. The mod SHALL show the banner "Refugees have arrived".

#### Scenario: A vassal is lost
- **WHEN** a handed-over vassal of 10 families is wiped
- **THEN** the home region gains 5 families and the wave is active
- **AND** the home region has at least 1 homeless family when it has fewer than 5 free home slots
- Not checked yet (planned: `mod/InvasionMod/scenarios/refugees/refugee_wave.py`, updated).

#### Scenario: The loss starts the wave by itself
- **WHEN** the vassals feature reports a lost vassal in the fake game
- **THEN** the refugees feature sends a wave without a command
- Checked by `harness/tests/test_fakegame_refugees.py`.
