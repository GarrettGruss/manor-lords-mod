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

- [ ] 2.8 Manor gate: deal no offer without a built manor; deal at once when a manor is built outside winter; move the manor check from `liege_influence` into `liege_contracts`. Verified by the fake game test.

## 3. Window and commands

- [ ] 3.1 New liege window as in the mockup. Verified by `mod/InvasionMod/scenarios/liege_contracts/window.py`.
- [ ] 3.2 Commands: `liege_contract_fulfil`; remove `liege_contract_pick` and `liege_contract_complete`; update `liege_contracts_state` and the test commands. Verified by the fake game test.
- [ ] 3.3 Capture picture evidence of the window into `evidence/` with `ctx.screenshot(name)` and list it in `evidence/README.md`.

## 4. Remove the arms shipment

Found by grep (2026-10-30). Nothing outside these files uses the arms shipment code.

- [ ] 4.1 Delete the arms code in `mod/InvasionMod/Scripts/features/liege_influence/init.lua` (the manor helpers, `shipment_status`, `request_arms_shipment`, the commands `InvasionMod.liege_request_arms` and `InvasionMod.liege_test_set_arms_day`, the ModState key `arms_last_day`, the arms fields of `liege_state`) and `shipment_status` in `rules.lua` (delete `rules.lua` if it is then empty). Update the file header.
- [ ] 4.2 Delete the config `liege_influence.arms_shipment` in `mod/InvasionMod/Scripts/config.lua`.
- [ ] 4.3 In `mod/InvasionMod/Scripts/features/liege_contracts/init.lua` delete `arms_info`, the `ArmsInfoText` and `ArmsButton` code, the use of `liege.shipment_status`, `liege.request_arms_shipment` and `liege.arms_config`, and the arms fields of the view (`arms_label`, `arms_disabled`, `shipments`).
- [ ] 4.4 Delete the test scenario `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py`. Update `mod/InvasionMod/scenarios/liege_contracts/window.py` (it names the arms button).
- [ ] 4.5 Delete the arms tests in `harness/tests/test_fakegame_liege_influence.py` and in `harness/tests/test_fakegame_liege_contracts.py` (`test_the_arms_text_stays` and the `arms_last_day` checks of the old save test).
- [ ] 4.6 Remove the arms button and its info text from the pak widget: `mod/InvasionMod/ue/make_liege_widget.py` (`ArmsInfoText` and the arms button), rebuild `WBP_LiegeContracts` in `mod/InvasionMod/data/liege_contracts/assets/` and the pak `mod/InvasionMod/paks/InvasionMod_P.pak`. Search the diff for the AES key before the commit.
- [ ] 4.7 Update `docs/wiki/architecture/invasion-features.md` (the `liege_influence` paragraph), the skills that name the arms shipment (grep `.claude/skills`), `CHANGELOG.md` under Removed ("the arms shipment") and `mod/InvasionMod/CHANGELOG.md`.

Left alone: the archived changes, and the old mockup `openspec/specs/mod/liege_contracts/mockups/liege-contracts-layout.html` (replaced at the archive of this change). The scenario start kit (`add-scenario-start-kit`) stays; only its arms shipment part is removed.

## 5. Close

- [ ] 5.1 Update the real game test scenarios (`window.py`, `complete.py`, `pick.py`, `roundtrip.py`). Verified by real game runs (`roundtrip.py` needs the guarded `save_game`).
- [ ] 5.2 Update the wiki, the skills and `CHANGELOG.md`. Verified by `wiki.py check`.
- [ ] 5.3 Run the full test set and `openspec validate update-liege-contracts-tiers --strict`.
- [ ] 5.4 Write the test results table of the implementation pull request.
