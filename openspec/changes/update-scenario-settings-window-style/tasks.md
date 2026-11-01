## 1. Spike result

- [x] 1.1 Reuse the font and texture result of `update-liege-contracts-window-style` (`notes/fonts-textures.md`). Write what applies to this window in `notes/fonts-textures.md` of this change.

## 2. Framework

- [x] 2.1 Add the flag `close_button = false` to `menu.register` in `core/menu.lua`: no framework Close, and Esc does not close the menu. Register the scenario settings menu with it.
- [x] 2.2 Fake-game tests for the flag (no Close made, Esc does nothing, other menus unchanged).

## 3. Widget

- [x] 3.1 Rebuild `WBP_ScenarioSettings` in `make_scenario_settings_widget.py` in a private UE workspace and a private pak work_dir.
- [x] 3.2 Update `init.lua`: selected option gold and underlined, others grey; no warning box.
- [x] 3.3 Remove the vassals guard and the warning: state key, live check, rules, config text, the `vassals` and `warning` fields of `scenario_settings_state`, the guard test file and test scenario (owner decision 2026-11-01).

## 4. Check

- [x] 4.1 Run `scenario_settings/new_game_menu.py` and the other `scenario_settings` test scenarios that open the menu; take screenshots into `evidence/` with a `README.md`.
- [x] 4.2 Run the fake game tests and `openspec validate update-scenario-settings-window-style --strict`.
- [x] 4.3 Update `CHANGELOG.md`, the wiki and the skills that the change affects.

## 5. Archive

- [ ] 5.1 Archive as the last commit: `openspec archive update-scenario-settings-window-style --yes`.
