# M12 iteration 04: laws-and-vassal-policies

Branch: `feat/M12-tech_tree-04-laws-and-vassal-policies` (stacked on M13.02, PR #216). Issue: #217.

## Goal
Mod-owned laws, and vassal tribute policies that the tree opens. Lua applies the effects. No game policy system.

## Changes
- `tree.json` gets `laws` (6) and `vassal_policies` (2 gates). A law: `id`, `path`, `name`, `requires` (nodes of the same path), `effect`.
- New effect kinds: `tribute_share` (percent, tribute feature) and `vassal_loyalty` (add to the season loyalty change, vassals feature).
- Laws (all values TBD). Oppression: Conscription (militia attack +10%, approval -5), Forced Labor on Walls (Public Order +5, approval -3; the wall effect itself is a stand-in), Scorched Earth (militia defence +10%, tribute -25%). Prosperity: Militia Charter (militia attack +5%, approval +2), Trade Pacts (tribute +25%, vassal loyalty +2), Pay Off Warbands (buy-back price -25%).
- A law is free, may be repealed, and at most `max_active_laws` (2) are in force.
- Vassal policy gates: `heavy` needs Oppression and Martial Law; `light` needs Prosperity and Fair Courts; `fair` is open. The command `tech_tree_set_vassal_policy` checks the gate and then calls `vassals.set_policy`. The direct `vassals_set_policy` stays open for tests.
- Commands `tech_tree_enact_law`, `tech_tree_repeal_law`, `tech_tree_set_vassal_policy`. ModState key `tech_laws`.
- `tech_tree` now requires `vassals` and `tribute`.

## Acceptance criteria
- L1, L2: light is refused before Fair Courts; heavy is refused on Prosperity.
- L3: light alone pays 10 (5 families, loyalty 50). L4: with Trade Pacts the tribute is 12 to 14. L5: loyalty rises by at least 3 at the season change. L6: after the repeal the tribute is 10.
- Fake game: loader refusals, enact and repeal, law places, policy gates (`test_fakegame_laws.py`).

## Result
PASS in the real game (2026-10-18), `--new-game`. Runs `20261018-100341-061b` and `20261018-100452-039c` pass (L1 to L6). The menu lists the laws since iteration 05.
