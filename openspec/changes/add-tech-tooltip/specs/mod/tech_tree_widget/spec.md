## ADDED Requirements
<!-- Issue: #428 -->

### Requirement: A tooltip lists the effects of a tech
Mouse over a node button or a law button of the tech tree menu SHALL show a tooltip. The tooltip SHALL have one line for each effect of the node or law, in data order. A hidden button SHALL have no tooltip.

#### Scenario: Hover shows all effects
- **WHEN** the mouse is over a node or a law with 2 or more effects
- **THEN** the tooltip shows one line for each effect and no other effect line
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_tooltip.py` (the tooltip property) and by the picture evidence of the implementation pull request (the real hover, owner needed).

#### Scenario: Every shipped tech has a tooltip
- **WHEN** the menu is open with the shipped tree
- **THEN** each shown node button and law button has a non-empty tooltip text that equals the text built from its effect data
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_tooltip.py`.

### Requirement: The tooltip text comes from the effect data
The tooltip text SHALL be built from the effect data of the tree (`effects` of the node or law) and not from hand-written text. A percent effect (a factor) SHALL show as a signed percentage ("+10%", "-25%"). A flat effect SHALL show as a signed number with its name ("Public Order +10"). An effect with `min_garrison_squads` SHALL show its condition on the same line. A node that opens a vassal policy SHALL show one more line, "Opens vassal policy <policy>".

#### Scenario: A factor shows as a percentage
- **WHEN** a node has the effects militia attack 0.10, buy-back price -0.25 and tribute share 0.25
- **THEN** the lines are "Militia attack +10%", "Buy-back price -25%" and "Tribute share +25%"
- **AND** a factor that is not a whole percent (0.025) shows with one decimal ("+2.5%")
- Checked by `harness/tests/test_fakegame_tech_tooltip.py`.

#### Scenario: A flat effect shows as a number
- **WHEN** a node has the effects public order 10, approval -3, retinue capacity 12 and manor storage 200
- **THEN** the lines are "Public Order +10", "Approval -3", "Retinue capacity +12" and "Manor storage capacity +200"
- Checked by `harness/tests/test_fakegame_tech_tooltip.py`.

#### Scenario: A condition and a non-statistic effect
- **WHEN** a node has the effect public order 25 with `min_garrison_squads` 4, and it opens a vassal policy
- **THEN** the lines are "Public Order +25 (needs at least 4 garrison squads)" and "Opens vassal policy <policy>"
- Checked by `harness/tests/test_fakegame_tech_tooltip.py`.

#### Scenario: Every effect kind has a text
- **WHEN** the tree data uses any effect kind of `tech_tree.EFFECT_KINDS`
- **THEN** the text builder has a text for that kind
- **AND** a kind without a text makes the builder fail with a message that names the kind
- Checked by `harness/tests/test_fakegame_tech_tooltip.py`.
