## Why

Issue: #505. Owner request 2026-10-28: "Change the liege screen from tribute to contracts. This is a fundamental change. The player is given 3 random contracts each year. They pick one. The spec will require a contracts table to store the data."

Today the liege screen has one tribute button: the player pays silver and gets influence. Influence has no use yet, and the player makes no choice. The owner wants the liege relation to be a yearly decision: the liege offers three tasks, the player picks one, and the task pays rewards or costs influence if it fails.

## What Changes

- New capability `mod/liege_contracts`:
  - a contracts table `data/liege_contracts/contracts.json` (id, name, quote as card flavor text, weight, objectives, rewards, duration);
  - at each start of spring (and only then), 3 different contracts are drawn at random (weighted) and offered; the player picks exactly one, the others are discarded; an offer that is not picked is replaced at the next spring with no penalty;
  - 5 objective types and 5 reward types (all from proven mechanics, see `design.md`), among them a tech point for the tech tree;
  - deadline: a contract ends when winter begins; a contract that is not complete then costs 500 influence (config value `fail_penalty`);
  - saved state, named commands, telemetry metrics;
  - the liege window shows three contract cards (mockup `mockups/liege-contracts-layout.html` with its icons in `mockups/icons/`; gate 2 copies both to `openspec/specs/mod/liege_contracts/mockups/`).
- `mod/liege_influence`: REMOVED the requirements "Tribute is silver from the lord's treasury", "The tribute ratio is configurable", "The command name", "Tribute menu" and "One tribute button". MODIFIED "Influence is a saved value" (only contracts change it; a penalty stops at 0). The arms shipment requirements do not change.
- `mod/core`: MODIFIED "Mod menus pause the game while open" (the menu name "liege and tribute" becomes "liege").
- Behavior changes against today:
  - The player can no longer buy influence with silver. The command `liege_send_tribute`, the config values `influence_per_unit` and `tribute_button_amount`, and the `TributeButton` of the pak widget are removed.
  - Influence rises only by contract rewards and falls by contract penalties.
  - The liege window is a new pak widget (`WBP_LiegeContracts`); the old `WBP_LiegeTribute` asset is removed from the pak.
  - A save from before the change loads. Its influence and arms cooldown stay. The first offer comes at the next start of spring (no offer at the first poll).
- Not changed: the vassal tribute (goods from handed-over vassals, `mod/tribute`), the vassal policies heavy, light and fair, the law effects Scorched Earth (-25 percent tribute share) and Trade Pacts (+25 percent tribute share), and the yearly tribute of vassalage terms (`mod/sack_and_terms`). They are not on the liege screen (see the open question).
- Out of scope: spending influence (design: call for aid, request villagers or weapons); a contract reward of regional wealth (no safe write is proven); game art for contracts (in the game the items are letter boxes, see `design.md`; the mockup has original icons).

## Decisions (owner, 2026-10-28)

- The liege screen offers contracts, not tribute.
- 3 random contracts each year; the player picks one.
- A contracts table stores the data.

Answers to the open questions (owner, 2026-10-28):

- The offer is made at the start of spring only. A new game, or a save that is not in spring, waits for the next spring (no offer at the first poll).
- An offer that is not picked: nothing happens, no penalty. The next spring replaces it.
- A contract ends when winter begins. The season counter and enum are those of `features/invasion`. Gate 2 reads the spring value (task of `update-tech-tree-yearly-picks`) and the winter value.
- The penalty for a failed contract is 500 influence, never below 0. It is the config value `liege_contracts.fail_penalty`, one value for all contracts.
- A completed contract pays at once. No bonus for early completion. No second offer in the same year.
- Goods of `deliver_goods` are taken at completion, not at the pick.
- A contract can pay a tech point (one tech pick for the tech tree). The reward `tech_pick` depends on `update-tech-tree-yearly-picks` (ModState `tech_picks_earned`). At least one starter contract uses it.
- The reward `retinue_squad` is removed, and so is every starter contract that used it.
- The starter values (weights, amounts) are placeholders for owner tuning. Note: influence rewards in the starter set (10 to 40) are small against the penalty of 500; tune them together.
- In the game, items show a letter box (accepted). In the mockup, each objective and reward type has an original icon (`mockups/icons/*.png`, sources in `mockups/icons/src/*.svg`).
- The envoy (portrait and quote) is removed from the spec, the layout and the mockup. The `quote` of a contract stays only as flavor text on its card.

## Spec changes (decided in gate 2)

Open question 1 (scope of "tribute") is decided: option A (owner, issue #505 comment, 2026-10-28). Only the liege tribute (silver for influence, on the liege screen) is removed. The vassal goods tribute, the vassal policies heavy, light and fair, and the law effects Scorched Earth and Trade Pacts stay. No change to `mod/tribute`, `mod/vassals`, `mod/tech_tree` or `mod/finite_resources`.

Findings of gate 2 that change a decision (details in `notes/`):

- Goods ids (`notes/goods-ids.md`): id 15 is Rubble, not bread. The reward of `feed_the_city` is bread (id 172). Ids 14 (iron ore), 16 (wood), 17 (planks), 30 (carp), 145 (salt) and 133 (spears) are as in the starter set.
- Saved text (`notes/state-encoding.md`): ModState strings allow only letters, digits, `_`, `.` and `-`. The progress and baseline text use `o<index>-<value>` entries separated by dots (for example `o0-12.o1-40`), not `key=value;` pairs.

## Impact

- Specs: `mod/liege_contracts` (ADDED), `mod/liege_influence` (REMOVED 5, MODIFIED 1), `mod/core` (MODIFIED 1).
- Code (gate 2): `Scripts/features/liege_influence/` (remove tribute; keep arms shipment), new `Scripts/features/liege_contracts/` (rules, world, init), `data/liege_contracts/contracts.json`, a getter for the spring tick in `features/invasion`, a kill-count getter in `features/raid_behavior`, the pak widget generator and pak (`WBP_LiegeContracts`), `config.lua` (`liege_influence`, new `liege_contracts`), `feature_list.lua`, tests, test scenarios (`liege_influence/send_tribute.py` and `tribute_menu.py` are replaced), wiki, skills, CHANGELOG.
- Overlap: `update-tech-tree-yearly-picks` (#499, the spring tick and `spring_season`) and `update-tech-tree-widget-layout` (#502, widget pool method). Merge #499 first or rebase on it. This change does not edit their files.
- Risk: see `design.md` (storehouse take, kill count for bandits, a new pak widget with pools, UI hooks).
