# mod/liege_contracts Specification

## Purpose
The liege offers three contracts at each start of spring. The player picks one. A completed contract pays rewards at once; a contract that is not complete when winter begins costs influence. The contracts are a data table, and the liege window shows them as cards.

## Requirements

### Requirement: Contracts live in a data table
The mod SHALL read all contracts from the data file `mod/InvasionMod/data/liege_contracts/contracts.json`. No contract id, amount or text SHALL be in Lua code. A bad table SHALL stop the load with a clear message.

#### Scenario: The table fields
- **WHEN** the table loads
- **THEN** it holds `version`, `offer_size` (default 3), and `contracts`
- **AND** each contract has `id` (unique), `name`, `quote` (flavor text, may be empty), `weight` (above 0), `objectives` (1 or 2), `rewards` (1 to 3) and `duration`
- **AND** `duration` is `winter_start` or a number of game days
- **AND** the table has no envoy and no penalty field (the penalty is the config value `liege_contracts.fail_penalty`)
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The starter table loads
- **WHEN** the feature loads the starter table
- **THEN** it holds at least 8 contracts and every objective and reward type is known
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A bad table stops the load
- **WHEN** the table has a duplicate id, an unknown type, a missing field or fewer contracts than `offer_size`
- **THEN** the load fails and the message names the contract and the field
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Objective types
The mod SHALL support five objective types. The poll reads the progress of each one. A contract is complete when all its objectives reach their target. No objective SHALL use regional wealth or the regional treasury (no safe read is proven).

#### Scenario: The types and their progress
- **WHEN** a contract uses an objective type
- **THEN** `deliver_goods` (fields `good`, `amount`) counts the stock of the good in the player region and takes the goods at completion
- **AND** `build_count` (`building_type`, `amount`) counts buildings of that type built after the pick
- **AND** `kill_raiders` (`amount`) counts raiders of tracked raids that `raid_behavior` saw die after the pick (a running total; deaths in a bandit camp are not counted, `notes/kill-count.md`)
- **AND** `hold_public_order` (`min`, `days`) counts consecutive game days with the mod order at or above `min`
- **AND** `raise_militia_squads` (`amount`) counts the militia squads of the player
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/progress.py`.

#### Scenario: Hold public order resets
- **WHEN** the mod order falls under `min` after 40 days of a 90 day objective
- **THEN** the progress is 0 and counts again from the next day at or above `min`
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Reward types
The mod SHALL support five reward types, paid once when the player completes a contract. A reward that cannot be paid SHALL be logged and counted in `failed_rewards`, SHALL NOT block the other rewards and SHALL NOT be retried. No reward SHALL use regional wealth.

#### Scenario: The types and their effect
- **WHEN** a contract pays a reward type
- **THEN** `influence` raises the influence, and `silver` raises the silver of the lord's treasury
- **AND** `goods` (`good`, `amount`) adds the goods to a storehouse
- **AND** `public_order` raises the mod order once, clamped to 0..100
- **AND** `tech_pick` adds tech picks (ModState `tech_picks_earned`) that the player spends in the tech tree, and is allowed only when `update-tech-tree-yearly-picks` is built
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/complete.py`.

#### Scenario: A completed contract pays every reward
- **WHEN** the player completes a contract with influence, silver and goods rewards
- **THEN** the influence, the silver and the stock rise by the table amounts
- **AND** the contract is closed and `contracts_done` rises by 1
- Checked by `mod/InvasionMod/scenarios/liege_contracts/complete.py`.

#### Scenario: A reward that fails
- **WHEN** the goods reward finds no storehouse
- **THEN** `failed_rewards` rises, the other rewards are paid and a log line names the reward
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The mod offers three contracts each spring
At each start of spring, and only then, the mod SHALL draw `offer_size` different contracts at random, with a chance in proportion to `weight`, and offer them. The new offer SHALL replace the old one. The mod SHALL NOT make an offer at the first poll of a new game or of a save. The offer SHALL be saved before it is logged.

#### Scenario: A spring draw
- **WHEN** the season counter shows a new spring (read as in `mod/tech_tree`)
- **THEN** the offer holds 3 different ids from the table
- **AND** one offer is made for each spring counter value
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: Weights
- **WHEN** 2000 draws run with a seeded random function and one contract has weight 10 and another weight 5
- **THEN** the first is offered about twice as often as the second (within 15 percent)
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: No second draw after a load
- **WHEN** an offer exists, the game is saved and loaded
- **THEN** the offer holds the same ids and no new draw happens before the next spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py`; a real load needs the guarded `save_game`: `mod/InvasionMod/scenarios/liege_contracts/roundtrip.py`.

#### Scenario: A game that starts in another season
- **WHEN** a new game starts in summer, or a save that is not in spring loads without contract state
- **THEN** no offer is made, the window shows that the liege sends contracts at the next spring, and the first offer comes at the next start of spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The player picks exactly one contract
The command `InvasionMod.liege_contract_pick` (argument: the contract id) SHALL activate a contract of the current offer and discard the others. The player SHALL have at most one active contract. A pick starts the clock of the duration and takes the baseline of each objective.

#### Scenario: A pick discards the others
- **WHEN** the offer holds A, B and C and the player picks B
- **THEN** B is active and A and C are gone from the offer
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/pick.py`.

#### Scenario: Refused picks
- **WHEN** the player picks while a contract is active, picks an id outside the offer, or picks with no offer
- **THEN** the call is refused with the reason and the state is unchanged
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: An unpicked offer
- **WHEN** the player picks nothing for a year
- **THEN** nothing happens: the offer stays open until the next spring and then 3 new contracts replace it
- **AND** the influence is unchanged (no penalty)
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Completion, deadline and penalty
The command `InvasionMod.liege_contract_complete` SHALL complete the active contract when all objectives reach their target, take the goods of the `deliver_goods` objectives at that moment and pay the rewards at once. Early completion SHALL give no extra reward. A contract that is not complete when winter begins SHALL fail and take the config value `liege_contracts.fail_penalty` (default 500) from the influence, never below 0. Completion SHALL NOT start a new offer.

#### Scenario: Completion
- **WHEN** all objectives of the active contract reach their target and the player completes it
- **THEN** the goods are taken, the rewards are paid and the contract is closed
- Checked by `mod/InvasionMod/scenarios/liege_contracts/complete.py`.

#### Scenario: An incomplete contract is refused
- **WHEN** an objective is below its target and the player completes the contract
- **THEN** the call is refused with the missing amount and nothing is taken or paid
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The deadline passes
- **WHEN** winter begins and the active contract (`winter_start`) is not complete
- **THEN** the influence falls by `fail_penalty` (500; to 0 at the lowest), `contracts_failed` rises and the contract is closed
- **AND** a changed config value changes the penalty
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A day count
- **WHEN** a contract has `duration` 120 and 120 game days pass after the pick
- **THEN** it fails with the penalty at day 120, not at the start of winter
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Contract state is saved
The mod SHALL keep the contract state in ModState and restore it after a load: the spring counter, the offer, the active contract, its start day, baseline and progress, and the counts of done and failed contracts. Old saves with no contract keys SHALL load with defaults. The saved keys `liege_influence` and `arms_last_day` SHALL stay.

#### Scenario: The keys
- **WHEN** the state is written
- **THEN** the keys are `contracts_spring_no` (integer, -1: no offer yet), `contracts_offer` (ids, dot separated), `contracts_active` (id, empty for none), `contracts_start_day`, `contracts_baseline` (same text form), `contracts_progress` (text, entries `o<index>-<value>` separated by dots), `contracts_done` and `contracts_failed`
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: State round trip
- **WHEN** a contract is active with progress and the game is saved and loaded
- **THEN** `liege_contracts_state` shows the same active contract, the same progress and the same deadline
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/roundtrip.py`.

#### Scenario: An old save
- **WHEN** a save made before this change loads
- **THEN** the influence and the arms cooldown are unchanged and the first offer comes at the next start of spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A removed contract id
- **WHEN** the save holds an active id that the table no longer has
- **THEN** the contract is dropped, no penalty applies and the log names the id
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The liege window shows three contract cards
The liege window (menu id `liege`, a pak widget) SHALL follow the layout of the mockup `openspec/specs/mod/liege_contracts/mockups/liege-contracts-layout.html`: a title, the influence and the silver, and three cards side by side. The window has no envoy and no portrait. A click on PICK SHALL call the same code as `liege_contract_pick`. The window SHALL use only controls of the pak (fixed pools) and hide the unused ones.

#### Scenario: The cards
- **WHEN** an offer exists and the player opens the window
- **THEN** three cards show, each with the contract name, its flavor text (when the table has one), an OBJECTIVE section (1 or 2 items), a REWARDS section (up to 3 items), a penalty badge and a PICK button
- **AND** each item shows an icon box and an amount
- Checked by picture evidence in `evidence/` of this change (archived with it) and `mod/InvasionMod/scenarios/liege_contracts/window.py`.

#### Scenario: Picking in the window
- **WHEN** the player clicks PICK on the second card
- **THEN** that contract is active, the other cards show as discarded and the active panel shows its progress, the days left and a Complete button
- **AND** the Complete button is enabled only when all objectives are complete, and calls the same code as `liege_contract_complete`
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`.

#### Scenario: A tooltip
- **WHEN** the mouse is over an objective or reward item
- **THEN** the name and the description of the item show: as a tooltip text on the item and, because the game draws no hover box over this widget, in the footer line of the window (`notes/tooltip-hover.md`)
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

#### Scenario: The window has no offer
- **WHEN** no offer exists (for example in a game that did not start in spring)
- **THEN** the cards are hidden and the window says that the liege sends contracts at the next spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The arms shipment stays
- **WHEN** the window is open
- **THEN** the button "Request arms shipment" and its reason line show as today (see `mod/liege_influence`)
- Checked by `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py`, updated.

### Requirement: The liege window opens in at most 2 clicks
The player SHALL open the root of the liege window from the game UI with the mouse in at most 2 clicks, with no hotkey. The window SHALL update the influence and the silver after a pick, a completion or an arms shipment. The rule covers only the root window.

#### Scenario: Opens in 2 clicks
- **WHEN** the player is in the normal game view with no mod menu open
- **THEN** the player opens the liege window with at most 2 clicks on game UI elements, and no key press
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`.

#### Scenario: Values update
- **WHEN** a contract is completed with silver and influence rewards while the window is open
- **THEN** the shown influence and silver change to the new values
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`.

### Requirement: The feature offers named commands
The mod SHALL register the commands `InvasionMod.liege_contracts_state`, `liege_contract_pick`, `liege_contract_complete`, `liege_contracts_offer_now` and `liege_contracts_test_progress`. Tests and the window SHALL use them, not eval. The command `liege_send_tribute` SHALL NOT exist. The state SHALL go to the telemetry metrics `liege_contract_active`, `liege_contracts_done` and `liege_contracts_failed`.

#### Scenario: State is readable
- **WHEN** a scenario sends `InvasionMod.liege_contracts_state`
- **THEN** the answer holds the offer, the active contract with progress, the deadline day, the counters, `failed_rewards` and the spring counter
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: Test commands
- **WHEN** a scenario sends `liege_contracts_offer_now` (optional argument `ids` names the offer) or `liege_contracts_test_progress` (sets the progress of one objective)
- **THEN** the offer or the progress changes at once, with no wait for a spring or for kills
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The tribute command is gone
- **WHEN** a scenario sends `InvasionMod.liege_send_tribute`
- **THEN** the harness answers that the command is unknown
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.
