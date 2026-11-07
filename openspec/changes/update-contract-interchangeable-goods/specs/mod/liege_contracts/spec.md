## MODIFIED Requirements
<!-- Issue: #589 -->

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
- **THEN** the card text is "Deliver 40 berries or mushrooms" and the text fits the card
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
