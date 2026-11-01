## 1. Month clock

- [x] 1.1 Find the value for a game month change. Result: `TemporalComponent.month` (`notes/month-clock.md`, run `tr-rich-1`).

## 2. Rules and detection

- [x] 2.1 In `rules.lua`: add the amount rule (`base x factor`), the node rule, the choice of 2 goods by priority and the flax fill; remove `production` and `split`. Verified by `harness/tests/test_fakegame_tribute.py`.
- [x] 2.2 Add `features/tribute/world.lua`: scan `ResourceNode` objects, apply the decal and clump thresholds, group by `getRegionByPos(pos, true)`, cache for one loaded game. Verified by fake-game tests with fake nodes (rich, poor, game, outside region, two ticks scan once, scan again after a load).
- [x] 2.3 In `config.lua`: add `tribute.base`, `tribute.rich` (thresholds, goods ids, priority); remove `share`, `goods`, `finite_goods`, `units_per_family`. Verified by `harness/tests/test_fakegame_tribute.py` and `harness/tests/lua_syntax.py`.
- [x] 2.4 In `init.lua`: pay by month, update `tribute_state` (decision 8 of the design). Verified by `harness/tests/test_fakegame_tribute.py`.
- [x] 2.5 Owner decisions of 2026-11-01: flax twice for 0 rich, 2 goods cut by priority, month period, decision 21 of `design/mod/decisions.md` changed from season to month. Verified by `harness/tests/test_fakegame_tribute.py`.

## 3. Real game test scenario

- [x] 3.1 Add `mod/InvasionMod/scenarios/tribute/tribute_rich.py` on the test map: Krumme Leite pays stone and salt, Hochweg pays mushrooms and flax, 100 units of each for `fair`, 150 and 50 for `heavy` and `light`. The same goods come back in separate runs (each run loads the game). Verified by real game runs (run ids in the pull request).
- [x] 3.2 Update `tribute_payout.py`, `finite_resources/vassal_supply.py`, `tech_tree/laws.py` and `vassals/policies_and_orders.py` to the new rule. Verified by real game runs.

## 4. Docs

- [x] 4.1 Move engine facts that stay true from `notes/` into the wiki (the month field). The resource node facts are in the wiki already (spikes #546, #548, #551). Verified by `uv run python .claude/skills/repo-wiki/scripts/wiki.py check`.
- [x] 4.2 Update the skills that name the old tribute rule, if any. None names it (`harness-mod-state` names only the stand-in mod). Verified by review.
- [x] 4.3 Add `CHANGELOG.md` entries under `Unreleased` (Changed: tribute; Removed: iron and salt by family) and the mod changelog. Verified by review.
- [x] 4.4 Update the feature feedback file `openspec/specs/mod/tribute/feedback.md` if it exists. It does not exist. Verified by review.

## 5. Close

- [x] 5.1 Run the full test set and `openspec validate update-vassal-tribute-rich-resources --strict`.
- [ ] 5.2 Archive as the last commit (`docs(openspec): archive update-vassal-tribute-rich-resources`).
- [ ] 5.3 Fill the test results table of the implementation pull request (check, run id or test file, verdict, key number or range).
