## MODIFIED Requirements
<!-- Issue: #538 -->

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
