## REMOVED Requirements
<!-- Issue: #505 -->

### Requirement: Tribute is silver from the lord's treasury
**Reason**: The liege screen offers contracts, not tribute (owner decision 2026-10-28). Silver no longer buys influence.
**Migration**: Influence now changes only through contract rewards and penalties (see `mod/liege_contracts`). The command `InvasionMod.liege_send_tribute` is removed.

### Requirement: The tribute ratio is configurable
**Reason**: There is no tribute to convert, so `influence_per_unit` has no use.
**Migration**: Remove `influence_per_unit` from the config. Contract rewards set the influence amount directly.

### Requirement: The command name
**Reason**: It names the removed tribute command and menu button.
**Migration**: The liege commands are listed in `mod/liege_contracts` (requirement "The feature offers named commands"). `InvasionMod.liege_request_arms` stays.

### Requirement: Tribute menu
**Reason**: The menu becomes the contracts window.
**Migration**: See the ADDED requirements in `mod/liege_contracts` ("The liege window shows three contract cards" and "The liege window opens in at most 2 clicks"). The menu id `liege` stays.

### Requirement: One tribute button
**Reason**: The window has no tribute button.
**Migration**: The pak button `TributeButton` is replaced by the pick and complete buttons of the contracts window.

## MODIFIED Requirements

### Requirement: Influence is a saved value
The mod SHALL keep an influence value for the player in ModState. The value SHALL start at 0 on a new game. It SHALL come back after a save and a load. The command `InvasionMod.liege_state` SHALL show it. Only contract rewards and contract penalties (see `mod/liege_contracts`) SHALL change it. A penalty SHALL NOT take it below 0. The value SHALL NOT decay over time and SHALL NOT have a cap.

#### Scenario: Influence survives a load
- **WHEN** the influence is above 0, the game is saved with the harness action `save_game`, and the slot is loaded
- **THEN** `liege_state` shows the same influence
- Checked by `mod/InvasionMod/scenarios/liege_influence/influence_roundtrip.py` (updated: it sets the influence through a completed contract and not through a tribute).

#### Scenario: A new game
- **WHEN** a new game starts with the feature on
- **THEN** `liege_state` shows an influence of 0
- Checked by `mod/InvasionMod/scenarios/liege_influence/influence_roundtrip.py`.

#### Scenario: No decay
- **WHEN** the influence is above 0 and several game days pass with no contract event
- **THEN** the influence is unchanged
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: No cap
- **WHEN** contract rewards raise the influence above 1000
- **THEN** each reward still raises the influence
- Checked by `harness/tests/test_fakegame_liege_influence.py` (updated).

#### Scenario: A penalty stops at 0
- **WHEN** the influence is 5 and a contract penalty of 500 applies
- **THEN** the influence is 0
- Checked by `harness/tests/test_fakegame_liege_influence.py`.
