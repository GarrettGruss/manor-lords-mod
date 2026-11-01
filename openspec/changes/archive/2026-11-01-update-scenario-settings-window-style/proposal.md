## Why

<!-- Issue: #540 -->

The scenario settings window (the start screen of the Hussite scenario) uses the manuscript look. The game's own windows are dark, quiet and serif. The liege contracts window was restyled to match the game (change `update-liege-contracts-window-style`, #538). The owner approved a start screen mockup in the same style (decision 2026-10-31). Issue: #540.

## What Changes

- Restyle the scenario settings window (menu id `scenario_settings`, widget `WBP_ScenarioSettings`) to the mockup `mockups/scenario-settings-game-style.html`.
- Dark full background with a soft centre light. Centred title "The Hussites Are Coming" in spaced small capitals with a thin gold rule.
- One dark panel with rough edges and two columns.
  - Left: a "The Scenario" heading bar and the background text (unchanged). There is no warning box.
  - Right: a "Settings" heading bar and the same five rows, options and defaults.
- Options are plain serif text. The selected option is gold and underlined, the others are grey. The "> Medium <" markers are removed.
- Bottom: "Use defaults" and a large "Begin the game" with flourishes, in the style of the game's Close button.
- The framework's bottom Close does not show on this window. "Begin the game" is the only way out. The framework gets a per-menu flag for this.
- The framework's Esc key does nothing on this window.
- REMOVED (owner decision 2026-11-01): the warning "vassals are not enabled" and the check behind it (the guard value `vassals`, the live check, the config text). The spike of #543 proved that vassals work with AI opponents 0.
- Behavior does not change otherwise: settings, defaults, pause and kit stay as they are.

## Impact

- Spec: `mod/scenario_settings`. MODIFIED: "The menu follows the approved look", "Other game settings lock nothing". REMOVED: "The vassals guard value is a mod setting saved in ModState", "An old save without the setting uses the live check", "AI opponents 0 warns that vassals are not enabled".
- Code (gate 2): `mod/InvasionMod/ue/make_scenario_settings_widget.py`, the pak widget, `Scripts/core/menu.lua` (flag), `Scripts/features/scenario_settings/init.lua` (option text and colour; the guard and the warning code is removed), `Scripts/features/scenario_settings/rules.lua`, `Scripts/config.lua`.
- Dependency: the font and texture result of change `update-liege-contracts-window-style` (gate 2). Reuse it.
