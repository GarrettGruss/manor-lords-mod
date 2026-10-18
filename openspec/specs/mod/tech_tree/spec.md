# mod/tech_tree Specification

## Purpose
The tech tree feature gives the player two exclusive paths, Oppression and Prosperity, with nodes, laws and vassal policies. The mod owns and applies all of them. It does not use the game policy system.

## Requirements

### Requirement: The tree is read from a data file
The mod SHALL build the tree from `mod/InvasionMod/data/tech_tree/tree.json` (config `tech_tree.tree_file`). The shipped file has 2 paths, 8 nodes, 6 laws and 2 vassal policy gates. The mod SHALL stop loading the feature with a clear message when the file is bad: an unknown required id, a cycle, a requirement across paths, a duplicate id, an unknown path or an unknown effect kind.

#### Scenario: The shipped file loads
- **WHEN** the feature loads the shipped file
- **THEN** the tree has two paths and eight nodes
- Checked by `harness/tests/test_fakegame_tech_tree.py`.

#### Scenario: A bad file stops the load
- **WHEN** the file has a cycle, an unknown required id or a duplicate id
- **THEN** the load fails with a message that names the problem
- Checked by `harness/tests/test_fakegame_tech_tree.py`.

#### Scenario: The laws are loaded and checked
- **WHEN** a law names an unknown node, a node of the other path or an unknown effect kind
- **THEN** the load fails with a message
- Checked by `harness/tests/test_fakegame_laws.py`.

### Requirement: The player picks one path and the choice is final
The mod SHALL start with no path. The player SHALL pick one path with `InvasionMod.tech_tree_choose_path`. A second choice SHALL be refused and the first path SHALL stay. The path is kept in mod state (key `tech_path`) and not in a save call.

#### Scenario: The first choice and the second choice
- **WHEN** the player picks Oppression and then calls the command again
- **THEN** the second call is refused
- **AND** the path is still Oppression
- Checked by `mod/InvasionMod/scenarios/tech_tree/path_choice.py`.

#### Scenario: A node needs a path
- **WHEN** the player unlocks a node before a path is chosen
- **THEN** the call is refused with the message "no path is chosen"
- Checked by `mod/InvasionMod/scenarios/tech_tree/path_choice.py`.

#### Scenario: The choice is kept in the pawn tags
- **WHEN** a path and a node are chosen
- **THEN** the mod state keys `tech_path` and `tech_nodes` hold them
- Checked by `harness/tests/test_fakegame_tech_tree.py`.

### Requirement: One node slot for each settlement level
The mod SHALL allow as many unlocked nodes as the settlement level of the player region times `slots_per_level` (default 1). A node is free of cost. A node needs the nodes it `requires` first, and a node of the other path is refused. A node cannot be unlocked twice.

#### Scenario: Slots follow the level
- **WHEN** the settlement level is 1 and the player unlocks the first node
- **THEN** one slot is used and a second node is refused with "no free node slot"
- Checked by `mod/InvasionMod/scenarios/tech_tree/path_choice.py`.

#### Scenario: Order and path rules
- **WHEN** the player unlocks a node before its required node, or a node of the other path
- **THEN** the call is refused with the reason
- Checked by `mod/InvasionMod/scenarios/tech_tree/path_choice.py`.

#### Scenario: Two levels give two slots
- **WHEN** the settlement level is 2
- **THEN** two nodes can be unlocked in order
- Checked by `harness/tests/test_fakegame_tech_tree.py`.

### Requirement: Oppression nodes raise Public Order
The nodes of the Oppression path SHALL add Public Order: Martial Law +10, Iron Hand +15 and Fear of the Lord +25. Fear of the Lord counts only while the player commands at least 4 squads. Iron Hand also raises the buy-back price of bandits by 25 percent. Veteran Levies raises the defence of the militia by 10 percent. The values are tunable in `tree.json`.

#### Scenario: Martial Law and Iron Hand
- **WHEN** the player unlocks Martial Law and then Iron Hand
- **THEN** Public Order equals the natural order plus 10 (then 25) minus the approval debuff, within the limits 0 to 100
- **AND** the buy-back price factor is 1.25 and a buy-back of 2 families costs 25 silver
- Checked by `mod/InvasionMod/scenarios/tech_tree/path_choice.py`.

#### Scenario: Fear of the Lord needs four squads
- **WHEN** the player unlocks Fear of the Lord with fewer than 4 squads
- **THEN** the +25 does not count
- **AND** it counts with 4 squads
- Checked by `harness/tests/test_fakegame_tech_tree.py`.

### Requirement: Prosperity nodes raise approval and cut costs
The nodes of the Prosperity path SHALL raise approval: Fair Courts +5 and Golden Age +15. The approval bonus lowers the Public Order debuff of the bandits feature. Amnesty halves the buy-back price of bandits. Militia Rights raises the attack of the militia by 10 percent. The real approval value is not written.

#### Scenario: Approval removes the debuff
- **WHEN** the player has Golden Age and approval is high
- **THEN** the Public Order debuff is removed
- Checked by `harness/tests/test_fakegame_tech_tree.py`.

#### Scenario: Amnesty halves the price
- **WHEN** the player unlocks Amnesty
- **THEN** the buy-back price factor is 0.5
- Checked by `harness/tests/test_fakegame_tech_tree.py`.

### Requirement: Militia factors reach the player militia
The mod SHALL scale the attack and the defence of the militia units of the player by the factors of the unlocked nodes and laws. It SHALL NOT scale other sides and SHALL NOT apply a factor twice. The militia is found by the role Husband or Son.

#### Scenario: Militia Rights raises the attack
- **WHEN** the player has Militia Rights
- **THEN** the militia attack is 1.1 times the base value and stays so for 20 game seconds
- Checked by `mod/InvasionMod/scenarios/tech_tree/militia_factor.py`.

#### Scenario: Only the player militia changes
- **WHEN** a factor is set
- **THEN** only the militia of the player is scaled, once
- Checked by `harness/tests/test_fakegame_tech_tree.py`.

### Requirement: Laws can be enacted and repealed
The mod SHALL let the player enact a law of the chosen path when the node it requires is unlocked. A law is free and can be repealed. At most `max_active_laws` laws (default 2) are in force. The six laws are: Conscription, Forced Labor on Walls, Scorched Earth (Oppression), and Militia Charter, Trade Pacts, Pay Off Warbands (Prosperity). The laws are kept in mod state (key `tech_laws`).

#### Scenario: Law places and refusals
- **WHEN** the player enacts a third law, a law of the other path, or a law whose node is locked
- **THEN** the call is refused with the reason
- Checked by `harness/tests/test_fakegame_laws.py`.

#### Scenario: Trade Pacts raise the tribute
- **WHEN** the player enacts Trade Pacts and a vassal with 5 families pays at loyalty 50
- **THEN** the tribute is between 12 and 14 units, and after the repeal it is 10 again
- **AND** the vassal loyalty rises by at least 3 at the season change
- Checked by `mod/InvasionMod/scenarios/tech_tree/laws.py`.

### Requirement: Nodes open vassal policies
The mod SHALL gate the vassal tribute policies: `heavy` needs the Oppression path and Martial Law, `light` needs the Prosperity path and Fair Courts, and `fair` is always open. The command `InvasionMod.tech_tree_set_vassal_policy` SHALL check the gate before it sets the policy.

#### Scenario: Gates refuse a wrong policy
- **WHEN** the player on Prosperity sets `heavy`, or sets `light` before Fair Courts
- **THEN** the call is refused with the reason
- Checked by `mod/InvasionMod/scenarios/tech_tree/laws.py`.

#### Scenario: Gate rules without the game
- **WHEN** a policy is set with the node unlocked or with the policy `fair`
- **THEN** the call is allowed
- Checked by `harness/tests/test_fakegame_laws.py`.

### Requirement: Named commands for the tree
The mod SHALL register the commands `InvasionMod.tech_tree_state`, `tech_tree_choose_path`, `tech_tree_unlock`, `tech_tree_enact_law`, `tech_tree_repeal_law` and `tech_tree_set_vassal_policy`. The state lists the path, the unlocked nodes, the laws in force, the slots, the effect totals and every node.

#### Scenario: The state at the start
- **WHEN** a new game starts
- **THEN** the state shows path "none", 8 nodes, no unlocked node and 1 slot at settlement level 1
- Checked by `mod/InvasionMod/scenarios/tech_tree/path_choice.py`.
