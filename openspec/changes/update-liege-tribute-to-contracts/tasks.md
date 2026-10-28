## 1. Prepare and spikes

- [ ] 1.1 Confirm that `update-tech-tree-yearly-picks` (#499) is merged or rebase on it. Use its season getter and `spring_season`. Copy `mockups/liege-contracts-layout.html` and the folder `mockups/icons/` (PNGs and `src/*.svg`) of this change to `openspec/specs/mod/liege_contracts/mockups/` (the archive does not copy extra files). Commit them before the archive.
- [ ] 1.2 Spike (read and small writes, single player, no save call): can `consumeGoodNoCheck` take goods from a storehouse (`bType` 72) so that `getStockOfGood` falls by the amount? Write the result to `notes/storehouse-take.md`. Choose the take source for `deliver_goods` from the result (see design, Risks).
- [ ] 1.4 Read the winter value of the season enum of `features/invasion` (the spring value is read in gate 2 of `update-tech-tree-yearly-picks`). Write both values to `notes/season-values.md`.
- [ ] 1.3 Spike: does `raid_behavior` count the dead units of a bandit camp raid? Write `notes/kill-count.md`. If not, name the objective text "raiders" in the data and list the gap.

## 2. Data and pure rules

- [ ] 2.1 `data/liege_contracts/contracts.json` from `notes/contracts-starter-set.json`, with an `items` map for tooltips. `liege_contracts/loader.lua`: checks every field and stops with a message (duplicate id, unknown type, missing field, fewer than `offer_size`).
- [ ] 2.2 `liege_contracts/rules.lua`: weighted draw without replacement with an injected random function, progress per objective type, completion check, deadline check (winter start), reward list, penalty from the config (floor 0).
- [ ] 2.3 `config.lua`: new `liege_contracts` (`poll_ms`, `fail_penalty` = 500; `offer_size` is in the data); remove `influence_per_unit` and `tribute_button_amount` from `liege_influence`.

## 3. Feature

- [ ] 3.1 ModState keys and `STATE_VERSION` (spec: "Contract state is saved"). Spring offer only (no first-poll offer), save before log.
- [ ] 3.2 `world.lua`: progress reads, goods take, reward writes (influence, silver with the HUD refresh, goods, public order, tech pick). A failed reward is logged and counted.
- [ ] 3.3 Commands and telemetry metrics (spec: "The feature offers named commands"). Remove `liege_send_tribute` and the tribute code from `liege_influence/init.lua` and `rules.lua`. Keep the arms shipment.
- [ ] 3.4 Add the getter for the kill count in `raid_behavior` and the season getter in `invasion` if #499 has not added it. Register the feature in `feature_list.lua`.

## 4. Widget

- [ ] 4.1 `mod/InvasionMod/ue/make_liege_widget.py`: the pools of the design. Rebuild the pak, remove `WBP_LiegeTribute`. Grep the diff for the AES key before the commit.
- [ ] 4.2 `liege_contracts/init.lua` (or the liege menu in `liege_influence`): fill and hide controls, pick and Complete clicks through the click queue, tooltips, active panel, empty state. `IsValid` on each child from `GetChildAt`. No run-time `Button.OnClicked:Add` (#308).
- [ ] 4.3 Update `liege_menu_state` for the new controls.

## 5. Tests and evidence

- [ ] 5.1 `harness/tests/test_fakegame_liege_contracts.py` (every fake game scenario of the spec: load, draw, weights, spring tick, refusals, deadline, penalty floor, state round trip, old save, removed id). Update `test_fakegame_liege_influence.py` (influence without tribute) and the boundary test.
- [ ] 5.2 Test scenarios in `mod/InvasionMod/scenarios/liege_contracts/`: `pick`, `complete`, `progress`, `window`, `roundtrip`. Update `liege_influence/influence_roundtrip.py` and `arms_shipment.py`. Delete `send_tribute.py` and `tribute_menu.py`. Back up the saves first. Run each once in the real game.
- [ ] 5.3 Screenshots with `ctx.screenshot`, at most 1280x720, about 1 MB in total, in `evidence/` with `evidence/README.md` (test scenario and run id for each): three cards, a pick, the active panel, a tooltip, the empty state. The owner compares them with the mockup.
- [ ] 5.4 Update the "Checked by" lines in the delta specs.

## 6. Close

- [ ] 6.1 Wiki (`invasion-features.md` liege section, `mod-commands-and-state.md`), the skills that name the tribute command, and `CHANGELOG.md` and `mod/InvasionMod/CHANGELOG.md` under Unreleased. Run the full test set, `wiki.py check` and `openspec validate update-liege-tribute-to-contracts --strict`.
- [ ] 6.2 Merge `origin/main` into the branch. Archive as the last commit: `openspec archive update-liege-tribute-to-contracts --yes`.
