## MODIFIED Requirements

<!-- Issue: #563 -->

### Requirement: The menu lists the laws
The node cards whose tech opens a law SHALL show the law name only. The tech window SHALL NOT show an Enact or Repeal button and SHALL NOT show the laws strip. It SHALL show one line, "Laws: open the Laws menu", which names the Laws menu (`mod/laws_menu`), where the player enacts and revokes laws. The commands `tech_tree_enact_law` and `tech_tree_repeal_law` stay and are used by the Laws menu. This follows the recommendation of open question Q1 of change `add-laws-menu`; the owner may reverse it before gate 2.

#### Scenario: No law buttons in the tech window
- **WHEN** the tech window opens with a law unlocked
- **THEN** the card shows the law name, there is no Enact or Repeal button, and the line "Laws: open the Laws menu" shows
- Not checked yet. Planned: `mod/InvasionMod/scenarios/tech_tree/widget_laws.py` (updated).

#### Scenario: Presses enact, repeal and refuse
- **WHEN** the harness presses a law through the Laws menu command (`laws_menu_press`)
- **THEN** the tech tree state shows the law in force or gone after each press, and the tech window only shows the law name
- **AND** a press on a law of a locked tech is refused, and a press above the slot count is refused
- Not checked yet. Planned: `mod/InvasionMod/scenarios/tech_tree/widget_laws.py` (updated).

#### Scenario: Labels say what a click does
- **WHEN** a law is in force, open, closed only by the limit of laws, or its tech is not yet unlocked
- **THEN** its button in the Laws menu says Revoke, says Enact, is disabled with the slot text, or the card is Locked
- Not checked yet. Planned: `harness/tests/test_fakegame_laws_menu.py`.
