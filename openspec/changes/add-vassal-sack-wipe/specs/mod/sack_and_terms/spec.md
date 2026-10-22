## MODIFIED Requirements
<!-- Issue: #341 -->

### Requirement: The feature offers named commands
The mod SHALL register `InvasionMod.sack_state`, `sack_now`, `sack_set_fatal`, `terms_state`, `terms_offer`, `terms_accept` and `terms_decline`. Scenarios SHALL use these commands and not eval.

#### Scenario: A state command answers
- **WHEN** a scenario sends `InvasionMod.sack_state`
- **THEN** the answer holds the sack count, the window values and the share for the current difficulty
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/sack.py`.

## ADDED Requirements

### Requirement: The sack picks the region
The mod SHALL sack the raid target when the player owns it. Else it SHALL sack the home region (`vassals_home_region`) when the player owns it. Else it SHALL sack the first region of the player. A manual sack SHALL use the home region. The sack result SHALL name the region.

#### Scenario: A manual sack names the home region
- **WHEN** `sack_now` runs with no raid target
- **THEN** the sack result names the home region
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/sack_region.py`.

#### Scenario: Region choice rule
- **WHEN** the raid targets a player region, a foreign region, or no known region
- **THEN** the sack hits that region, the home region, or the first player region
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

### Requirement: No terms after a sack of the player
After a sack of a player region the mod SHALL close an open offer and SHALL NOT open a new offer for the same raid. `InvasionMod.terms_offer` SHALL be refused for that raid.

#### Scenario: A sack closes the offer
- **WHEN** an offer is open and the raid sacks a player region
- **THEN** the offer is closed
- **AND** `terms_offer` for the same raid is refused
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

## REMOVED Requirements

### Requirement: The sack hits the right region
**Reason**: Renamed to "The sack picks the region" because its scenario about the fallback capital move is dropped (owner, 2026-10-20, item 4).
**Migration**: Use the ADDED requirement "The sack picks the region". The rule text is the same.

### Requirement: A fortified vassal becomes the fallback capital
**Reason**: Capital moves are not part of the game (owner, 2026-10-20, item 4).
**Migration**: None. Remove the commands `fallback_state`, `fallback_move`, `fallback_set_take_back` and `fallback_set_min_buildings`, and the test scenario `fallback_capital.py`. The home region stays the owned region with the most buildings (`vassals_home_region`).
