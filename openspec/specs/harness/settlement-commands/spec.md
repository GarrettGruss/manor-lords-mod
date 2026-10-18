# harness/settlement-commands Specification

## Purpose
Named harness commands for the bandit faction, the homes and families of the player village, and the reverse path where homeless families become bandits. Tests use them to negotiate with raiders, to read and change housing, and to start a rebellion.

## Requirements

### Requirement: Bandit state is read only
The harness SHALL answer `bandit_state` without changing the game. The reply SHALL give the families, homeless families and vacant home slots of each player region, the numbers of bandit and player units, silver, influence, the bandit lord silver and the relation tags between the player and the bandit lord. The harness SHALL answer with an error when no bandit lord exists.

#### Scenario: The state of a village
- **WHEN** a client sends `bandit_state`
- **THEN** the reply is ok and gives families, bandit units, silver and the relation tags
- Checked by `harness/tests/test_fakegame_harnessbandits.py`.

### Requirement: Relation tags and the settle letter can be driven
The harness SHALL add or remove one relation tag (`attacking`, `acquainted` or `at_war`) between the player and the bandit lord on `bandit_tag`. It SHALL send 1 to 4 letter paragraphs on `bandit_letter` and call the developer settle cheat on `settle_raiders`. Each reply SHALL give the state before and after.

#### Scenario: A tag is added and removed
- **WHEN** a client sends `bandit_tag` with `tag` attacking, and then with `remove` 1
- **THEN** `bandit_state` lists the tag after the first command and not after the second
- Checked by `harness/tests/test_fakegame_harnessbandits.py`.

#### Scenario: A tag outside the list
- **WHEN** a client sends `bandit_tag` with `tag` not in the list
- **THEN** the reply is not ok
- Checked by `harness/tests/test_fakegame_harnessbandits.py`.

#### Scenario: The settle letter with the attacking tag
- **WHEN** the relation has the `attacking` tag and a client sends `bandit_letter` with `raider_suggestSettle+20`
- **THEN** the silver falls and the bandit units are cleared
- **AND** without the `attacking` tag nothing changes
- Checked by `harness/tests/test_fakegame_harnessbandits.py`.

#### Scenario: Bad paragraphs
- **WHEN** a client sends `bandit_letter` with a paragraph that is not allowed, a bad silver amount, or no paragraph
- **THEN** the reply is not ok and no letter is sent
- **AND** only `raider_greeting`, `raider_suggestSettle`, `raider_acceptSettle` and `raider_refuseSettle` are allowed, each with an optional `+<silver>` amount
- Checked by `harness/tests/test_fakegame_harnessbandits.py`.

#### Scenario: The settle cheat
- **WHEN** a client sends `settle_raiders`
- **THEN** the reply is ok and gives the state before and after
- Checked by `harness/tests/test_fakegame_harnessbandits.py`.

### Requirement: Bandit units can be followed
The harness SHALL remember the living units of the bandit side on `bandit_mark` (at most 200). `bandit_track` SHALL report, for the remembered units, the counts of gone, dead, units with no squad and units in a squad, the roles, and a sample of rows with squad, role, position and region. `bandit_track` SHALL NOT change the game.

#### Scenario: Marked units are followed
- **WHEN** a client sends `bandit_mark` and then `bandit_track`
- **THEN** `marked` equals the number of bandit units that were marked, and all of them count as in a squad
- Checked by `harness/tests/test_fakegame_harnessbandits.py`.

### Requirement: Families can become bandits
The harness SHALL spawn bandit squads at a point on `bandit_spawn_at`, turn units into bandits on `bandit_turn`, remove families and spawn bandits at their homes on `homeless_rebel`, send one real raid to a forest spot on `rebel_raid_rally`, and kill bandit squads on `bandit_kill_squads`. It SHALL refuse bad input before it removes or spawns anything.

#### Scenario: A bandit squad at a point
- **WHEN** a client sends `bandit_spawn_at` with a point and a known template
- **THEN** a bandit squad appears and the bandit unit count rises
- **AND** missing or far coordinates are refused
- Checked by `harness/tests/test_fakegame_harnessrebel.py`.

#### Scenario: Units are turned
- **WHEN** a client sends `bandit_turn` with `source` family
- **THEN** the turned members leave their families
- **AND** `source` squad without units made by `spawn_units` is refused, and so are a bad count and a bad source
- Checked by `harness/tests/test_fakegame_harnessrebel.py`.

#### Scenario: Homeless families rebel
- **WHEN** a client sends `homeless_rebel` with `count` 2
- **THEN** 2 families leave and bandit squads stand at their homes
- **AND** `families_per_squad` groups several families into one squad
- **AND** a bad count, mode or template is refused and no family is removed
- Checked by `harness/tests/test_fakegame_harnessrebel.py`.

#### Scenario: A raid aimed at a forest
- **WHEN** a client sends `rebel_raid_rally` with `count` 2
- **THEN** 2 families leave and one raid is aimed at the forest spot nearest to the rally point
- **AND** when no forest spot exists the reply is not ok and no family is removed
- Checked by `harness/tests/test_fakegame_harnessrebel.py`.

#### Scenario: Only the named squads die
- **WHEN** a client sends `bandit_kill_squads` with `squad` 41 and `count` 2
- **THEN** the living bandit units of squads 41 and 42 die and other bandit squads stay
- **AND** a squad below 1 or a count above 10 is refused
- Checked by `harness/tests/test_fakegame_harnessrebel.py`.

#### Scenario: Limits
- **WHEN** a client sends `bandit_spawn_at` with a count above 6, `bandit_turn` above 20, `homeless_rebel` or `rebel_raid_rally` with a count above 6, or `bandit_kill_squads` with a count above 10
- **THEN** the reply is not ok and nothing is spawned, turned, removed or killed
- Checked by `harness/tests/test_fakegame_harnessrebel.py`.

### Requirement: Housing is read and homeless families are accommodated
The harness SHALL read the housing of the player region on `housing_state` and call the game accommodate call on `accommodate_homeless`. It SHALL list up to 5 free tent spots on `tent_find_spot` and up to 5 dense tree cells on `forest_spot`. The two spot finders SHALL NOT place anything.

#### Scenario: Housing state with a tent
- **WHEN** the village has a homeless tent and a client sends `housing_state`
- **THEN** the tent is listed and the residential buildings show their slots
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

#### Scenario: Accommodate homeless
- **WHEN** a client sends `accommodate_homeless`
- **THEN** the reply gives the housing before and after
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

#### Scenario: Tent spots
- **WHEN** a client sends `tent_find_spot`
- **THEN** every spot is clear of buildings
- **AND** when the game check does not run, no spot is returned
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

#### Scenario: Forest spots
- **WHEN** a client sends `forest_spot`
- **THEN** a dense grove far from the buildings is listed
- **AND** shrubs, other regions and groves outside the distance window are ignored
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

### Requirement: Families can be read, ejected and added
The harness SHALL read families on `family_state`, `family_census` and `member_fields`. It SHALL make 1 to 10 housed families leave their homes on `family_eject` and start 1 to 10 new families without a home on `family_add`. A refused command SHALL change nothing.

#### Scenario: State and census
- **WHEN** a client sends `family_state` or `family_census`
- **THEN** the replies list housed ids with approval, each family with members and roles, and the occupants of each home
- Checked by `harness/tests/test_fakegame_harnessfamilies.py`.

#### Scenario: Eject families
- **WHEN** a client sends `family_eject` with `count` 2
- **THEN** 2 housed families lose their home and `suppress` is passed on to the game call
- **AND** a bad count, more families than housed, an unknown home, and `home` tent without a tent are refused
- Checked by `harness/tests/test_fakegame_harnessfamilies.py`.

#### Scenario: Add a family
- **WHEN** a client sends `family_add` with `adult` true
- **THEN** the oldest member of a family of 2 or more starts a new family without a home
- **AND** with `adult` false the last member is taken
- Checked by `harness/tests/test_fakegame_harnessfamilies.py`.

#### Scenario: Member fields of an unknown family
- **WHEN** a client sends `member_fields` with an index that has no family, or a property walk fails
- **THEN** the reply is not ok and the error is reported, not hidden
- Checked by `harness/tests/test_fakegame_harnessfamilies.py`.
