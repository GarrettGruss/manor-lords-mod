## MODIFIED Requirements
<!-- Issue: #TBD -->

### Requirement: Contracts live in a data table
The mod SHALL read all contracts from the data file `mod/InvasionMod/data/liege_contracts/contracts.json`. No contract id, amount or text SHALL be in Lua code. The table holds, for each tier (`small`, `medium`, `large`), a pool of requests and a pool of rewards. The pools are in the tables of `design.md` of the change `update-liege-contracts-tiers` (proposed defaults; the owner tunes them). A bad table SHALL stop the load with a clear message.

#### Scenario: The table fields
- **WHEN** the table loads
- **THEN** it holds `version`, `offer_per_tier` (default 3) and the three tiers
- **AND** each request has `good` and `weight` (above 0); the base of each tier and the difficulty values are config values
- **AND** each reward has `kind` (`goods`, `weapons`, `regional_wealth`, `silver`, `tech_point` or `influence`), `good` where the kind needs one, `min` and `max` (the reward amount range)
- **AND** the table has no objective type other than goods delivery, no `duration` and no penalty field
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The starter table loads
- **WHEN** the feature loads the starter table
- **THEN** each tier has at least `offer_per_tier` requests and at least one reward, and every good id is known
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A bad table stops the load
- **WHEN** the table has an unknown kind, a missing field, a weight of 0 or less or fewer requests in a tier than `offer_per_tier`
- **THEN** the load fails and the message names the tier and the field
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Reward types
The mod SHALL support six reward kinds, paid once when the player fulfils a contract. Each contract has exactly one reward, drawn from the reward pool of its tier. A reward that cannot be paid SHALL be logged and counted in `failed_rewards`, and SHALL NOT be retried.

#### Scenario: The types and their effect
- **WHEN** a contract pays a reward kind
- **THEN** `goods` and `weapons` (`good`, `amount`) add the goods to a storehouse
- **AND** `regional_wealth` raises the regional wealth of the player region by the amount
- **AND** `silver` raises the silver of the lord's treasury
- **AND** `tech_point` adds tech picks (ModState `tech_picks_earned`) and is allowed only when `update-tech-tree-yearly-picks` is built
- **AND** `influence` raises the influence
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

#### Scenario: Rewards by tier
- **WHEN** the offer is drawn
- **THEN** a Small contract pays tier 1 goods or regional wealth, a Medium contract pays weapons, tier 2 goods or treasury silver, and a Large contract pays 1 tech point or 1000 influence (the pools of table 2 in `design.md`)
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A completed contract pays every reward
- **WHEN** the player fulfils a contract whose reward is silver
- **THEN** the silver of the treasury rises by the amount, the goods are taken, and the contract shows as fulfilled
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

#### Scenario: A reward that fails
- **WHEN** the goods reward finds no storehouse
- **THEN** `failed_rewards` rises and a log line names the reward
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Contract state is saved
The mod SHALL keep the contract state in ModState and restore it after a load: the spring counter (it names the year of the offer), the offer, the fulfilled count of each tier and the count of done contracts. Old saves with no contract keys SHALL load with defaults. The saved key `liege_influence` SHALL stay. The key `arms_last_day` is no longer written (the arms shipment is removed).

#### Scenario: The keys
- **WHEN** the state is written
- **THEN** the keys are `contracts_spring_no` (integer, -1: no offer yet), `contracts_offer` (the 9 contracts with request and reward amounts, text form), `contracts_used` (fulfilled count of each tier, text form) and `contracts_done`
- **AND** the keys `contracts_active`, `contracts_start_day`, `contracts_baseline`, `contracts_progress` and `contracts_failed` are gone
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: State round trip
- **WHEN** the offer holds 9 contracts, one is fulfilled, and the game is saved and loaded
- **THEN** `liege_contracts_state` shows the same 9 contracts (same amounts) and the same fulfilled counts
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/roundtrip.py` (a real load needs the guarded `save_game`).

#### Scenario: An old save
- **WHEN** a save made before this change loads
- **THEN** the influence is unchanged, the old offer and the old active contract are dropped without penalty, and the first new offer comes at the next start of spring
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A removed contract id
- **WHEN** the save holds an offer with a request or reward that the table no longer has
- **THEN** that contract is dropped, no penalty applies and the log names the id
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The liege window opens in at most 2 clicks
The player SHALL open the root of the liege window from the game UI with the mouse in at most 2 clicks, with no hotkey. The window SHALL update the stock and the button states after a fulfilment. The rule covers only the root window.

#### Scenario: Opens in 2 clicks
- **WHEN** the player is in the normal game view with no mod menu open
- **THEN** the player opens the liege window with at most 2 clicks on game UI elements, and no key press
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_contracts/window.py`.

#### Scenario: Values update
- **WHEN** the player fulfils a contract while the window is open
- **THEN** the "Fulfilled" count of the tier, the "In storage" lines and the button states change to the new values
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_contracts/window.py`.

### Requirement: The feature offers named commands
The mod SHALL register the commands `InvasionMod.liege_contracts_state`, `liege_contract_fulfil` (argument: the contract id) and `liege_contracts_offer_now`. Tests and the window SHALL use them, not eval. The commands `liege_contract_pick`, `liege_contract_complete`, `liege_contracts_test_progress` and `liege_send_tribute` SHALL NOT exist. The state SHALL go to the telemetry metrics `liege_contracts_done` and `liege_contracts_offered`.

#### Scenario: State is readable
- **WHEN** a scenario sends `InvasionMod.liege_contracts_state`
- **THEN** the answer holds the 9 contracts, the fulfilled count and limit of each tier, the days to the start of winter, the days to the next spring, `failed_rewards` and the spring counter
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: Test commands
- **WHEN** a scenario sends `liege_contracts_offer_now` (optional argument `ids` names the offer)
- **THEN** the offer changes at once, with no wait for a spring
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The tribute command is gone
- **WHEN** a scenario sends `InvasionMod.liege_send_tribute`, `liege_contract_pick` or `liege_contract_complete`
- **THEN** the harness answers that the command is unknown
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

## REMOVED Requirements

### Requirement: Objective types
**Reason**: Requests are deliveries of goods only (owner decision 2026-10-30). The kinds `build_count`, `kill_raiders`, `hold_public_order` and `raise_militia_squads` are removed.
**Migration**: The requirement "Requests are deliveries of goods" replaces it.

### Requirement: The mod offers three contracts each spring
**Reason**: The offer is now 9 contracts (3 for each tier).
**Migration**: The requirement "The mod offers nine contracts each spring" replaces it.

### Requirement: The player picks exactly one contract
**Reason**: There is no pick step and no active contract. Each card has a Fulfil button.
**Migration**: The requirement "The player fulfils contracts, up to a limit for each tier" replaces it.

### Requirement: Completion, deadline and penalty
**Reason**: There is no penalty and no deadline per contract. Contracts expire when winter begins.
**Migration**: The requirements "The player fulfils contracts, up to a limit for each tier" and "Contracts expire when winter begins" replace it.

### Requirement: The liege window shows three contract cards
**Reason**: The window has a new layout with three tiers of three cards.
**Migration**: The requirement "The liege window shows contracts by tier" replaces it.

## ADDED Requirements

### Requirement: Requests are deliveries of goods
Every contract SHALL ask for the delivery of one good in one amount. A Small contract asks for a tier 1 good, a Medium contract for a tier 2 good and a Large contract for a tier 3 good (the goods tiers of table 1 in `design.md`). A contract SHALL have no other objective kind.

#### Scenario: The request is a delivery
- **WHEN** a contract is drawn
- **THEN** it holds one good id of the goods tier of its contract tier and one amount
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: Stock is read from the player region
- **WHEN** a card shows "In storage: <have> / <need>"
- **THEN** `<have>` is the stock of the good in the player region (any store, as today)
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_contracts/window.py`.

### Requirement: The request amount comes from a formula
The amount SHALL be `max(1, round(base(tier) * weight(good) * difficulty))`, rounded half up. `base(tier)`, `weight(good)` and `difficulty` are config values. The difficulty comes from the yearly raid level of the scenario settings (proposed: level 1 gives 0.75, level 2 gives 1.0, level 3 gives 1.25, level 0 gives 1.0; an open question of the proposal).

#### Scenario: The amount formula
- **WHEN** a Large contract asks for plate armor (base 15, weight 0.35) at difficulty 1.25
- **THEN** the amount is 7 (`15 * 0.35 * 1.25 = 6.56`), and at difficulty 1.0 it is 5
- **AND** a result below 1 gives 1, and a changed base, weight or difficulty in config changes the amount
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The mod offers nine contracts each spring
At each start of spring, with or without a built manor, the mod SHALL draw `offer_per_tier` different contracts (default 3) at random from each tier and offer them. The new offer SHALL replace the old one and reset the fulfilled counts. The mod SHALL NOT make an offer at the first poll of a new game or of a save. The offer SHALL be saved before it is logged.

#### Scenario: A spring draw
- **WHEN** the season counter shows a new spring (read as in `mod/tech_tree`)
- **THEN** the offer holds 3 different contracts for each tier (9 in all) and every fulfilled count is 0
- **AND** one offer is made for each spring counter value
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: No second draw after a load
- **WHEN** an offer exists, the game is saved and loaded
- **THEN** the offer holds the same contracts and no new draw happens before the next spring
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/roundtrip.py`.

#### Scenario: A game that starts in another season
- **WHEN** a new game starts in summer, or a save that is not in spring loads without contract state
- **THEN** no offer is made, the window shows the time to the next spring, and the first offer comes at the next start of spring
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The player fulfils contracts, up to a limit for each tier
The command `InvasionMod.liege_contract_fulfil` (argument: the contract id) SHALL take the requested goods from the stores of the player region and pay the reward at once. The player may fulfil at most N contracts of each tier in a year (config value `liege_contracts.tier_limits`, default 1). A refused call SHALL change nothing and SHALL give the reason.

#### Scenario: A fulfilment
- **WHEN** the stock of the good is at or above the amount and the tier count is below the limit, and the player fulfils the contract
- **THEN** the stock falls by the amount, the reward is paid, the tier count rises by 1 and `contracts_done` rises by 1
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_contracts/fulfil.py` and `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: Not enough goods
- **WHEN** the stock is below the amount and the player fulfils the contract
- **THEN** the call is refused with the missing amount and nothing is taken or paid
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The tier limit
- **WHEN** the limit of a tier is 1 and one contract of that tier is fulfilled
- **THEN** a second contract of that tier is refused, even with enough goods, and contracts of the other tiers are not affected
- **AND** a changed config value changes the limit
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Contracts expire when winter begins
When winter begins, the mod SHALL clear the offer. An unfulfilled contract SHALL have NO penalty: the influence, the silver and the goods do not change. The config value `liege_contracts.fail_penalty` SHALL NOT exist. New contracts come at the next spring.

#### Scenario: Winter clears the offer
- **WHEN** winter begins with unfulfilled contracts in the offer
- **THEN** the offer is empty, the influence is unchanged and no failure is counted
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: No contracts in winter
- **WHEN** the player opens the window in winter
- **THEN** the window shows no cards and shows the time to the next spring
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: The liege window shows contracts by tier
The liege window (menu id `liege`, a pak widget) SHALL follow the layout of the mockup `liege-contracts-tiers.html` (in `openspec/changes/update-liege-contracts-tiers/mockups/`; after the archive, in `openspec/specs/mod/liege_contracts/mockups/`). It has a title "Contracts of the Liege", a top bar, three rows (Small, Medium, Large) of three cards, and a bottom bar with only a full-width Close button. It SHALL use only controls of the pak and hide the unused ones.

#### Scenario: The bars
- **WHEN** the window is open
- **THEN** the top bar shows "Time to fulfil contracts: <n> days remaining" (days until winter begins) and "Contracts refresh: In spring, in <n> days"
- **AND** the top bar has no influence and no treasury counter, and the bottom bar has no status text and no tooltip
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

#### Scenario: The tier box
- **WHEN** the window is open
- **THEN** each row has a box at the left with the tier name only (Small, Medium or Large) and "Fulfilled <used> / <limit>"
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

#### Scenario: A card
- **WHEN** an offer exists
- **THEN** each card shows "Requirement" (for example "Deliver 40 firewood"), "In storage: <have> / <need>", "Reward" and a Fulfil button
- **AND** a card has no name, no quote and no penalty
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

#### Scenario: The Fulfil button
- **WHEN** the manor is built, the goods are in storage and the tier limit is not reached
- **THEN** the Fulfil button is enabled and a click calls the same code as `liege_contract_fulfil`
- **AND** otherwise the button is greyed out and clicks are ignored
- **AND** after a fulfilment the label of that card is "Fulfilled"
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_contracts/window.py`.

#### Scenario: The countdowns
- **WHEN** the window is open in spring, summer or autumn
- **THEN** "days remaining" is the number of game days until winter begins, and "In spring, in <n> days" is the number of game days until the next spring
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The window has no offer
- **WHEN** no offer exists (a game that did not start in spring, or winter)
- **THEN** the cards are hidden and the window shows the time to the next spring
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: No arms shipment button
- **WHEN** the window is open
- **THEN** it shows no "Request arms shipment" button (the arms shipment is removed; see the delta of `mod/liege_influence`)
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_contracts/window.py`.

### Requirement: Fulfilling needs a built manor
The mod SHALL deal the offer whether or not a manor exists. A contract SHALL be fulfilled only when the player's manor is built (a `HarnessManor.manor_state()` module with `built == true`). The Fulfil button SHALL be enabled only when the manor is built, the goods are in storage and the tier limit is not reached. The command `liege_contract_fulfil` SHALL check the manor again at click time and refuse if it is not built.

#### Scenario: No manor
- **WHEN** no manor is built and an offer exists
- **THEN** the window shows the 9 contracts, all Fulfil buttons are greyed, and the line "Build a manor to fulfil contracts." shows above the rows
- **AND** the offer is dealt at spring as usual
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/window.py`.

#### Scenario: The command refuses without a manor
- **WHEN** no manor is built and `liege_contract_fulfil` is sent, even with enough goods
- **THEN** the call is refused with the reason "Build a manor to fulfil contracts." and nothing is taken or paid
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The manor is lost
- **WHEN** the manor is no longer built
- **THEN** the Fulfil buttons are greyed again and the offer stays
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_contracts.py`.
