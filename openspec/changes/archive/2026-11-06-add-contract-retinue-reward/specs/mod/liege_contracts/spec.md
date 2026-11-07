## MODIFIED Requirements

<!-- Issue: #591 -->

### Requirement: Reward types
The mod SHALL support these reward kinds, paid once when the player fulfils a contract. Each contract has exactly one reward, drawn from the reward pool of its tier. A reward that cannot be paid SHALL be logged and counted in `failed_rewards`, and SHALL NOT be retried. The kinds `regional_wealth`, `silver`, `tech_point` and `influence` SHALL NOT be in any reward pool.

#### Scenario: The types and their effect
- **WHEN** a contract pays a reward kind
- **THEN** `goods`, `weapons` and `armor` (`good`, `amount`) add the goods to a storehouse
- **AND** `law` unlocks one random law that is not unlocked yet, through `laws_unlock(id, source)` of `add-laws-menu`
- **AND** `kings_favour` raises `kingsFavour` of the player by the amount
- **AND** `law_slot` adds one law slot through `laws_add_slot()` of `add-laws-menu`
- **AND** `relief_promise` raises the mod state value `relief_bonus_squads` by the amount
- **AND** `retinue_squad` adds one native retinue squad with 5 men (config `retinue_squad_men`) through `retinue.add_native_squad` of the feature manor_stronghold
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

#### Scenario: Rewards by tier
- **WHEN** the offer is drawn
- **THEN** a Small contract pays vassal goods (salt, iron ore, clay, flax or stone), a Medium contract pays tools, ale, cider, mead or clothes, and a Large contract pays a law, King's Favour, weapons, armor, a law slot, a relief promise or a retinue squad (the pools of table 2 in `design.md` of the change `update-liege-contracts-tier-goods` and `design.md` of the change `add-contract-retinue-reward`)
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A completed contract pays every reward
- **WHEN** the player fulfils a contract whose reward is King's Favour
- **THEN** `kingsFavour` rises by the amount, the cost is taken, and the contract shows as fulfilled
- Checked by `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

#### Scenario: A reward that fails
- **WHEN** the goods reward finds no storehouse
- **THEN** `failed_rewards` rises and a log line names the reward
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

### Requirement: Large contracts ask for a cost
A Large contract SHALL hold one cost in place of goods: `loan_units` (default 1 retinue squad for 60 game days), `send_families` (default 3 families, for good) or `tribute_season` (default 3 months of vassal tribute), as in table 2 of `design.md` of the change `update-liege-contracts-tier-goods`. The amount SHALL scale with the difficulty. A cost SHALL be taken only at fulfilment. A cost kind with no safe method SHALL NOT be in the table (not the herd, not the peasant loan). The cost `loan_units` SHALL take retinue squads only, never militia or levy squads.

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
- **WHEN** the player region holds fewer families (one family must stay), retinue squads or vassals than the cost needs
- **THEN** the call is refused with the missing amount and nothing is taken or paid
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: A loan takes a retinue squad only
- **WHEN** the player has a militia squad and no retinue squad and a `loan_units` contract is checked
- **THEN** the contract cannot be fulfilled, the card shows "Needs a retinue squad", and nothing is taken
- **AND** with a militia squad and a retinue squad the retinue squad is loaned, and with two retinue squads the one with fewer men is loaned
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

#### Scenario: A loan ends
- **WHEN** a `loan_units` contract is fulfilled and 60 game days pass
- **THEN** a native retinue squad with the same number of men returns to the player (equal, not the same men), and the loan record is kept in mod state across a save and a load
- **AND** a banner shows "The liege returns your squad (<n> men)"
- **AND** a 5-man retinue squad is never recorded as `spearMilitia`
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

#### Scenario: The card shows the cost
- **WHEN** a Large card is shown
- **THEN** it shows "Cost: <text>" in place of "Deliver <n> <GOODS>", for example "Cost: 3 families, for good", and "Reward: <text>"
- Checked by `mod/InvasionMod/scenarios/liege_contracts/window.py`, picture evidence.

## ADDED Requirements

### Requirement: The retinue squad reward
A Large reward `retinue_squad` SHALL add one native retinue squad of 5 men (config `retinue_squad_men`). The player pays the normal retinue recruiting to grow it; the game saves it.

#### Scenario: The reward is paid
- **WHEN** a Large contract with the reward `retinue_squad` is fulfilled with a built manor
- **THEN** a new squad with 5 living men is in the commanded squads of the player, the silver is as before, and the card text is "+1 retinue squad"
- Checked by `harness/tests/test_fakegame_liege_contracts.py` and `mod/InvasionMod/scenarios/liege_contracts/fulfil.py`.

### Requirement: The retinue squad reward has a cap
The mod SHALL allow at most 4 reward squads (config `retinue_squad_cap`, owner decision 2026-11-06) and SHALL save the count in the mod state key `contracts_retinue_squads`. At the cap the reward SHALL NOT be drawn, and a fulfilment at the cap SHALL pay King's Favour instead. The mod SHALL keep the ids of the retinue squads in the key `retinue_squad_ids`, because no safe read tells a retinue squad.

#### Scenario: The cap
- **WHEN** 4 reward squads were paid and a contract with the reward `retinue_squad` is fulfilled
- **THEN** no squad is added and `kingsFavour` rises by the default amount
- **AND** with a count of 4 the offer holds no new `retinue_squad` reward
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.

#### Scenario: The reward in the saved text and the data
- **WHEN** the table loads with the row `{ "kind": "retinue_squad", "min": 1, "max": 1 }` and an offer with that reward is encoded and decoded
- **THEN** the loader accepts the kind and the decoded reward has the same kind and amount
- Checked by `harness/tests/test_fakegame_liege_contracts.py`.
