## MODIFIED Requirements
<!-- Issue: #530 -->

### Requirement: A new game starts with the scenario kit
When the player clicks "Begin the game" in a new game (or the settings are applied by command), the mod SHALL give the player a start kit once: 10 families and 300 starting silver. The amounts SHALL come from config values (`start_kit.families`, `start_kit.silver`). The mod SHALL NOT give the kit for a game loaded from a save, and SHALL NOT give it a second time. The mod SHALL store in the mod state that the kit was given, so it is saved with the game.

#### Scenario: A new game gets the kit
- **WHEN** a new game starts and the player clicks "Begin the game"
- **THEN** the player region has 10 families and the player pawn property `silver` is 300
- **AND** the mod state holds the entry "kit given"
- Not checked yet.

#### Scenario: A loaded save gets no kit
- **WHEN** a save loads, with or without the entry "kit given"
- **THEN** no silver and no families are added
- Not checked yet.

#### Scenario: The kit is given once
- **WHEN** the settings are applied a second time in the same game (for example by command)
- **THEN** no second kit is given
- Not checked yet.

### Requirement: The villagers replace the start population
The 10 families SHALL be the family count of the top bar. The mod SHALL make the family count of the player region exactly the configured value. When the region has fewer families, the mod SHALL add the missing families with `settleRegion` (homeless families in a tent camp). When it has more, the mod SHALL remove the last families by `just_die` on their members, and SHALL NOT call `K2_DestroyActor` on a unit. The 300 silver SHALL set the silver of the player pawn to 300.

#### Scenario: Ten families in total
- **WHEN** a new game begins
- **THEN** the player region has exactly 10 families
- **AND** the test reports the number of people
- Not checked yet.

#### Scenario: A region with more families is cut
- **WHEN** the region has more than 10 families at "Begin the game"
- **THEN** the last families are removed until 10 families remain
- Not checked yet.
