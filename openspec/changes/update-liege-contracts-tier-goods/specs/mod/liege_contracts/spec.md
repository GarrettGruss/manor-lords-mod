## MODIFIED Requirements

<!-- Issue: #569 -->

### Requirement: Contracts live in a data table
The mod SHALL read all contracts from the data file `mod/InvasionMod/data/liege_contracts/contracts.json`. No contract id, amount or text SHALL be in Lua code. The table holds, for each tier (`small`, `medium`, `large`), a pool of requests and a pool of rewards. The pools are in the tables of `design.md` of the change `update-liege-contracts-tier-goods` (proposed defaults; the owner tunes them). A bad table SHALL stop the load with a clear message.

#### Scenario: The table fields
- **WHEN** the table loads
- **THEN** it holds `version` (3), `offer_per_tier` (default 3) and the three tiers
- **AND** each request of Small and Medium has `good` and `weight` (above 0); each request of Large has `cost` (a cost kind), `min` and `max` (the amount range) and `weight` (above 0)
- **AND** each reward has `kind` (`goods`, `weapons`, `armor`, `law`, `kings_favour`, `law_slot` or `relief_promise`), `goods` where the kind needs one (the name of a list of good ids in the top level field `good_lists`, because the JSON reader limits the nesting), `min` and `max` (the reward amount range)
- **AND** the table has no `duration` and no penalty field
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The starter table loads
- **WHEN** the feature loads the starter table
- **THEN** each tier has at least `offer_per_tier` requests and at least one reward, and every good id is known (an id of `DT_Items`)
- **AND** Small requests are only the renewable goods and Medium requests are only the processed goods of table 1 in `design.md`
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A bad table stops the load
- **WHEN** the table has an unknown kind, a missing field, a weight of 0 or less or fewer requests in a tier than `offer_per_tier`
- **THEN** the load fails and the message names the tier and the field
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

### Requirement: Requests are deliveries of goods
A Small or Medium contract SHALL ask for the delivery of one good in one amount. A Small contract asks for a renewable good and a Medium contract for a processed good (table 1 in `design.md`). A Large contract SHALL ask for one cost, not for goods (requirement `Large contracts ask for a cost`).

#### Scenario: The request is a delivery
- **WHEN** a Small or Medium contract is drawn
- **THEN** it holds one good id of the goods list of its tier and one amount
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: Stock is read from the player region
- **WHEN** a card shows "In storage: <have> / <need>"
- **THEN** `<have>` is the stock of the good in the player region (any store, as today)
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`.

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

## ADDED Requirements

### Requirement: Large contracts ask for a cost
A Large contract SHALL hold one cost in place of goods. The kinds are `loan_units`, `loan_peasants`, `send_families`, `tribute_season` and `herd`, (table 2 in `design.md`). A cost SHALL be taken only at fulfilment. A cost kind with no safe method SHALL NOT be in the table. The loan kinds need `liege_contracts.loan_enabled` (set from the spike `spike-loan-units`; if loaning is impossible, the units are lost).

#### Scenario: A cost is taken
- **WHEN** the player fulfils a Large contract with the cost `herd` (10 sheep) and the player region holds at least 10 sheep
- **THEN** the sheep count falls by 10 and the reward is paid
- Checked by `mod/InvasionMod/scenarios/liege_contracts/fulfil.py` (after the spike tasks).

#### Scenario: A cost that cannot be paid
- **WHEN** the player region holds fewer families, animals or units than the cost needs
- **THEN** the call is refused with the missing amount and nothing is taken or paid
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A loan ends
- **WHEN** a loan contract is fulfilled and the loan length passed (and loaning is possible)
- **THEN** the loaned units or peasants return to the player, and the end is kept in mod state across a save and load
- **AND** when loaning is not possible the units or peasants are lost at fulfilment and the card text says "lost"
- Checked by `harness/tests/test_fakegame_liege_contracts.py` (after the result of `spike-loan-units`).

#### Scenario: The card shows the cost
- **WHEN** a Large card is shown
- **THEN** it shows "Cost: <text>" in place of "Deliver <n> <GOODS>", for example "Cost: 3 families, for good", and "Reward: <text>"
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

### Requirement: Law rewards follow the Laws menu rules
A `law` reward SHALL unlock one random law that is not unlocked yet, through `laws_unlock(id, source)` of `add-laws-menu`, and SHALL NOT be drawn when no law is locked. The law SHALL work whatever the tech path (owner decision 2026-11-04). Law slots start at 1 and are at most 5 in total. A `law_slot` reward SHALL NOT be drawn at 5 slots; if fulfilled at 5 slots it pays `kings_favour` instead (a lead proposal). The mod SHALL keep no law state of its own.

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
A `kings_favour` reward SHALL raise `kingsFavour` of the player pawn by the amount (default 10). If the write is not proven by the spike, the reward SHALL NOT be in the table. A `relief_promise` reward SHALL raise the mod state value `relief_bonus_squads` (default +5 squads). The great raid SHALL add `relief_bonus_squads` to the squads of the relief army when it spawns, and SHALL reset the value to 0 after that. The value SHALL be saved and restored after a load.

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
