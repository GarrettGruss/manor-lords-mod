## MODIFIED Requirements

<!-- Issue: #563 -->

### Requirement: Laws can be enacted and repealed
The mod SHALL let the player enact a law of the chosen path when the node it requires is unlocked, and a common law when its common tech is unlocked (also before a path is chosen). A law is also unlocked when a contract unlocked it through `laws_unlock` (see `mod/laws_menu`). A law is free and can be repealed. At most the law slots are in force: `max_active_laws` (default 2) plus the extra slots added by `laws_add_slot`. The common laws count toward the limit. The nine laws are: Conscription, Forced Labor on Walls, Scorched Earth (Oppression), Militia Charter, Trade Pacts, Pay Off Warbands (Prosperity), and Strip the Dead, Disarm the Peasantry and Curfew (common). Trade Pacts raises the tribute only; no law changes vassal loyalty. The laws are kept in mod state (key `tech_laws`). A law of the other path is refused also when it is unlocked.

#### Scenario: Law places and refusals
- **WHEN** the player enacts a law above the slot count, a law of the other path, or a law that is not unlocked
- **THEN** the call is refused with the reason
- Checked by `harness/tests/test_fakegame_laws.py`.

#### Scenario: A common law counts toward the limit
- **WHEN** the player enacts Conscription and Curfew and then Strip the Dead
- **THEN** the third call is refused as a third law
- Checked by `harness/tests/test_fakegame_laws.py`.

#### Scenario: An extra slot allows a third law
- **WHEN** `laws_add_slot` ran once and the player enacts three unlocked laws
- **THEN** all three are in force and a fourth is refused
- Not checked yet. Planned: `harness/tests/test_fakegame_laws_menu.py`.

#### Scenario: Trade Pacts raise the tribute
- **WHEN** the player enacts Trade Pacts and a vassal with 5 families and the policy light pays
- **THEN** the tribute is between 12 and 14 units, and after the repeal it is 10 again
- Checked by `mod/InvasionMod/scenarios/tech_tree/laws.py`.
