## Why

<!-- Issue: #540 -->

The scenario settings window (the start screen of the Hussite scenario) uses the manuscript look. The game's own windows are dark, quiet and serif. The liege contracts window was restyled to match the game (change `update-liege-contracts-window-style`, #538). The owner approved a start screen mockup in the same style (decision 2026-10-31). Issue: #540.

## What Changes

- Restyle the scenario settings window (menu id `scenario_settings`, widget `WBP_ScenarioSettings`) to the mockup `mockups/scenario-settings-game-style.html`.
- Dark full background with a soft centre light. Centred title "The Hussites Are Coming" in spaced small capitals with a thin gold rule.
- One dark panel with rough edges and two columns.
  - Left: a "The Scenario" heading bar and the background text (unchanged). The vassal warning is a muted red box at the bottom of the column.
  - Right: a "Settings" heading bar and the same five rows, options and defaults.
- Options are plain serif text. The selected option is gold and underlined, the others are grey. The "> Medium <" markers are removed.
- Bottom: "Use defaults" and a large "Begin the game" with flourishes, in the style of the game's Close button.
- The framework's bottom Close does not show on this window. "Begin the game" is the only way out. The framework gets a per-menu flag for this.
- Behavior does not change: settings, defaults, pause, kit and warning rule stay as they are.

## Impact

- Spec: `mod/scenario_settings`, requirements "The menu follows the approved look" and "AI opponents 0 warns that vassals are not enabled" (MODIFIED; the second changes the look of the warning only).
- Code (gate 2): `mod/InvasionMod/ue/make_scenario_settings_widget.py`, the pak widget, `Scripts/core/menu.lua` (flag), `Scripts/features/scenario_settings/init.lua` (option text, warning box).
- Dependency: the font and texture result of change `update-liege-contracts-window-style` (gate 2). Reuse it.
