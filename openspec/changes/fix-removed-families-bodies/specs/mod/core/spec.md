## ADDED Requirements
<!-- Issue: #580 -->

### Requirement: Removed families leave no visible body and no corpse count
When `ManorCore.remove_families` removes families, it SHALL kill each member with `just_die`, SHALL hide each body with `SetActorHiddenInGame(true)`, and SHALL NOT leave the new bodies in the game's corpse count, so that no dead-bodies notification shows. It SHALL NOT call `K2_DestroyActor` on a unit. A failed hide SHALL NOT stop the removal of the other members.

#### Scenario: Families are removed
- **WHEN** a feature removes families from the player region
- **THEN** the people are dead and their bodies are hidden
- **AND** the corpse count of the region does not rise
- **AND** the game shows no dead-bodies notification
- **AND** the game runs 5 more game days with no crash
- Checked by `mod/InvasionMod/scenarios/liege_contracts/removed_bodies.py` and `harness/tests/test_fakegame_remove_families_bodies.py`.
