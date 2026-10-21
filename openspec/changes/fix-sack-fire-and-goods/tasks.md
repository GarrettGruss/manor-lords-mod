## 1. Spike
- [x] 1.1 Run a sack with `method` fire while raiders are in the village; record flee, fire, rubble and burn time (design questions 1, 2 and 4); verify with a real game run. Write `notes/fire-during-raid.md`.
- [x] 1.2 Measure the stock before and after a store burns to rubble (design question 3); verify with a real game run. Ask the owner if goods are lost.

## 2. Code
- [ ] 2.1 Remove the stock share from the sack; verify with fake game tests in `harness/tests/test_fakegame_sack_and_terms.py`.
- [ ] 2.2 Make sacked buildings rubble within the time limit while raiders are present, and keep the goods of burned stores (per the answer to 1.2); verify with fake game tests.

## 3. Test scenarios
- [ ] 3.1 Update `sack_ruins.py` and `sack.py` to run the sack during a raid and check rubble and the unchanged stock; verify with real game runs. Update the "Checked by" lines.

## 4. Close
- [ ] 4.1 Update the wiki page for the sack, `CHANGELOG.md`, and `openspec/specs/mod/sack_and_terms/feedback.md` if it exists; verify with `wiki.py check`.
