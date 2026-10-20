# Tasks

## 1. Decisions

- [x] 1.1 Get the user's answers to the open questions in `design.md` (done 2026-10-19: menu, no decay, no cap, 10 tribute for 1 influence, silver from the lord's treasury, command name, start); verify by review of `design.md`
- [x] 1.2 Get the answers to the new open questions 7 to 9 in `design.md` (how the menu opens, how the amount is chosen, influence format); verify by review of `design.md`

## 2. Code

- [x] 2.1 Add the feature folder `liege_influence` (config with `influence_per_unit` = 0.1, rules, commands `liege_state` and `liege_send_tribute` that take silver from the lord's treasury) that requires `mod_state` and `tribute`; verify with fake game tests in `harness/tests/test_fakegame_liege_influence.py` (paid tribute, refused tribute, ratio, no decay, no cap)
- [x] 2.2 Check that no code calls a save function; verify with `harness/tests/test_save_call_sites.py`

## 3. Tribute menu (pak widget)

- [x] 3.1 Make the widget asset `WBP_LiegeTribute` with an editor script in `mod/InvasionMod/ue/` (as `make_raid_widget.py`), use `Border` placeholders for buttons, cook it, and add it to the pak work folder; verify with `pakmod.py buildmod InvasionMod`
- [ ] 3.2 Copy the cooked `WBP_ClickButton` into the pak work folder and add `HarnessClickHooks` to `shared` in `mod.json`; verify with `pakmod.py list` and a deploy
- [ ] 3.3 Write the menu script in the feature (load the widget with `AssetRegistryHelpers:GetAsset`, `clickhooks.attach` and `bind_texts`, drain clicks in the scheduler tick, `release` on close); the menu calls the same code as `liege_send_tribute`; verify with fake game tests and a real game run
- [ ] 3.4 Make sure that the menu does not tick faster than 100 ms and does not rewrite labels each tick; verify by review and the scenario in 4.1

## 4. Test scenarios

- [ ] 4.1 Add `influence_roundtrip.py`, `send_tribute.py` and `tribute_menu.py` (real mouse clicks, as `tech-tree-widget-clicks`) in `mod/InvasionMod/scenarios/liege_influence/`; verify with a real game run of each
- [ ] 4.2 Take menu screenshots with `ctx.screenshot(name)` (menu open, after a tribute), commit compressed copies (at most 1280x720) to `openspec/changes/add-liege-influence/evidence/` and list them in `evidence/README.md` with test scenario and run id; verify by review of the pictures
- [ ] 4.3 Run the `tribute`, `mod_state` and widget test scenarios again; verify that they pass

## 5. Docs and results

- [ ] 5.1 Update the wiki, `CHANGELOG.md` and the living spec `mod/liege_influence`; verify with `wiki.py check` and `openspec validate --strict`
- [ ] 5.2 Fill the test results table and the evidence links of the implementation pull request; verify by review
