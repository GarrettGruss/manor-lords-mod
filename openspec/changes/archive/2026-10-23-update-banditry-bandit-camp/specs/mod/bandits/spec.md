## MODIFIED Requirements
<!-- Issue: #453 -->

### Requirement: A conversion removes two families and spawns a bandit squad
When the banditry timer expires, the mod SHALL remove `leavers` (default 18) villagers, as families, and SHALL spawn one bandit camp (`RTSMultiEngineCPP:spawnBanditCamp()`, a camp with 18 Brigands) for the leave event. The mod SHALL NOT spawn squads at the homes. The number of squads does not depend on the number of families (the rule "one squad per 5 families" is removed). When the game has no bandit pawn, the same call SHALL make the bandit pawn, and the mod SHALL then call `addPawnRelations` for it, so villager banditry works with the game setting bandit camps 0. The game picks the camp place; the mod SHALL log the camp place. A villager here is a family. The village SHALL keep at least `min_families_left` (default 1) families, so fewer than 18 may leave. The mod SHALL show the banner `Families have turned to banditry`.

#### Scenario: A forced conversion
- **WHEN** the banditry timer expires (a test forces it) with enough villagers
- **THEN** the villagers that leave are between 1 and 18, and the village keeps at least 1 family
- **AND** one bandit camp exists and the bandit units grow by 18
- **AND** the game runs 10 more game days with no crash
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_timer.py`.

#### Scenario: The last family stays
- **WHEN** the village has only 1 family and the timer expires
- **THEN** no family leaves and no camp spawns
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: One squad for every 5 families
- **WHEN** 18 families leave (the old rule gave 3 squads)
- **THEN** exactly one camp spawns, whatever the number of families, and no squad spawns at the homes
- Checked by `harness/tests/test_fakegame_bandits.py` and `mod/InvasionMod/scenarios/bandits/banditry_timer.py`.

#### Scenario: No bandit pawn
- **WHEN** villagers leave and the game has no bandit pawn (bandit camps 0)
- **THEN** the mod makes the bandit pawn with the camp (one `spawnBanditCamp` call) and calls `addPawnRelations`
- **AND** the bandit pawn exists afterward
- Checked by `harness/tests/test_fakegame_bandits.py` and a real run on fixture `playtest-noai` (proposed).

#### Scenario: The conversion banner
- **WHEN** villagers leave for banditry
- **THEN** the banner `Families have turned to banditry` shows
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_banners.py`.
