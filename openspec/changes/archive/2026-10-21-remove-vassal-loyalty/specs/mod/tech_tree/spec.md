## MODIFIED Requirements
<!-- Issue: #344 -->

### Requirement: Laws can be enacted and repealed
The mod SHALL let the player enact a law of the chosen path when the node it requires is unlocked. A law is free and can be repealed. At most `max_active_laws` laws (default 2) are in force. The six laws are: Conscription, Forced Labor on Walls, Scorched Earth (Oppression), and Militia Charter, Trade Pacts, Pay Off Warbands (Prosperity). Trade Pacts raises the tribute only; no law changes vassal loyalty. The laws are kept in mod state (key `tech_laws`).

#### Scenario: Law places and refusals
- **WHEN** the player enacts a third law, a law of the other path, or a law whose node is locked
- **THEN** the call is refused with the reason
- Checked by `harness/tests/test_fakegame_laws.py`.

#### Scenario: Trade Pacts raise the tribute
- **WHEN** the player enacts Trade Pacts and a vassal with 5 families and the policy light pays
- **THEN** the tribute is between 12 and 14 units, and after the repeal it is 10 again
- Not checked yet (planned: `mod/InvasionMod/scenarios/tech_tree/laws.py`, updated).
