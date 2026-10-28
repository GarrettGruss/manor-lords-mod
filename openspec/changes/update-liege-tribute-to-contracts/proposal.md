## Why

Issue: #505. Owner request 2026-10-28: "Change the liege screen from tribute to contracts. This is a fundamental change. The player is given 3 random contracts each year. They pick one. The spec will require a contracts table to store the data."

Today the liege screen has one tribute button: the player pays silver and gets influence. Influence has no use yet, and the player makes no choice. The owner wants the liege relation to be a yearly decision: the liege envoy offers three tasks, the player picks one, and the task pays rewards or costs influence if it fails.

## What Changes

- New capability `mod/liege_contracts`:
  - a contracts table `data/liege_contracts/contracts.json` (id, name, quote, weight, objectives, rewards, duration, penalty);
  - at each start of spring, 3 different contracts are drawn at random (weighted) and offered; the player picks exactly one, the others are discarded;
  - 5 objective types and 6 reward types (all from proven mechanics, see `design.md`);
  - deadline (default: the next spring) and a penalty of lost influence if the contract is not complete;
  - saved state, named commands, telemetry metrics;
  - the liege window shows three contract cards (mockup `mockups/liege-contracts-layout.html`; gate 2 copies it to `openspec/specs/mod/liege_contracts/mockups/`).
- `mod/liege_influence`: REMOVED the requirements "Tribute is silver from the lord's treasury", "The tribute ratio is configurable", "The command name", "Tribute menu" and "One tribute button". MODIFIED "Influence is a saved value" (only contracts change it; a penalty stops at 0). The arms shipment requirements do not change.
- `mod/core`: MODIFIED "Mod menus pause the game while open" (the menu name "liege and tribute" becomes "liege").
- Behavior changes against today:
  - The player can no longer buy influence with silver. The command `liege_send_tribute`, the config values `influence_per_unit` and `tribute_button_amount`, and the `TributeButton` of the pak widget are removed.
  - Influence rises only by contract rewards and falls by contract penalties.
  - The liege window is a new pak widget (`WBP_LiegeContracts`); the old `WBP_LiegeTribute` asset is removed from the pak.
  - A save from before the change loads. Its influence and arms cooldown stay. The first poll makes an offer.
- Not changed: the vassal tribute (goods from handed-over vassals, `mod/tribute`), the vassal policies heavy, light and fair, the law effects Scorched Earth (-25 percent tribute share) and Trade Pacts (+25 percent tribute share), and the yearly tribute of vassalage terms (`mod/sack_and_terms`). They are not on the liege screen (see open question 1).
- Out of scope: spending influence (design: call for aid, request villagers or weapons); a contract reward of regional wealth (no safe write is proven); contract art (icons are letter boxes, see `design.md`).

## Decisions (owner, 2026-10-28)

- The liege screen offers contracts, not tribute.
- 3 random contracts each year; the player picks one.
- A contracts table stores the data.

## Open questions (with defaults)

1. Scope of "tribute". Default: only the liege tribute (silver for influence, on the liege screen) is removed. The vassal goods tribute, the vassal policies and the two tribute law effects stay, because they supply iron and salt (`mod/finite_resources`) and are not on the liege screen. Alternative: remove the vassal tribute and policies too, and map Scorched Earth and Trade Pacts to a -25 percent and +25 percent contract reward factor. That alternative is a larger change and needs its own spec change for `mod/tribute`, `mod/vassals`, `mod/tech_tree` and `mod/finite_resources`.
2. The first offer. Default: a new game, and a save without contract state, gets an offer at the first poll (like `initial_picks` of the tech tree), then one at each spring.
3. An offer that the player does not pick. Default: it stays open until the next spring, then it is replaced, with no penalty.
4. The deadline. Default: every starter contract runs until the next spring (`duration` `next_spring`). A day count is possible in the data.
5. The penalty. Default: the contract fails at the deadline and the influence falls by the penalty, never below 0. Influence is the only liege score today. Alternative: also a public order or silver penalty.
6. A contract that is completed early. Default: it pays at once; no second offer until the next spring.
7. Delivery of goods. Default: `deliver_goods` takes the goods from the storehouses when the player completes the contract (not before). Gate 2 must prove the take from a storehouse with `consumeGoodNoCheck` (task 1.2); the fallback is the manor store (`HarnessManor.manor_take`, proven), which needs a built manor.
8. The reward `tech_pick`. Default: allowed in the data only after `update-tech-tree-yearly-picks` (#499) is built; the starter set does not use it.
9. The reward `retinue_squad`. Default: in the starter set for one hard contract. Cost to tune: the squad is free to the player.
10. All numbers in the starter set (weights, amounts, penalties) are placeholders for owner tuning.
11. Icons. Default: the game has no icon for these items in the pak widget pool, so an item shows a letter box and the name in the tooltip. Gate 2 may use game textures if the owner picks some.
12. The envoy portrait. Default: a plain portrait box with the envoy name; no model or texture.

## Impact

- Specs: `mod/liege_contracts` (ADDED), `mod/liege_influence` (REMOVED 5, MODIFIED 1), `mod/core` (MODIFIED 1).
- Code (gate 2): `Scripts/features/liege_influence/` (remove tribute; keep arms shipment), new `Scripts/features/liege_contracts/` (rules, world, init), `data/liege_contracts/contracts.json`, a getter for the spring tick in `features/invasion`, a kill-count getter in `features/raid_behavior`, the pak widget generator and pak (`WBP_LiegeContracts`), `config.lua` (`liege_influence`, new `liege_contracts`), `feature_list.lua`, tests, test scenarios (`liege_influence/send_tribute.py` and `tribute_menu.py` are replaced), wiki, skills, CHANGELOG.
- Overlap: `update-tech-tree-yearly-picks` (#499, the spring tick and `spring_season`) and `update-tech-tree-widget-layout` (#502, widget pool method). Merge #499 first or rebase on it. This change does not edit their files.
- Risk: see `design.md` (storehouse take, kill count for bandits, a new pak widget with pools, UI hooks).
