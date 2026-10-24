## RENAMED Requirements
<!-- Issue: #480 -->

- FROM: `### Requirement: A conversion removes two families and spawns a bandit squad`
- TO: `### Requirement: A rebellion removes families and spawns an Outlaws raid`

## MODIFIED Requirements

### Requirement: A rebellion removes families and spawns an Outlaws raid
When the banditry timer expires, the mod SHALL remove `rebellion_families` (default 5) families (`ManorCore.remove_families`) and SHALL spawn `rebellion_squads` (default 1) squads of the template Brigands for the bandit pawn "Outlaws" at the home of the first removed family (`HarnessBandits.homeless_rebel`, mode `home`, `spawnArmy`). The mod SHALL NOT call `spawnBanditCamp` for a leave event when the Outlaws pawn exists. When the pawn is missing, the mod SHALL create it with `spawnBanditCamp()` (side effect: one camp of 18 Brigands) and call `addPawnRelations` for it, and then spawn the squads. The native Outlaws AI SHALL do the raid: it burns buildings, logs "enough looted" and leaves the map. The mod does not steer it. The village SHALL keep at least `min_families_left` (default 1) families, so fewer than `rebellion_families` may leave. A villager here is a family. The mod SHALL show the banner `Families have turned to banditry`.

#### Scenario: A forced conversion
- **WHEN** the banditry timer expires (a test forces it) with enough families
- **THEN** the families that leave are between 1 and 5, and the village keeps at least 1 family
- **AND** the bandit squad spawns within 500 units of a removed home
- **AND** within 400 game seconds at least 1 building burns and the AI logs "enough looted"
- **AND** the game runs 10 more game days with no crash
- Checked by `mod/InvasionMod/scenarios/bandits/rebellion_raid.py` (to write, based on `probe_rebel_noai.py`).

#### Scenario: The last family stays
- **WHEN** the village has only 1 family and the timer expires
- **THEN** no family leaves and no squad spawns
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: One squad for every 5 families
- **WHEN** 5 families leave (the old rule gave one squad for each 5 families; now the count comes from config: `rebellion_squads` is 1 by default, or the config sets other values)
- **THEN** that many families leave and that many squads spawn at the first removed home
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: No bandit pawn
- **WHEN** families leave and the game has no Outlaws pawn
- **THEN** the mod creates the pawn with one `spawnBanditCamp` call, calls `addPawnRelations`, and then spawns the squads at the home
- **AND** one camp of 18 Brigands exists as an accepted side effect
- Checked by `harness/tests/test_fakegame_bandits.py` and `mod/InvasionMod/scenarios/bandits/rebellion_raid.py`.

#### Scenario: No camp when the pawn exists
- **WHEN** families leave and the Outlaws pawn exists
- **THEN** `spawnBanditCamp` is not called
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: Repeat rebellion
- **WHEN** a second rebellion happens after the first squads raided
- **THEN** the new squad spawns at the new home and raids, or logs "enough looted", with no crash
- Not checked yet.

#### Scenario: Plunder by Outlaws squads
- **WHEN** an Outlaws squad raids
- **THEN** the result records whether goods are looted
- Not checked yet.

#### Scenario: Removal at the map edge
- **WHEN** the squads leave the map after "enough looted"
- **THEN** the bandit units fall to the camp units, or the result records that they stay
- Not checked yet.

#### Scenario: The conversion banner
- **WHEN** families leave for banditry
- **THEN** the banner `Families have turned to banditry` shows
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_banners.py`.

### Requirement: Low order starts a banditry timer
When the order drops below `threshold` (default 25), the mod SHALL start a timer of `timer_days` (default 60) game days. When the timer expires, the rebellion SHALL start. When the order is `threshold` or more before the timer expires, the timer SHALL reset. After the rebellion, the order rises by `order_gain` (default 25), and the timer SHALL restart if the order is still below `threshold`. The values `threshold`, `timer_days`, `order_gain` and `tick_days` (default 30) are config values of the feature.

#### Scenario: Timer start and expiry
- **WHEN** a tick leaves the order at 20
- **THEN** the timer starts, and the rebellion happens between 55 and 65 game days later if the order stays under 25
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_timer.py`.

#### Scenario: The timer resets
- **WHEN** the order rises to 25 or more before the timer expires
- **THEN** the timer stops and no family leaves
- Checked by `harness/tests/test_bandits_rules.py`.

#### Scenario: Config values
- **WHEN** the config sets `threshold`, `timer_days`, `order_gain` or `tick_days`
- **THEN** the rules use those values
- Checked by `harness/tests/test_bandits_rules.py`.
