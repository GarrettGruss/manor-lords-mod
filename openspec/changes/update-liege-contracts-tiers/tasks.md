## 1. Spikes

- [ ] 1.1 Spike: can the mod write `Region.regionalWealth` and does the value hold after a game day? Write `notes/regional-wealth.md`. Verified by a real game run of a spike test scenario.
- [ ] 1.2 Confirm the item ids of every good in Table 1 of `design.md` against `DT_Items`. Four are unknown (cut stone, tools, bows, helmets); each has a candidate. Write `notes/item-ids.md`. Verified by review of the notes.
- [ ] 1.3 Check which window controls the pak has (rows, cards, a greyed button) and whether the pak must change. Write `notes/window-controls.md`. Verified by review.

## 2. Data and rules

- [ ] 2.1 New `contracts.json` format: tiers, request pool (good, weight) and reward pool by tier. Verified by `harness/tests/test_fakegame_liege_contracts.py`.
- [ ] 2.2 Config values: `liege_contracts.tier_limits` (Small, Medium, Large; default 1 each), `base` (by tier), `weight` (by good id) and `difficulty` (by raid level); remove `fail_penalty`. Verified by the fake game test.
- [ ] 2.3 Spring draw of 3 contracts per tier with the request amount from the formula `round(base * weight * difficulty)`. Verified by the fake game test (seeded random).
- [ ] 2.4 Fulfil rule: goods check, tier limit, take goods, pay one reward. Verified by the fake game test.
- [ ] 2.5 Expiry at the start of winter, with no penalty. Verified by the fake game test.
- [ ] 2.6 Remove the pick, complete, progress and penalty code and the objective kinds. Verified by the fake game test.
- [ ] 2.7 ModState keys and the load of old saves. Verified by the fake game test.

## 3. Window and commands

- [ ] 3.1 New liege window as in the mockup. Verified by `mod/InvasionMod/scenarios/liege_contracts/window.py`.
- [ ] 3.2 Commands: `liege_contract_fulfil`; remove `liege_contract_pick` and `liege_contract_complete`; update `liege_contracts_state` and the test commands. Verified by the fake game test.
- [ ] 3.3 Capture picture evidence of the window into `evidence/` with `ctx.screenshot(name)` and list it in `evidence/README.md`.
- [ ] 3.4 Move the arms shipment button to the manor: check the manor UI hook and the pak controls, write `notes/manor-button.md`, remove the button from the contracts window, and update `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py`. Verified by that test scenario.

## 4. Close

- [ ] 4.1 Update the real game test scenarios (`window.py`, `complete.py`, `pick.py`, `roundtrip.py`). Verified by real game runs (`roundtrip.py` needs the guarded `save_game`).
- [ ] 4.2 Update the wiki, the skills and `CHANGELOG.md`. Verified by `wiki.py check`.
- [ ] 4.3 Run the full test set and `openspec validate update-liege-contracts-tiers --strict`.
- [ ] 4.4 Write the test results table of the implementation pull request.
