## 1. Month clock

- [ ] 1.1 Find the value for a game month change (open question 3). Verified by a read-only real game run or a note in `notes/month-clock.md`.

## 2. Rules and detection

- [ ] 2.1 In `rules.lua`: add the amount rule (`base x factor`), the choice of 2 goods and the flax second good; remove `production` and `split` if unused. Verified by `harness/tests/test_fakegame_tribute.py`.
- [ ] 2.2 Add `features/tribute/world.lua`: scan `ResourceNode` objects, apply the decal and clump thresholds, group by `getRegionByPos(pos, true)`, cache for the session. Verified by fake-game tests with fake nodes (rich, poor, game, outside region, two ticks scan once).
- [ ] 2.3 In `config.lua`: add `tribute.base`, `tribute.rich` (thresholds and goods ids); remove `share`, `goods`, `finite_goods`, `units_per_family`. Verified by `harness/tests/test_fakegame_tribute.py` and `harness/tests/lua_syntax.py`.
- [ ] 2.4 In `init.lua`: pay by month, update `tribute_state` (decision 8 of the design). Verified by `harness/tests/test_fakegame_tribute.py`.

## 3. Real game test scenario

- [ ] 3.1 Add `mod/InvasionMod/scenarios/tribute/tribute_rich.py` on the test map: Krumme Leite pays stone and salt, Hochweg pays mushrooms and flax, 100 units of each for `fair`, 50 and 150 for `light` and `heavy`; check the same goods after a load. Assert ranges for stock changes. Verified by a real game run (run id in the pull request).
- [ ] 3.2 Update `tribute_payout.py` and `finite_resources/vassal_supply.py` to the new rule. Verified by a real game run.

## 4. Docs

- [ ] 4.1 Move engine facts that stay true from `notes/` into the wiki (resource nodes, decal size, clump capacity, region lookup). Verified by `uv run python .claude/skills/repo-wiki/scripts/wiki.py check`.
- [ ] 4.2 Update the skills that name the old tribute rule, if any (`harness-mod-state`). Verified by review.
- [ ] 4.3 Add `CHANGELOG.md` entries under `Unreleased` (Changed: tribute; Removed: iron and salt by family). Verified by review.
- [ ] 4.4 Update the feature feedback file `openspec/specs/mod/tribute/feedback.md` if it exists. Verified by review.

## 5. Close

- [ ] 5.1 Run the full test set and `openspec validate update-vassal-tribute-rich-resources --strict`.
- [ ] 5.2 Archive as the last commit (`docs(openspec): archive update-vassal-tribute-rich-resources`).
- [ ] 5.3 Fill the test results table of the implementation pull request (check, run id or test file, verdict, key number or range).
