## 1. Spike result

- [ ] 1.1 Reuse the font and texture result of `update-liege-contracts-window-style` (`notes/fonts-textures.md`). Write what applies to this window in `notes/fonts-textures.md` of this change.

## 2. Framework

- [ ] 2.1 Add the flag `close_button = false` to `menu.register` in `core/menu.lua`: no framework Close, and Esc does not close the menu. Register the scenario settings menu with it.
- [ ] 2.2 Fake-game tests for the flag (no Close made, Esc does nothing, other menus unchanged).

## 3. Widget

- [ ] 3.1 Rebuild `WBP_ScenarioSettings` in `make_scenario_settings_widget.py` in a private UE workspace and a private pak work_dir.
- [ ] 3.2 Update `init.lua`: selected option gold and underlined, others grey; warning box shown only when `vassals` is 0.

## 4. Check

- [ ] 4.1 Run `scenario_settings/new_game_menu.py` and the other `scenario_settings` test scenarios that open the menu; take screenshots into `evidence/` with a `README.md`.
- [ ] 4.2 Run the fake game tests and `openspec validate update-scenario-settings-window-style --strict`.
- [ ] 4.3 Update `CHANGELOG.md`, the wiki and the skills that the change affects.

## 5. Archive

- [ ] 5.1 Archive as the last commit: `openspec archive update-scenario-settings-window-style --yes`.
