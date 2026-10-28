## MODIFIED Requirements
<!-- Issue: #499 -->

### Requirement: The tree is read from a data file
The mod SHALL build the tree from `mod/InvasionMod/data/tech_tree/tree.json` (config `tech_tree.tree_file`). The shipped file has 2 paths, 8 path nodes, 3 common techs, 9 laws (6 path laws and 3 common laws) and 2 vassal policy gates. A common tech and a common law belong to no path. The mod SHALL stop loading the feature with a clear message when the file is bad: an unknown required id, a cycle, a requirement across paths, a duplicate id, an unknown path or an unknown effect kind.

#### Scenario: The shipped file loads
- **WHEN** the feature loads the shipped file
- **THEN** the tree has two paths, eight path nodes, three common techs and nine laws
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

#### Scenario: A bad file stops the load
- **WHEN** the file has a cycle, an unknown required id or a duplicate id
- **THEN** the load fails with a message that names the problem
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

#### Scenario: The laws are loaded and checked
- **WHEN** a law names an unknown node, a node of the other path or an unknown effect kind
- **THEN** the load fails with a message
- Checked by `harness/tests/test_fakegame_laws.py`.

### Requirement: Laws can be enacted and repealed
The mod SHALL let the player enact a law of the chosen path when the node it requires is unlocked, and a common law when its common tech is unlocked (also before a path is chosen). A law is free and can be repealed. At most `max_active_laws` laws (default 2) are in force, and the common laws count toward the limit. The nine laws are: Conscription, Forced Labor on Walls, Scorched Earth (Oppression), Militia Charter, Trade Pacts, Pay Off Warbands (Prosperity), and Strip the Dead, Disarm the Peasantry and Curfew (common). Trade Pacts raises the tribute only; no law changes vassal loyalty. The laws are kept in mod state (key `tech_laws`).

#### Scenario: Law places and refusals
- **WHEN** the player enacts a third law, a law of the other path, or a law whose node is locked
- **THEN** the call is refused with the reason
- Checked by `harness/tests/test_fakegame_laws.py`.

#### Scenario: A common law counts toward the limit
- **WHEN** the player enacts Conscription and Curfew and then Strip the Dead
- **THEN** the third call is refused as a third law
- Not checked yet (planned: `harness/tests/test_fakegame_laws.py`, updated).

#### Scenario: Trade Pacts raise the tribute
- **WHEN** the player enacts Trade Pacts and a vassal with 5 families and the policy light pays
- **THEN** the tribute is between 12 and 14 units, and after the repeal it is 10 again
- Not checked yet (planned: `mod/InvasionMod/scenarios/tech_tree/laws.py`, updated).

### Requirement: Named commands for the tree
The mod SHALL register the commands `InvasionMod.tech_tree_state`, `tech_tree_choose_path`, `tech_tree_unlock` (a path node or a common tech), `tech_tree_enact_law`, `tech_tree_repeal_law` and `tech_tree_set_vassal_policy`. The state lists the path, the unlocked techs, the laws in force, the picks earned and the picks free, the effect totals and every node and common tech.

#### Scenario: The state at the start
- **WHEN** a new game starts
- **THEN** the state shows path "none", 8 path nodes, 3 common techs, no unlocked tech and `initial_picks` free pick
- Not checked yet (planned: `mod/InvasionMod/scenarios/tech_tree/path_choice.py`, updated).

## REMOVED Requirements

### Requirement: One node slot for each settlement level
**Reason**: The player now gets one pick for each game year, earned at the start of spring and saved when unused (owner, 2026-10-27). The settlement level no longer limits nodes.
**Migration**: See the ADDED requirements "One tech pick for each game year, saved when unused" and "A pick is spent on each unlock and saved with the game". The config `slots_per_level` is removed.

## ADDED Requirements

### Requirement: One tech pick for each game year, saved when unused
The mod SHALL give the player `initial_picks` (default 1) pick at the start and `picks_per_year` (default 1) pick at each start of spring, a new spring on the season counter of the mod. A game that starts in another season SHALL give its first yearly pick at the first spring after the start. A game that starts in spring SHALL give no pick for that spring. An unused pick SHALL be banked.

#### Scenario: A new spring gives a pick
- **WHEN** a new spring starts and the player has used all picks
- **THEN** the player has 1 free pick
- **AND** a node unlock then succeeds, and a second unlock is refused with "no free pick"
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

#### Scenario: Only spring gives a pick
- **WHEN** summer, autumn and winter start and no spring starts
- **THEN** the player gets no new pick
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

#### Scenario: A game that starts in autumn
- **WHEN** a new game starts in autumn and the next spring starts
- **THEN** the player has `initial_picks` at the start, no new pick in winter, and one more pick at the spring
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

#### Scenario: A game that starts in spring
- **WHEN** a new game starts in spring
- **THEN** the player has `initial_picks` only, and the next pick comes at the next spring
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

#### Scenario: Unused picks are banked
- **WHEN** three springs start and the player unlocks nothing
- **THEN** the player has 3 free picks (plus `initial_picks`)
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

#### Scenario: Order and path rules for path nodes
- **WHEN** the player unlocks a path node before its required node, or a node of the other path
- **THEN** the call is refused with the reason
- Checked by `mod/InvasionMod/scenarios/tech_tree/path_choice.py`.

### Requirement: A pick is spent on each unlock and saved with the game
Each unlock of a path node or a common tech SHALL cost one pick. The settlement level SHALL NOT limit picks. The picks earned and the season counter of the last spring that gave a pick SHALL be kept in mod state (`tech_picks_earned`, `tech_spring_no`), saved before use.

#### Scenario: A load keeps the picks
- **WHEN** the player has 2 free picks, the game is saved by the harness action `save_game`, and the slot is loaded in a new run
- **THEN** the player still has 2 free picks and the same spring gives no new pick
- Not checked yet (planned: `mod/InvasionMod/scenarios/tech_tree/picks_roundtrip.py`).

#### Scenario: The settlement level does not matter
- **WHEN** the settlement level is 1 and the player has 3 free picks
- **THEN** three unlocks succeed in order
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

### Requirement: Common techs belong to both paths
The mod SHALL offer three common techs: Corpse Robbing, Armory Census and Night Watch. Any common tech SHALL be unlockable with a free pick, in any order, on either path, also before a path is chosen. A path node SHALL still be refused before a path is chosen. Each common tech opens one law (Strip the Dead, Disarm the Peasantry, Curfew).

#### Scenario: A common tech with no path
- **WHEN** no path is chosen and the player has a free pick and unlocks Night Watch
- **THEN** the unlock succeeds and the state lists it
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

#### Scenario: A path node with no path
- **WHEN** no path is chosen and the player unlocks a path node
- **THEN** the call is refused with "no path is chosen" and costs no pick
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

#### Scenario: Both paths use the same techs
- **WHEN** a player on Oppression and a player on Prosperity unlock Armory Census out of order
- **THEN** both unlocks succeed
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

#### Scenario: A pick on a tech that is taken
- **WHEN** the player unlocks a common tech twice
- **THEN** the second call is refused with "already unlocked" and costs no pick
- Not checked yet (planned: `harness/tests/test_fakegame_tech_tree.py`, updated).

### Requirement: Strip the Dead gives loot from bodies at the corpse pit
While the law Strip the Dead is in force, the mod SHALL pay goods to the corpse pit for each body of a bandit or a soldier that the pit receives, and SHALL lower the mod order by `strip_the_dead.order_loss` (default 1) for each corpse looted, inside the limits 0 to 100. The goods of a body SHALL come from the existing loot rules (see the scenarios). A body with no loot entry pays nothing. Without the law, no body pays (see `mod/raid_behavior`).

#### Scenario: A body is looted
- **WHEN** Strip the Dead is in force and the body of a bandit with a `body_loot` entry reaches the pit
- **THEN** the pit gains the goods of the entry and the mod order falls by 1
- Not checked yet (planned: `mod/InvasionMod/scenarios/tech_tree/strip_the_dead.py`).

#### Scenario: A rebel body with an override
- **WHEN** Strip the Dead is in force and the body of a rebel with an override of 3 spears reaches the pit
- **THEN** the pit gains 3 spears and the entry is cleared
- Not checked yet (planned: `harness/tests/test_fakegame_laws.py`, updated; needs `update-banditry-rebellion-raid`).

#### Scenario: Loot sources
- **WHEN** Strip the Dead is in force and a body reaches the pit
- **THEN** the pit gets, in this order, the loot override of the body (change `update-banditry-rebellion-raid`), else the raid share of a Hussite body, else the entry for its unit type in `raid_behavior.body_loot`
- Not checked yet (planned: `harness/tests/test_fakegame_raid_behavior.py`, updated).

#### Scenario: The law is not in force
- **WHEN** the law is not enacted and a body reaches the pit
- **THEN** the pit gains no goods and the order does not change
- Not checked yet (planned: `harness/tests/test_fakegame_laws.py`, updated).

### Requirement: Disarm the Peasantry moves home weapons to the storehouse
While the law Disarm the Peasantry is in force, the mod SHALL, every `disarm.tick_days` game days (default 1), move each good with an id in `bandits.rebellion_weapon_ids` from every home to the storehouse (`consumeGoodNoCheck`, then `addToInventory`). No family then holds such a good, so the rebellion is blocked. The militia must re-arm when called. The law lowers approval by 3. A missed good is logged (`disarm_homes_missed`) and does not stop the tick.

#### Scenario: Homes are emptied
- **WHEN** the law is in force and 6 homes hold spears (id 133)
- **THEN** after the tick the homes hold none and the storehouse holds the same spears
- Not checked yet (planned: `mod/InvasionMod/scenarios/tech_tree/disarm.py`).

#### Scenario: No rebellion
- **WHEN** the law is in force, the banditry timer expires and all homes are disarmed
- **THEN** no family leaves, no squad spawns and the mod logs `rebellion_blocked`
- Not checked yet (planned: `mod/InvasionMod/scenarios/tech_tree/disarm.py`).

#### Scenario: The law is repealed
- **WHEN** the law is repealed
- **THEN** the mod stops the tick and the approval returns by 3
- Not checked yet (planned: `harness/tests/test_fakegame_laws.py`, updated).

### Requirement: Curfew halves the order loss of banditry
While the law Curfew is in force, the mod SHALL multiply the order loss of each banditry tick (`homeless_term`) by 0.5, rounded half up. The law SHALL lower approval by 4. It SHALL NOT change the timer, the threshold or the order gain.

#### Scenario: Slower loss
- **WHEN** the law is in force and 4 families are homeless (loss 5 each, 20 in total)
- **THEN** the tick loses 10 order
- Not checked yet (planned: `harness/tests/test_fakegame_bandits.py`, updated).

#### Scenario: The law is repealed
- **WHEN** the law is repealed
- **THEN** the next tick loses 20 again
- Not checked yet (planned: `harness/tests/test_fakegame_bandits.py`, updated).
