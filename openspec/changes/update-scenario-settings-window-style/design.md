## Context

This change is visual only. Settings, defaults, pause, start kit and commands do not change. The mockup `mockups/scenario-settings-game-style.html` is the visual source (artifact board "Scenario start screen").

## Decisions

- **Font and texture:** reuse the result of the liege restyle (`update-liege-contracts-window-style`, task 1.1, `notes/fonts-textures.md`). Do not repeat the open technical questions of that design (font, panel texture, centre light, fallbacks). If that gate 2 is not done, do the spike there first. Use the same fallback it chose, and name it in the pull request.
- **Colours:** gold #e8c87a for the selected option, the title rule and the headings. Grey for other options. Muted red box for the warning.
- **Options:** plain serif text blocks. The selected one is gold and underlined, the others grey. The Lua code that today adds "> " and " <" around the selected option sets a colour and an underline instead. The option widgets keep their names, so the click hooks stay.
- **Warning:** the rule does not change (`rules.background_with_warning`): the warning shows only when `vassals` is 0 (the current spec ties it to `vassals`, not to the Vassal raids level). The mockup shows it in a box at the bottom of the left column. The box is a separate widget that Lua shows or hides, and the warning text leaves the background text block.
- **Close removed:** `core/menu.lua` makes the framework Close for every menu (`make_close_button`, called when a menu opens). Add an optional field `close_button = false` to `menu.register` (like the existing `bar = false`). When it is false, the open function makes no Close button; `close_menu` already handles `S.close_button == nil`. The scenario settings menu registers with `close_button = false`.
  - The Esc key must not close this menu. Otherwise the player could leave without "Begin the game". Check in gate 2 how `core/menu.lua` handles Esc, and make Esc do nothing for a menu with `close_button = false`. Add a fake-game test.
  - "Begin the game" closes the menu as today.
- **Begin the game button:** large, with flourishes, in the style of the game's Close button (`/Game/UI/Common/menuButton.menuButton_C`) or a widget made like it. Lua finds the buttons by the same names as today.

## Risks

- One exit only. If "Begin the game" fails to attach, the player is stuck. Keep the existing fallback: a missing widget logs a clear message and applies the defaults.
- A game font or texture may not load from the pak. The fallback of the liege change applies.
