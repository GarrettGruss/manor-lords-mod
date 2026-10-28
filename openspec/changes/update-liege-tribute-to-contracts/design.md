## Context

The feature `liege_influence` (`Scripts/features/liege_influence/`) keeps an influence number in ModState (`liege_influence`), a tribute command and button, an arms shipment button with a cooldown (`arms_last_day`) and the pak widget `WBP_LiegeTribute` (button names `TributeButton`, `ArmsButton`, `CloseButton`). The tech tree change `update-tech-tree-yearly-picks` (#499) gives one pick at each start of spring and reads the spring from the season counter of `features/invasion` (`yearly_season_no`) and `tech_tree.spring_season`. Contracts use the same tick source. The tech window change (#502) shows the pattern for a larger pak widget made from fixed pools.

## Data model (`data/liege_contracts/contracts.json`)

The starter set is in `notes/contracts-starter-set.json` (8 contracts; all values are placeholders for owner tuning). Fields:

- Top level: `version` (1), `offer_size` (3), `contracts`. No envoy.
- Contract: `id` (kebab or snake text, unique, no dot), `name`, `quote` (flavor text on the card; may be empty), `weight`, `objectives[]`, `rewards[]`, `duration` (`"winter_start"` or a number of game days).
- The penalty is not in the table. It is the config value `liege_contracts.fail_penalty` (500 influence), the same for all contracts.
- Objective: `type` plus the fields of its type (`good`, `building_type`, `min`, `days`) and `amount`.
- Reward: `type` plus `good` where needed and `amount`.

Loading follows `tree.lua` of the tech tree: a pure loader checks every field and stops with a message that names the contract and the field. Display names and descriptions of items (for the tooltip) come from a small `items` map in the same file (`kind:id` to name and description) or, for goods, from the config good names. An item with no entry shows its type name.

## Yearly tick and random draw

- The poll in `liege_contracts/init.lua` (period `poll_ms`, default 2000) reads the season value and the counter through the small getter in `features/invasion` that #499 adds. If #499 is not merged, gate 2 adds the same getter and #499 reuses it.
- Offers are made at the start of spring only. There is no offer at the first poll. With `contracts_spring_no` = -1 and a season that is not spring, the window shows the empty state until the next spring. When the season equals `spring_season` and the counter is above `contracts_spring_no`, the old offer is dropped (no penalty) and a new draw is made. The counter is saved before the log, so a load never draws twice.
- Deadline: a contract ends when winter begins. The poll reads the season value; when it equals the winter value and the active contract is not complete, the contract fails: the config `fail_penalty` (500) is taken from the influence, never below 0. A numeric `duration` (game days) is also allowed in the data. Gate 2 reads the spring and winter enum values of `features/invasion` (the spring value is also a read task of `update-tech-tree-yearly-picks`) and records them in `notes/`.
- A completed contract pays at once. It gives no bonus for being early and no second offer in the same year.
- Draw: weighted sampling without replacement (`rules.draw(contracts, n, rng)`). `rng` is injected: the game uses `math.random`, tests use a seeded function. The result is stored as ids in `contracts_offer`, so the draw is stable over save and load (it is saved state, not a seed that is replayed). Using `math.randomseed` from the clock is allowed; a replayable seed is not needed.
- If fewer contracts than `offer_size` are left after a data edit, the load fails (checked at load, not at draw).

## Progress per objective type (engine calls)

All reads run on the game thread in the poll. Progress for the active contract is computed on each poll and stored in `contracts_progress`.

| Type | Engine call or source | Feasibility source |
|---|---|---|
| `deliver_goods` | `region:getStockOfGood(good, false, false)` for progress; at completion `consumeGoodNoCheck(good)` once per unit on a storehouse | The stock read is used by `HarnessManor.manor_put` and `manor_take`. `consumeGoodNoCheck` is proven on homes (spike #482, wiki `engine-limits.md`, "Militia squads, weapons in homes") and on a manor module (`HarnessManor.manor_take`). A take from a storehouse is not proven: task 1.2 |
| `build_count` | count of buildings with `Data.bType` = `building_type` in the player region, minus the count at the pick | The restore of a vassal counts built buildings by type for `vassals.restore.rebuilt_share` (`mod/vassals`); the census of `sack_and_terms` (`world.census`) |
| `kill_raiders` | death events of `raid_behavior` (`rules` death events: a tracked unit that is gone or dead), counted after the pick | `raid_behavior` (corpse pit loot, wiki `invasion-features.md`). Gap: only raid units that the invasion feature tracks count; units of a native bandit camp may not. Task 1.3 checks this and the starter text says "raiders" |
| `hold_public_order` | the mod order of `bandits` (saved value, written to the region each poll) at day change | Wiki `engine-limits.md`, public order factors (spike #403); `invasion-features.md`, bandits |
| `raise_militia_squads` | `#pawn.commandedSquads` for militia squads | Spike #482: `addMilitiaSquad` and `pawn.commandedSquads` |

Rewards (engine calls):

| Type | Call | Feasibility source |
|---|---|---|
| `influence` | ModState write | `liege_influence` today |
| `silver` | `playerRef.silver` write, then `updatePlayerStats` on `W_HUD_LordPanel_V2_C` | The tribute and the arms shipment write silver today (`liege_influence/init.lua`) |
| `goods` | `building:addToInventory({Type, amt})` on the storehouse (`bType` 72) | Wiki `engine-limits.md` (spike #482); the arms shipment |
| `public_order` | one write to the mod order of `bandits` | Wiki `engine-limits.md`, "A per-tick `Region.publicOrder` write holds" |
| `tech_pick` | add to `tech_picks_earned` (one tech pick that the player spends in the tech tree) | Change #499; allowed only when that state exists. At least one starter contract uses it |

Excluded: any objective or reward of regional wealth or the regional treasury. No safe write is proven. A later spike can add them.

## State and migration

ModState keys (state `invasion`, pawn tags; see the requirement "Contract state is saved"): `contracts_spring_no`, `contracts_offer`, `contracts_active`, `contracts_start_day`, `contracts_baseline`, `contracts_progress`, `contracts_done`, `contracts_failed`. Register them with `state:register` and raise `STATE_VERSION`.

- Old saves have the keys `liege_influence` and `arms_last_day` only. The new keys take defaults, and the first offer comes at the next spring. No tribute state was saved (the `tributes` counter is in memory), so there is nothing to convert.
- Remove the config keys `influence_per_unit` and `tribute_button_amount`. An old `config.lua` copy with these keys is ignored.
- The scenarios `send_tribute.py` and `tribute_menu.py` are replaced. `influence_roundtrip.py` and `arms_shipment.py` are updated.

## UI approach (UMG pak widget)

- A new widget `WBP_LiegeContracts` replaces `WBP_LiegeTribute`. A generator `mod/InvasionMod/ue/make_liege_widget.py` builds it like the tech widget generator (#502): fixed pools of controls, no run-time creation of buttons.
  - Pools: 3 cards, each with a name text, a flavor text, 2 objective item boxes, 3 reward item boxes, a penalty badge and a PICK button; the title; influence and silver texts; the active panel (name, up to 2 progress lines, days left, Complete button); the arms button with its reason line; the footer line; the Close button. Items are a Border (icon box with a letter) and a text.
  - Unused cards and items are collapsed (`SetVisibility`).
- Buttons: the 3 PICK buttons, Complete, Arms and Close are pak buttons with fixed names. The mod uses the click queue and `clickhooks` as today (the tag value of a button is its name). It does NOT call `Button.OnClicked:Add` on a button made at run time (`DANGEROUS_ACTIONS.md`, #308).
- Children: use `IsValid` on each child from `GetChildAt` before use (the widget pool rule of #502).
- Icons: in the game, an item is a letter box (owner accepted, 2026-10-28). The mockup has original icons (`mockups/icons/`, 96x96 PNG made from `mockups/icons/src/*.svg`) as a reference for a later art change.
- Tooltips: each item box gets a tooltip text (`SetToolTipText`) with the name and the description. If a hover tooltip does not show in the real game, gate 2 shows the text of the hovered item in a line under the cards (the footer) and records it in `notes/`.
- The menu base (`menu.register`, pause on open, backdrop, Close position) does not change. The poll and refresh periods stay in the config.
- The layout reference is the mockup `mockups/liege-contracts-layout.html`. The owner compares the pictures of gate 2 with it. Fonts and textures of the game may differ.

## Commands and tests

- Pure rules in `liege_contracts/rules.lua` (load check, weighted draw, progress per type, deadline, reward list, penalty) test in the fake game kit. World calls are in `world.lua`.
- Commands are listed in the spec. The test commands (`offer_now`, `test_progress`) let a scenario skip the wait for a spring and the real kills.
- Real game test scenarios (`mod/InvasionMod/scenarios/liege_contracts/`): `pick`, `complete`, `progress`, `window` (clicks, screenshots), `roundtrip` (guarded `save_game`; back up the saves first).

## Risks

- Storehouse take: `consumeGoodNoCheck` on a storehouse is not proven. Fallback in the order: a second storehouse; the manor store; refuse the contract type until a spike passes. Task 1.2.
- Kill count: bandit camp units may not be tracked. Task 1.3.
- A new pak widget needs a cooked asset and a rebuilt pak; grep the diff for the AES key before the commit.
- A reward that adds goods to a full storehouse may fail; the mod counts `failed_rewards` and logs it.
- Spring and winter tick: depends on the season getter and `spring_season` of #499; the winter value is a gate 2 read task.
- The random draw is not deterministic between runs; tests inject the random function and the real game scenarios use `offer_now` with named ids.

## Not in scope

Spending influence; contract rewards or objectives of regional wealth; game icons for contracts; changes to the vassal tribute and policies (open question 1).
