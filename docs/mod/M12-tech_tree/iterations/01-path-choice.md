# M12 iterations 01 and 03: path-choice and first-nodes

Branch: `feat/M12-tech_tree-01-path-choice`. Issue: #195. Iteration 03 (first-nodes) is combined with 01 because the node effects are small.

## Goal
The player picks one of two exclusive paths. The mod builds the tree from a JSON file. The player unlocks nodes for free, one slot for each settlement level. The node effects reach the game through existing features. Commands only; the widget is iteration 02.

## Decisions used
M00 decisions 22 (exclusive paths, final choices, draft nodes), 23 (data driven), 24 (free, one slot for each settlement level), 29 (boon values, TBD), 14 (Oppression gives Public Order, Prosperity gives approval).

## Data schema (`mod/InvasionMod/data/tech_tree/tree.json`)
```
{ "version": 1,
  "paths": [ { "id", "name" }, { "id", "name" } ],            exactly 2 paths
  "nodes": [ { "id", "path", "name",
               "requires": [ node ids ],                      same path only, no cycle
               "effect": [ { "kind", "value", "min_garrison_squads"? } ],
               "layout": { "x", "y" }? } ] }                  optional, default x = depth, y = row of the path
```
- Effect kinds: `public_order` (add), `approval` (add, used by the Public Order debuff of M04, the real approval is not written), `buy_back_price` (percent, 0.25 is +25%), `militia_attack`, `militia_defence` (percent).
- `min_garrison_squads`: the effect counts only while the player commands at least that many squads (TBD meaning of "garrison", M13 may refine).
- The loader stops the feature with a clear message for: a wrong version, a path count other than 2, a duplicate id, an unknown path, an unknown effect kind, a bad type, an id with other characters than letters, digits, `_` and `-`, an unknown required id, a requirement of another path, and a cycle.

## Changes
- New feature `tech_tree` (`tree.lua` pure loader, `rules.lua` pure rules, `world.lua`, `init.lua`). Requires `bandits`, `unit_balance`, `mod_state`.
- Settlement level: `Region.settlementLevel` of the player region (verified by `set_settlement_level`). Slots = level x `slots_per_level` (1).
- ModState keys: `tech_path` (default `none`) and `tech_nodes` (ids joined by dots).
- Effects: a poll (scheduler, 2 s) and every choice push the totals to `bandits.set_modifiers` (Public Order bonus, approval bonus, buy-back price factor) and `unit_balance.set_militia` (att and def factors).
- bandits: `rules.debuffed_order(natural, approval, difficulty, modifiers)`, `modifiers` state, buy-back price config with the factor.
- unit_balance: militia factors for units of the player whose template is in `unit_balance.militia_templates`. The side comes from `HarnessUnits.squadMap`. The factors scale att, def and block from the base values the mod saw first.
- Commands: `tech_tree_state`, `tech_tree_choose_path`, `tech_tree_unlock`.
- `mod.json`: feature `tech_tree`, shared modules `HarnessJson` and `HarnessUnits`.

## Acceptance criteria
- T1: at the start `path == "none"`, 8 nodes, no unlocked node.
- T2: unlock before a path is chosen is refused.
- T3: the second path choice is refused; the path is kept.
- T4: a node of the other path is refused.
- T5: with settlement level 1 there is 1 slot; level 2 gives 2 slots.
- T6: a node whose required node is not unlocked is refused. T8: no free slot is refused.
- T7: after Martial Law, `bandits_state.order == clamp(natural_order + 10 - debuff)`.
- T9: after Iron Hand, `order == clamp(natural_order + 25 - debuff)`.
- T10, T11: after Iron Hand the buy-back price factor is 1.25 and a buy-back of 2 families costs 25 silver.
- Fake game: the Prosperity approval bonus lowers the debuff; Fear of the Lord counts only with 4 squads; Amnesty gives 0.5; the militia factors reach unit_balance.

## Scenarios
- `mod/InvasionMod/scenarios/tech_tree/path_choice.py` (`tech-tree-path-choice`).
- Militia att and def writes are covered by fake game tests only. A real-game check needs a player militia unit; the base `def` of unarmored militia is 0 after M05, so Veteran Levies has no visible effect on them (TBD).

## Result
PASS in the real game (2026-10-18). Notes: `../implementation-notes/iteration-01-path-choice.md`.
- `tech-tree-path-choice`: runs `20261018-065608-83f3`, `20261018-065952-80fe` and `20261018-073126-77c6` pass (T1 to T13). Public Order followed `natural + bonus - debuff` (40 to 50 to 75 at approval 40) and the buy-back of 2 families cost 25 silver with Iron Hand.
- `tech-tree-militia-factor`: runs `20261018-072731-ca37` and `20261018-072903-f30c` pass (M1 to M3). The saved game has 20 militia units (role Husband or Son); their live `att` was 1.1 times the base and stayed so for 20 game seconds.
- Fake game tests: `harness/tests/test_fakegame_tech_tree.py` (25 tests: loader refusals, path, slots, effects, militia factors).
- Deviations: the militia is found by role (Husband, Son), not by template, because `unitTemp` reads `None`. Test squads of `spawn_units` have role Soldier and are not changed. Veteran Levies has no visible effect on unarmored militia (def is 0 after M05).
