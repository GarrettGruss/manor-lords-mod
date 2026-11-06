## 1. Spikes (before the code of each cost or reward; findings in `notes/`)

- [x] 1.1 Spike: `changeKingsFavour(amount)` on the player pawn changes `kingsFavour`, and what the value does. Verified by a real game run on slot 1 or 2 (`--slot 1` or `--slot 2`, never `--slot auto`) and `notes/kings-favour.md`. If it fails, set the field or drop the reward.
- [x] 1.2 Spike: remove N families from the player region from Lua without a crash (the harness action `family_eject` is the start). Verified by a real game run and `notes/send-families.md`.
- [x] 1.3 Spike: pause the vassal tribute for one season (feature `tribute`). Built as the saved counter `tribute_skip_months`; verified by the fake game tests (`notes/tribute-season.md`). The real game run checks the refusal without a vassal; a real month change was not run.
- [x] 1.4 Spike: count and remove animals of one kind from the pens or the region. Result: animals can be counted but not removed (`notes/herd.md`, runs 20261106-001313-77bd, -001542-9c52, -001719-bfb7). The `herd` cost is dropped (design decision 9).
- [x] 1.5 Spike: is "Wood" (16) a stored good that the stock read finds? Verified by a real game run and `notes/timber.md`. Drop it if not.
- [x] 1.6 Read the result of `spike-loan-units` and set `liege_contracts.loan_enabled` (true; squads only, `notes/loan-units.md`). Verified by review.

## 2. Data

- [x] 2.1 Write `contracts.json` version 3: Small and Medium request pools and reward lists of table 1, Large costs and rewards of table 2, the lists `weapons` and `armor`. Verified by `harness/tests/test_fakegame_liege_contracts.py` (every id is a `DT_Items` row).
- [x] 2.2 Drop any cost or reward whose spike failed, and list it in the pull request: the `herd` cost is dropped; the peasant loan is dropped by the owner. Verified by review.

## 3. Code

- [x] 3.1 `loader.lua`: read the new request and reward shapes, check ids and kinds, name tier and field in errors. Verified by the fake game test (good table, bad table).
- [x] 3.2 `rules.lua`: draw a Large cost and reward, the cost amount formula, leave out `law` when no law is locked and `law_slot` at the cap, new saved text form. Verified by the fake game test.
- [x] 3.3 `world.lua` and `init.lua`: take each cost kind, pay each reward kind, call `laws_unlock` and `laws_add_slot`, the King's Favour fallback, the loan end with mod state. Verified by the fake game test and the real game test scenarios of task 5.
- [x] 3.4 Invasion: add `relief_bonus_squads` to the relief army and reset it. Verified by the fake game test of the invasion feature.
- [x] 3.5 `view.lua`: the cost line and the reward text of a Large card. Verified by the fake game test and `window.py`.
- [x] 3.6 `config.lua`: `loan_enabled`, Large defaults, base values. Verified by the fake game test.
- [x] 3.7 Check that `add-laws-menu` gate 2 applied the owner decisions (1 base slot, cap 5, a contract law ignores the path). If not, stop and ask the lead. Verified by review.

## 4. Fake game tests

- [x] 4.1 Update `harness/tests/test_fakegame_liege_contracts.py` for every spec scenario of the delta spec. Verified by `uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"` and the full set of CONTRIBUTING.md.

## 5. Real game test scenarios

- [x] 5.1 Update `mod/InvasionMod/scenarios/liege_contracts/fulfil.py` (one contract of each tier, King's Favour, a law) and `window.py` (cost line). Run each with `--slot 1` or `--slot 2`, and check that `config.json` of the run shows the slot. Verified by `runs/<id>/summary.json`.
- [x] 5.2 Capture picture evidence with `ctx.screenshot(name)` into `evidence/` (Small, Medium and Large cards, a fulfilled Large card). List each in `evidence/README.md` with its run id. At most 1280x720.

## 6. Docs and close

- [x] 6.1 Update `CHANGELOG.md` (Unreleased), the wiki pages and the skills that the change affects, and move engine facts from `notes/` into the wiki. Verified by `wiki.py check`.
- [x] 6.2 Run `openspec validate update-liege-contracts-tier-goods --strict`, merge `origin/main`, archive as the last commit.
- [x] 6.3 Fill the test results table of the implementation pull request.
