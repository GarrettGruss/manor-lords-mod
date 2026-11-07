## 1. Spike

- [x] 1.1 Spike: a native retinue squad of 5 men, native recruiting, save and load. Verified by real game runs on slot 2 and `notes/spike-native-retinue.md`.

## 2. Code

- [ ] 2.1 `manor_stronghold/retinue.lua`: `add_native_squad(men)`. Verified by `harness/tests/test_fakegame_manor_stronghold.py`.
- [ ] 2.2 Reward kind `retinue_squad`: `loader.lua`, `rules.lua` (letter `r`, cap rule), `view.lua`, `contracts.json`, `config.lua`, `init.lua` (pay, cap, King's Favour fallback). Verified by `harness/tests/test_fakegame_liege_contracts.py`.
- [ ] 2.3 Loan: retinue squads only, ids in mod state, reason "Needs a retinue squad", the native return, no `spearMilitia` guess. Verified by `harness/tests/test_fakegame_liege_contracts.py`.
- [ ] 2.4 Banner when a loan ends. Verified by `harness/tests/test_fakegame_liege_contracts.py`.

## 3. Tests

- [ ] 3.1 Fake game tests for every spec scenario. Verified by `uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"` and the full set.
- [ ] 3.2 Real game test scenario (slot 2): fulfil a Large contract with the reward (a native squad of 5 men), a loan with a retinue squad and the return banner (`liege_contracts_loans_due_now`). Verified by `runs/<id>/summary.json`.
- [ ] 3.3 Picture evidence: the contracts card with the reward. Listed in `evidence/README.md`.

## 4. Docs and close

- [ ] 4.1 `CHANGELOG.md` (root and mod), wiki pages, `wiki.py check`.
- [ ] 4.2 `openspec validate add-contract-retinue-reward --strict`, merge `origin/main`, archive as the last commit.
- [ ] 4.3 Test results table in the implementation pull request.
