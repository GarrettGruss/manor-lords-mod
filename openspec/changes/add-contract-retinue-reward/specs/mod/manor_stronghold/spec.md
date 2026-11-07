## ADDED Requirements

<!-- Issue: #591 -->

### Requirement: The mod can add a native retinue squad
The feature SHALL offer `retinue.add_native_squad(men)`. It SHALL add one empty native retinue squad with `InitializeEmptyRetinueSquad`, recruit `men` men into it with the native `hireExtraRetinue`, and return the new squad id. The silver of those recruits SHALL NOT stay charged to the player (the caller grants the men). The game saves the squad; the mod SHALL NOT keep a copy of it. The function SHALL return a reason when no manor is built or when fewer men than asked could be recruited.

#### Scenario: A squad of 5 men
- **WHEN** `add_native_squad(5)` runs with a built manor
- **THEN** a new squad with 5 living men is in the commanded squads of the player and the silver is as before
- Checked by `harness/tests/test_fakegame_manor_stronghold.py` and `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

#### Scenario: No manor
- **WHEN** no manor is built
- **THEN** the call returns nil with a reason and no squad is added
- Checked by `harness/tests/test_fakegame_manor_stronghold.py`.
