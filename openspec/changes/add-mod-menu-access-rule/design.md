# Design: Add mod menu access rule

## Decisions
- The rule counts clicks from the normal game view with no mod menu open, to the root menu shown on screen.
- Owner decision (2026-10-20): one button per root menu, not one shared "Mods" button. Each button opens its menu in 1 click.
- Owner decision (2026-10-20): the buttons sit in the game's bottom bar, after the game's own buttons, and look like the game's own buttons (size, icon frame, font, hover and pressed states). The player cannot hide them. This is option (a) of `notes/ui-entry-point.md`: a button added into an existing game HUD widget at run time. It was not tried in spike 1.1, so spike 1.3 must prove it.
- Owner decision (2026-10-20): every mod menu is fullscreen, like the developments menu, and blocks clicks so they never reach the game behind it (for example a burgage plot).
- Click blocking (spike, `notes/click-blocking.md`): the base menu puts a full-screen `Button` (not a `Border`, which does not block) under the menu content. A `Border` plus `SetInputMode_UIOnlyEx` also blocks and is the fallback.
- Owner decision (2026-10-20): all mod menus use one extensible base menu, `core/menu.lua`. The base owns the shared parts and is tested once in the real game; each menu adds only its id, label, content and actions, and is tested with fake game tests plus one shared smoke run.
- Keys stay as shortcuts. The rule only forbids a menu that needs a key.

## Open questions
| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 1 | Where is the entry point: a new HUD button, or a button inside an existing game menu? Can a pak or Lua add a HUD button at all? | A spike, then the owner | Task 1.1 |
| 2 | One shared "Mod" button, or one button per menu? | Owner | Answered 2026-10-20: one button per menu, in the bottom bar |
| 3 | Which game widget is the bottom bar, which panel takes `AddChild`, and can a button copy the style of the game's buttons? | A spike | Task 1.3 |
