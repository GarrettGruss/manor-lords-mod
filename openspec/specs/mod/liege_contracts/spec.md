# mod/liege_contracts Specification

## Purpose
The liege offers three contracts at each start of spring. The player picks one. A completed contract pays rewards at once; a contract that is not complete when winter begins costs influence. The contracts are a data table, and the liege window shows them as cards.

## Requirements

### Requirement: Contracts live in a data table
The mod SHALL read all contracts from the data file `mod/InvasionMod/data/liege_contracts/contracts.json`. No contract id, amount or text SHALL be in Lua code. The table holds, for each tier (`small`, `medium`, `large`), a pool of requests and a pool of rewards, and an optional top level list `groups` of interchangeable goods. A bad table SHALL stop the load with a clear message.

#### Scenario: The table fields
- **WHEN** the table loads
- **THEN** it holds `version` (3), `offer_per_tier` (default 3) and the three tiers
- **AND** each request of Small and Medium has `good` and `weight` (above 0); each request of Large has `cost` (a cost kind), `min` and `max` (the amount range) and `weight` (above 0)
- **AND** each reward has `kind` (`goods`, `weapons`, `armor`, `law`, `kings_favour`, `law_slot` or `relief_promise`), `goods` where the kind needs one (the name of a list of good ids in the top level field `good_lists`), `min` and `max` (the reward amount range)
- **AND** each group has `goods` (at least 2 good ids, no id in two groups) and an optional `label` (text)
- **AND** the table has no `duration` and no penalty field
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The starter table loads
- **WHEN** the feature loads the starter table
- **THEN** each tier has at least `offer_per_tier` requests and at least one reward, and every good id is known (an id of `DT_Items`)
- **AND** Small requests are only the renewable goods and Medium requests are only the processed goods of table 1 in `design.md`
- **AND** every good of a group has a name
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A bad table stops the load
- **WHEN** the table has an unknown kind, a missing field, a weight of 0 or less, fewer requests in a tier than `offer_per_tier`, a group with fewer than 2 goods, a good in two groups, or two requests of one tier in the same group
- **THEN** the load fails and the message names the tier or group and the field
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Reward types
The mod SHALL support these reward kinds, paid once when the player fulfils a contract. Each contract has exactly one reward, drawn from the reward pool of its tier. A reward that cannot be paid SHALL be logged and counted in `failed_rewards`, and SHALL NOT be retried. The kinds `regional_wealth`, `silver`, `tech_point` and `influence` SHALL NOT be in any reward pool.

#### Scenario: The types and their effect
- **WHEN** a contract pays a reward kind
- **THEN** `goods`, `weapons` and `armor` (`good`, `amount`) add the goods to a storehouse
- **AND** `law` unlocks one random law that is not unlocked yet, through `laws_unlock(id, source)` of `add-laws-menu`
- **AND** `kings_favour` raises `kingsFavour` of the player by the amount
- **AND** `law_slot` adds one law slot through `laws_add_slot()` of `add-laws-menu`
- **AND** `relief_promise` raises the mod state value `relief_bonus_squads` by the amount
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

#### Scenario: Rewards by tier
- **WHEN** the offer is drawn
- **THEN** a Small contract pays vassal goods (salt, iron ore, clay, flax or stone), a Medium contract pays tools, ale, cider, mead or clothes, and a Large contract pays a law, King's Favour, weapons, armor, a law slot or a relief promise (the pools of table 2 in `design.md`)
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A completed contract pays every reward
- **WHEN** the player fulfils a contract whose reward is King's Favour
- **THEN** `kingsFavour` rises by the amount, the cost is taken, and the contract shows as fulfilled
- Checked by `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

#### Scenario: A reward that fails
- **WHEN** the goods reward finds no storehouse
- **THEN** `failed_rewards` rises and a log line names the reward
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Contract state is saved
The mod SHALL keep the contract state in ModState and restore it after a load: the spring counter (it names the year of the offer), the offer, the fulfilled count of each tier and the count of done contracts. Old saves with no contract keys SHALL load with defaults. The saved key `liege_influence` SHALL stay. The key `arms_last_day` is no longer written (the arms shipment is removed).

#### Scenario: The keys
- **WHEN** the state is written
- **THEN** the keys are `contracts_spring_no` (integer, -1: no offer yet), `contracts_offer` (the 9 contracts with request and reward amounts, text form), `contracts_used` (fulfilled count of each tier, text form) and `contracts_done`
- **AND** the keys `contracts_active`, `contracts_start_day`, `contracts_baseline`, `contracts_progress` and `contracts_failed` are gone
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: State round trip
- **WHEN** the offer holds 9 contracts, one is fulfilled, and the game is saved and loaded
- **THEN** `liege_contracts_state` shows the same 9 contracts (same amounts) and the same fulfilled counts
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/roundtrip.py` (a real load needs the guarded `save_game`).

#### Scenario: An old save
- **WHEN** a save made before this change loads
- **THEN** the influence is unchanged, the old offer and the old active contract are dropped without penalty, and the first new offer comes at the next start of spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A removed contract id
- **WHEN** the save holds an offer with a request or reward that the table no longer has
- **THEN** that contract is dropped, no penalty applies and the log names the id
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The liege window opens in at most 2 clicks
The player SHALL open the root of the liege window from the game UI with the mouse in at most 2 clicks, with no hotkey. The window SHALL update the stock and the button states after a fulfilment. The rule covers only the root window.

#### Scenario: Opens in 2 clicks
- **WHEN** the player is in the normal game view with no mod menu open
- **THEN** the player opens the liege window with at most 2 clicks on game UI elements, and no key press
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`.

#### Scenario: Values update
- **WHEN** the player fulfils a contract while the window is open
- **THEN** the "Fulfilled" count of the tier, the "In storage" lines and the button states change to the new values
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`.

### Requirement: The feature offers named commands
The mod SHALL register the commands `InvasionMod.liege_contracts_state`, `liege_contract_fulfil` (argument: the contract id) and `liege_contracts_offer_now`. Tests and the window SHALL use them, not eval. The commands `liege_contract_pick`, `liege_contract_complete`, `liege_contracts_test_progress` and `liege_send_tribute` SHALL NOT exist. The state SHALL go to the telemetry metrics `liege_contracts_done` and `liege_contracts_offered`.

#### Scenario: State is readable
- **WHEN** a scenario sends `InvasionMod.liege_contracts_state`
- **THEN** the answer holds the 9 contracts, the fulfilled count and limit of each tier, the days to the start of winter, the days to the next spring, `failed_rewards` and the spring counter
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: Test commands (also `liege_menu_press`, argument: the button name, runs the code of a click)
- **WHEN** a scenario sends `liege_contracts_offer_now` (optional argument `ids` names the offer in the saved text form of `contracts_offer`)
- **THEN** the offer changes at once, with no wait for a spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The tribute command is gone
- **WHEN** a scenario sends `InvasionMod.liege_send_tribute`, `liege_contract_pick` or `liege_contract_complete`
- **THEN** the harness answers that the command is unknown
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Requests are deliveries of goods
A Small or Medium contract SHALL ask for the delivery of one good, or of one group of interchangeable goods, in one amount. A request for a good of a group SHALL accept any mix of the goods of the group. A Small contract asks for a renewable good and a Medium contract for a processed good. A Large contract SHALL ask for one cost, not for goods (requirement `Large contracts ask for a cost`). The starter table has the groups hides and pelts (ids 3 and 9) and berries and mushrooms (ids 171 and 279).

#### Scenario: The request is a delivery
- **WHEN** a Small or Medium contract is drawn
- **THEN** it holds one good id of the goods list of its tier and one amount
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: Stock is read from the player region
- **WHEN** a card shows "In storage: <have> / <need>"
- **THEN** `<have>` is the stock of the good in the player region (any store, as today), and for a group it is the sum of the stocks of all goods of the group
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`.

#### Scenario: A group contract shows both goods
- **WHEN** a contract asks for berries (group berries and mushrooms) in the amount 40
- **THEN** the card text is "Deliver 40 berries/fungi" and the text fits the card
- **AND** with 25 berries and 20 mushrooms in the stores the card shows "In storage: 45 / 40" and Fulfil is enabled
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/interchangeable.py`.

#### Scenario: Fulfil takes from the larger stock first
- **WHEN** a group contract for 40 is fulfilled with 25 berries and 30 mushrooms
- **THEN** 30 mushrooms and 10 berries are taken
- **AND** if a take is short, every taken unit is put back and the contract stays open
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: One offer never holds a group twice
- **WHEN** an offer is drawn
- **THEN** no tier holds two contracts of the same group, and the reward good is never a good of the request group
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: Saved contracts of a group member still load
- **WHEN** a saved offer holds a contract for mushrooms and the table has the request for berries in the same group
- **THEN** the contract loads and counts as the group
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The request amount comes from a formula
The amount of a Small or Medium request SHALL be `max(1, round(base(tier) * weight(good) * difficulty))`, rounded half up. `base(tier)` and `difficulty` are config values (base 50 for Small and 30 for Medium); `weight(good)` is the `weight` of the request in the data table, and a config value `liege_contracts.weight[good]` overrides it. The amount of a Large cost SHALL be `max(1, round(amount * difficulty))` with `amount` drawn between `min` and `max`. The difficulty comes from the yearly raid level of the scenario settings (proposed: level 1 gives 0.75, level 2 gives 1.0, level 3 gives 1.25, level 0 gives 1.0).

#### Scenario: The amount formula
- **WHEN** a Small contract asks for rubble stone (base 50, weight 1.6) at difficulty 1.25
- **THEN** the amount is 100 (`50 * 1.6 * 1.25`), and at difficulty 1.0 it is 80
- **AND** a result below 1 gives 1, and a changed base, weight or difficulty in config changes the amount
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A Large cost amount
- **WHEN** a Large contract draws the cost `send_families` with a drawn amount of 3 at difficulty 1.25
- **THEN** the cost amount is 4 (`3 * 1.25 = 3.75`, rounded half up)
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The mod offers nine contracts each spring
At each start of spring, with or without a built manor, the mod SHALL draw `offer_per_tier` different contracts (default 3) at random from each tier and offer them. The new offer SHALL replace the old one and reset the fulfilled counts. A game that starts in spring (a new game starts on day 61 in spring) SHALL get its offer at the first poll. A game that starts in another season SHALL make no offer until the next spring. A load SHALL NOT deal a second offer for a spring that was already dealt. The offer SHALL be saved before it is logged.

#### Scenario: A spring draw
- **WHEN** the season counter shows a new spring (read as in `mod/tech_tree`)
- **THEN** the offer holds 3 different contracts for each tier (9 in all) and every fulfilled count is 0
- **AND** one offer is made for each spring counter value
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: No second draw after a load
- **WHEN** an offer exists, the game is saved and loaded
- **THEN** the offer holds the same contracts and no new draw happens before the next spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/roundtrip.py`.

#### Scenario: A game that starts in another season
- **WHEN** a new game starts in summer, or a save that is not in spring loads without contract state
- **THEN** no offer is made, the window shows the time to the next spring, and the first offer comes at the next start of spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A game that starts in spring
- **WHEN** a new game starts in spring (day 61), with no contract state
- **THEN** the offer holds 9 contracts at the first poll, with no test command, and a load in the same spring deals no second offer
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/new_game_offer.py`.

### Requirement: The player fulfils contracts, up to a limit for each tier
The command `InvasionMod.liege_contract_fulfil` (argument: the contract id, for example `small-1`) SHALL take what the contract asks for (the goods from the buildings of the player region that hold them, the known stores first and food in a building of type 80; or the cost of a Large contract) and pay the reward at once. The player may fulfil at most N contracts of each tier in a year (config value `liege_contracts.tier_limits`, default 1). A refused call SHALL change nothing and SHALL give the reason.

#### Scenario: A fulfilment
- **WHEN** the stock of the good is at or above the amount (or the cost can be paid) and the tier count is below the limit, and the player fulfils the contract
- **THEN** the stock falls by the amount (or the cost is taken), the reward is paid, the tier count rises by 1 and `contracts_done` rises by 1
- Checked by `mod/InvasionMod/scenarios/liege_contracts/fulfil.py` and `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: Not enough goods
- **WHEN** the stock is below the amount and the player fulfils the contract
- **THEN** the call is refused with the missing amount and nothing is taken or paid
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The tier limit
- **WHEN** the limit of a tier is 1 and one contract of that tier is fulfilled
- **THEN** a second contract of that tier is refused, even with enough goods, and contracts of the other tiers are not affected
- **AND** a changed config value changes the limit
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Contracts expire when winter begins
When winter begins, the mod SHALL clear the offer. An unfulfilled contract SHALL have NO penalty: the influence, the silver and the goods do not change. The config value `liege_contracts.fail_penalty` SHALL NOT exist. New contracts come at the next spring.

#### Scenario: Winter clears the offer
- **WHEN** winter begins with unfulfilled contracts in the offer
- **THEN** the offer is empty, the influence is unchanged and no failure is counted
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: No contracts in winter
- **WHEN** the player opens the window in winter
- **THEN** the window shows no cards and shows the time to the next spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The liege window shows contracts by tier
The liege window (menu id `liege`, a pak widget) SHALL follow the game-menu style of the mockup `liege-contracts-game-style.html` (in `openspec/changes/update-liege-contracts-window-style/mockups/`; after the archive, in `openspec/specs/mod/liege_contracts/mockups/`). The layout is: a centred title "Contracts of the Liege", one countdown line, and one dark panel with three rows (Small, Medium, Large) of three cards. The only Close is the framework's bottom-centre Close; the widget has no Close. It SHALL use only controls of the pak and hide the unused ones. The behavior (tiers, amounts, manor check, notice line, countdowns) does not change.

#### Scenario: The style
- **WHEN** the window is open
- **THEN** the background is near-black with no beige panel, the title is in spaced small capitals with a thin gold rule under it, and the tier rows are in one dark grey panel
- **AND** card text is white serif, goods and rewards are gold capitals, and a missing amount is muted red
- Checked by picture evidence and the test scenario `liege-contracts-window`.

#### Scenario: The bars
- **WHEN** the window is open
- **THEN** one line under the title shows "Time to fulfil contracts: <n> days remaining" and "Contracts refresh: In spring, in <n> days", with the numbers in gold
- **AND** there is no influence counter, no treasury counter and no status text
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

#### Scenario: The tier box
- **WHEN** the window is open
- **THEN** each row has a box at the left with the tier name only (Small, Medium or Large), "Fulfilled" and "<used> / <limit>"
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

#### Scenario: A card
- **WHEN** an offer exists
- **THEN** each card shows a diamond-marked list: "Deliver <n> <GOODS>", "In storage: <have> / <need>", "Reward: +<n> <GOODS>", and a plain-text Fulfil
- **AND** a card has no name, no quote and no penalty
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

#### Scenario: The Fulfil button
- **WHEN** the manor is built, the goods are in storage and the tier limit is not reached
- **THEN** Fulfil is plain serif text with no box, and a click calls the same code as `liege_contract_fulfil`
- **AND** otherwise the card is dimmed and clicks are ignored
- **AND** after a fulfilment the card shows a gold "Fulfilled"
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

#### Scenario: Only the framework Close
- **WHEN** the window is open
- **THEN** the only Close is the game-style Close at the bottom centre, drawn by the menu framework, and the widget has no Close
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

#### Scenario: The countdowns
- **WHEN** the window is open in spring, summer or autumn
- **THEN** "days remaining" is the number of game days until winter begins (day 335 of the calendar year, `TemporalComponent.day`), and "In spring, in <n> days" is the number of game days until the next spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The window has no offer
- **WHEN** no offer exists (a game that did not start in spring, or winter)
- **THEN** the cards are hidden and the window shows the time to the next spring
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: No arms shipment button
- **WHEN** the window is open
- **THEN** it shows no "Request arms shipment" button (the arms shipment is removed; see the delta of `mod/liege_influence`)
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`.

### Requirement: Fulfilling needs a built manor
The mod SHALL deal the offer whether or not a manor exists. A contract SHALL be fulfilled only when the player's manor is built (a `HarnessManor.manor_state()` module with `built == true`). The Fulfil button SHALL be enabled only when the manor is built, the goods are in storage and the tier limit is not reached. The command `liege_contract_fulfil` SHALL check the manor again at click time and refuse if it is not built.

#### Scenario: No manor
- **WHEN** no manor is built and an offer exists
- **THEN** the window shows the 9 contracts, all Fulfil buttons are greyed, and the line "Build a manor to fulfil contracts." shows above the rows
- **AND** the offer is dealt at spring as usual
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/window.py`.

#### Scenario: The command refuses without a manor
- **WHEN** no manor is built and `liege_contract_fulfil` is sent, even with enough goods
- **THEN** the call is refused with the reason "Build a manor to fulfil contracts." and nothing is taken or paid
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The manor is lost
- **WHEN** the manor is no longer built
- **THEN** the Fulfil buttons are greyed again and the offer stays
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Large contracts ask for a cost
A Large contract SHALL hold one cost in place of goods: `loan_units` (default 1 squad for 60 game days), `send_families` (default 3 families, for good) or `tribute_season` (default 3 months of vassal tribute), as in table 2 of `design.md`. The amount SHALL scale with the difficulty. A cost SHALL be taken only at fulfilment. A cost kind with no safe method SHALL NOT be in the table (not the herd, not the peasant loan).

#### Scenario: A cost is taken
- **WHEN** the player fulfils a Large contract with the cost `send_families` (3 families) and the player region holds at least 4 families
- **THEN** the family count falls by 3 and the reward is paid
- Checked by `mod/InvasionMod/scenarios/liege_contracts/fulfil.py` (after the spike tasks).

#### Scenario: Costs scale and loans are switchable
- **WHEN** a Large contract is drawn at difficulty 1.25
- **THEN** its amount is `max(1, round(amount * difficulty))` (3 families become 4) and the loan length stays 60 days
- **AND** `loan_units` is drawn only while `liege_contracts.loan_enabled` is true
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A cost that cannot be paid
- **WHEN** the player region holds fewer families (one family must stay), squads or vassals than the cost needs
- **THEN** the call is refused with the missing amount and nothing is taken or paid
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A loan ends
- **WHEN** a `loan_units` contract is fulfilled and 60 game days pass
- **THEN** a squad of the same template returns to the player (equal, not the same men), and the loan record is kept in mod state across a save and load
- **AND** a squad whose type is not known is refused with a reason, and nothing is taken
- Checked by `harness/tests/test_fakegame_liege_contracts.py` (after the result of `spike-loan-units`).

#### Scenario: The card shows the cost
- **WHEN** a Large card is shown
- **THEN** it shows "Cost: <text>" in place of "Deliver <n> <GOODS>", for example "Cost: 3 families, for good", and "Reward: <text>"
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

### Requirement: Law rewards follow the Laws menu rules
A `law` reward SHALL unlock one random law that is not unlocked yet, through `laws_unlock(id, source)` of `add-laws-menu`, and SHALL NOT be drawn when no law is locked. The law SHALL work whatever the tech path (owner decision 2026-11-04). Law slots start at 1 and are at most 5 in total. A `law_slot` reward SHALL NOT be drawn at 5 slots; if fulfilled at 5 slots it pays `kings_favour` instead (owner decision 2026-11-05). The mod SHALL keep no law state of its own.

#### Scenario: A law reward
- **WHEN** a Large contract with the reward `law` is fulfilled and 3 laws are locked
- **THEN** one of the 3 locked laws is unlocked with the source "Contract: <name>", and the Laws menu shows it as Unlocked
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

#### Scenario: A law of the other path
- **WHEN** the player follows one tech path and a contract unlocks a law of the other path
- **THEN** the law can be enacted
- Checked by `harness/tests/test_fakegame_liege_contracts.py` (needs the gate 2 of `add-laws-menu`).

#### Scenario: No locked law
- **WHEN** all nine laws are unlocked and the offer is drawn
- **THEN** no Large contract has the reward `law`
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The slot cap
- **WHEN** the total of law slots is 5 and a contract with the reward `law_slot` is fulfilled
- **THEN** the slot total stays 5 and `kingsFavour` rises by the default amount
- **AND** with a total of 5 the offer holds no new `law_slot` reward
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: King's Favour and relief promise rewards
A `kings_favour` reward SHALL raise `kingsFavour` of the player pawn by the amount (default 10), through `changeKingsFavour` (spike 1.1). A `relief_promise` reward SHALL raise the mod state value `relief_bonus_squads` (default +5 squads). The great raid SHALL add `relief_bonus_squads` to the squads of the relief army when it spawns, and SHALL reset the value to 0 after that. The value SHALL be saved and restored after a load.

#### Scenario: King's Favour is paid
- **WHEN** a contract with the reward `kings_favour` (amount 10) is fulfilled
- **THEN** `kingsFavour` rises by 10 (a range of 10 and above, because the game may add its own changes)
- Checked by `mod/InvasionMod/scenarios/liege_contracts/fulfil.py` and `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A bigger relief army
- **WHEN** a `relief_promise` of 5 squads is paid and the great raid spawns its relief army at difficulty 1 (15 squads)
- **THEN** the relief army has 20 squads, and `relief_bonus_squads` is 0 afterwards
- **AND** at difficulty 3 (0 base squads) the relief army has 5 squads
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and a test scenario of the invasion feature.

#### Scenario: The promise survives a load
- **WHEN** `relief_bonus_squads` is 5, and the game is saved and loaded
- **THEN** `relief_bonus_squads` is 5
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.
