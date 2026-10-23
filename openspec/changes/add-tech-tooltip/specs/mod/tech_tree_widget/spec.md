## ADDED Requirements
<!-- Issue: #428 -->

### Requirement: A tooltip lists the numerical effects of a tech
Mouse over a node button or a law button of the tech tree menu SHALL show a tooltip. The tooltip SHALL list the numerical effects of the tech, each with its value. A percent effect SHALL show as a signed percent ("+10%"). A flat effect SHALL show as a signed number ("Public Order +10"). The tooltip MAY also show other information, for example a condition of an effect or a vassal policy that the node opens.

#### Scenario: A percent effect
- **WHEN** the mouse is over a tech with the effect militia attack 0.10
- **THEN** the tooltip has the line "Militia attack +10%"
- Checked by `harness/tests/test_fakegame_tech_tooltip.py`.

#### Scenario: A flat effect
- **WHEN** the mouse is over a tech with the effect public order 10
- **THEN** the tooltip has the line "Public Order +10"
- Checked by `harness/tests/test_fakegame_tech_tooltip.py`.

#### Scenario: A tech with several effects
- **WHEN** the mouse is over a tech with 2 or more numerical effects
- **THEN** the tooltip lists each of them with its value
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_tooltip.py` (the tooltip property) and by the picture evidence of the implementation pull request (the real hover, owner needed).
